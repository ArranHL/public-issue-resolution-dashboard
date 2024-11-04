// static/js/kanban.js

document.addEventListener('DOMContentLoaded', () => {
    loadIssues();
    initModal();
    initDragAndDrop();
    initFilterSort();
});

async function loadIssues(filters = {}) {
    try {
        let url = '/api/issues';
        const params = new URLSearchParams(filters);
        if (params.toString()) {
            url += '?' + params.toString();
        }
        console.log('Fetching issues with URL:', url);
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        let issues = await response.json();
        console.log('Fetched issues:', issues);
        updateKanbanBoard(issues);
    } catch (error) {
        console.error('Error loading issues:', error);
    }
}

function updateKanbanBoard(issues) {
    console.log('Updating Kanban board with issues:', issues);
    const newList = document.getElementById('new-list');
    const openList = document.getElementById('open-list');
    const waitingList = document.getElementById('waiting-list');
    const fixedList = document.getElementById('fixed-list');

    newList.innerHTML = '';
    openList.innerHTML = '';
    waitingList.innerHTML = '';
    fixedList.innerHTML = '';

    issues.forEach(issue => {
        const issueCard = createIssueCard(issue);
        switch (issue.status.toLowerCase()) {
            case 'new':
                newList.appendChild(issueCard);
                break;
            case 'open':
                openList.appendChild(issueCard);
                break;
            case 'waiting':
                waitingList.appendChild(issueCard);
                break;
            case 'fixed':
                fixedList.appendChild(issueCard);
                break;
            default:
                newList.appendChild(issueCard);
        }
    });

    initDragAndDrop();
}

function createIssueCard(issue) {
    const card = document.createElement('div');
    card.className = 'issue-card';
    card.draggable = true;
    card.dataset.issueId = issue.id;

    const title = issue.label || 'Untitled Issue';
    const imageHtml = issue.image 
        ? `<img src="data:image/jpeg;base64,${issue.image}" alt="${title}" class="issue-image" onerror="this.style.display='none';" />`
        : '';

    const createdDate = new Date(issue.created_at).toLocaleString();

    card.innerHTML = `
        <h3>${title}</h3>
        <p><strong>Type:</strong> ${issue.type || 'Not Specified'}</p>
        <p><strong>Severity:</strong> ${issue.severity || 'Not Specified'}</p>
        <p><strong>Timeframe:</strong> ${issue.timeframe || 'Not Specified'}</p>
        <p><strong>Description:</strong> ${issue.description || 'No Description'}</p>
        <p><strong>Created:</strong> ${createdDate}</p>
        ${imageHtml}
    `;

    card.addEventListener('click', () => {
        openModal(issue);
    });

    return card;
}

function initFilterSort() {
    const applyFiltersButton = document.getElementById('apply-filters');
    const resetFiltersButton = document.getElementById('reset-filters');
    applyFiltersButton.addEventListener('click', applyFiltersAndSort);
    resetFiltersButton.addEventListener('click', resetFilters);
}

function applyFiltersAndSort() {
    const searchQuery = document.getElementById('search-input').value.trim().toLowerCase();
    const severityFilter = document.getElementById('severity-filter').value.trim().toLowerCase();
    const timeframeFilter = document.getElementById('timeframe-filter').value.trim().toLowerCase();

    // Add date filters
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    const filters = {
        search: searchQuery,
        severity: severityFilter,
        timeframe: timeframeFilter,
        start_date: startDate,
        end_date: endDate
    };

    loadIssues(filters);
}


function resetFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('severity-filter').value = '';
    document.getElementById('timeframe-filter').value = '';

    loadIssues();
}

async function openModal(issue) {
    const modal = document.getElementById('kanban-issue-modal');
    const modalContent = document.getElementById('kanban-modal-issue-details');

    const imageHtml = issue.image 
        ? `<img src="data:image/jpeg;base64,${issue.image}" alt="${issue.label}" class="issue-image" onerror="this.style.display='none';" />`
        : '';

    modalContent.innerHTML = `
        <h3>${issue.label}</h3>
        ${imageHtml}
        <p><strong>Type:</strong> ${issue.type || 'Not Specified'}</p>
        <p><strong>Description:</strong> ${issue.description || 'No Description'}</p>
        <p><strong>Severity:</strong> ${issue.severity}</p>
        <p><strong>Status:</strong> ${issue.status}</p>
        <p><strong>Timeframe:</strong> ${issue.timeframe || 'Not specified'}</p>
        <p><strong>Action Taken:</strong> ${issue.action_taken || 'No action taken yet'}</p>
        <p><strong>Cost (USD):</strong> ${issue.costusd || 'Not specified'}</p>
        <p><strong>Recommended Contact:</strong> ${issue.recommended_contact || 'Not specified'}</p>
    `;

    modal.style.display = 'block';

    try {
        const response = await fetch(`/api/responses/${issue.id}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch responses: ${response.status}`);
        }
        const responseData = await response.json();
        console.log('Fetched responses:', responseData);
        updateCarousel(responseData);
    } catch (error) {
        console.error('Error fetching response data:', error);
        const carouselContent = document.querySelector('#kanban-response-carousel .carousel-content');
        carouselContent.innerHTML = '<p>Error loading issue history.</p>';
        document.querySelector('#kanban-response-carousel').style.display = 'none';
    }
}

function updateCarousel(responseData) {
    const carouselContent = document.querySelector('#kanban-response-carousel .carousel-content');
    carouselContent.innerHTML = '';

    const carousel = document.querySelector('#kanban-response-carousel');
    if (responseData.length === 0) {
        carouselContent.innerHTML = '<p>No history available for this issue.</p>';
        carousel.style.display = 'none';
        return;
    } else {
        carousel.style.display = 'block';
    }

    responseData.forEach((response, index) => {
        const slide = document.createElement('div');
        slide.className = 'carousel-slide';

        let imageHtml = '';
        if (response.action_image) {
            imageHtml = `
                <div class="response-image-container">
                    <img src="data:image/jpeg;base64,${response.action_image}" alt="Response Image" class="response-image">
                </div>
            `;
        }

        slide.innerHTML = `
            ${imageHtml}
            <div class="response-content">
                <p><strong>Submission Date:</strong> ${response.SubmissionDate}</p>
                <p><strong>Action Role:</strong> ${response.action_role}</p>
                <p><strong>Action Status:</strong> ${response.action_status}</p>
                <p><strong>Action Taken:</strong> ${response.action_action_taken}</p>
                <p><strong>Resolution Cost (USD):</strong> ${response.action_resolution_costusd}</p>
                <p><strong>Resolution Timeframe:</strong> ${response.action_resolution_timeframe}</p>
                <p><strong>Recommended Contact:</strong> ${response.action_recommended_contact}</p>
            </div>
        `;
        carouselContent.appendChild(slide);
    });

    initCarousel();
}

function initCarousel() {
    const carousel = document.querySelector('#kanban-response-carousel');
    const slides = carousel.querySelectorAll('.carousel-slide');
    const prevButton = carousel.querySelector('.carousel-prev');
    const nextButton = carousel.querySelector('.carousel-next');
    let currentSlide = 0;

    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.remove('active');
            slide.style.display = 'none';
            if (i === index) {
                slide.classList.add('active');
                slide.style.display = 'flex';
            }
        });
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    function prevSlide() {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    }

    prevButton.replaceWith(prevButton.cloneNode(true));
    nextButton.replaceWith(nextButton.cloneNode(true));

    const newPrevButton = carousel.querySelector('.carousel-prev');
    const newNextButton = carousel.querySelector('.carousel-next');

    if (slides.length > 1) {
        newPrevButton.style.display = 'block';
        newNextButton.style.display = 'block';

        newPrevButton.addEventListener('click', prevSlide);
        newNextButton.addEventListener('click', nextSlide);
    } else {
        newPrevButton.style.display = 'none';
        newNextButton.style.display = 'none';
    }

    showSlide(currentSlide);
}

function initModal() {
    const modal = document.getElementById('kanban-issue-modal');
    const closeButton = document.querySelector('#kanban-issue-modal .close-button');

    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
}

function initDragAndDrop() {
    const draggables = document.querySelectorAll('.issue-card');
    const dropzones = document.querySelectorAll('.issue-list');

    draggables.forEach(draggable => {
        draggable.addEventListener('dragstart', () => {
            draggable.classList.add('dragging');
        });

        draggable.addEventListener('dragend', () => {
            draggable.classList.remove('dragging');
            updateIssueStatus(draggable);
        });
    });

    dropzones.forEach(dropzone => {
        dropzone.addEventListener('dragover', e => {
            e.preventDefault();
            const draggable = document.querySelector('.dragging');
            if (draggable) {
                dropzone.appendChild(draggable);
            }
        });
    });
}

function updateIssueStatus(issueCard) {
    const issueId = issueCard.dataset.issueId;
    const newStatus = issueCard.parentElement.id.replace('-list', '');

    fetch(`/api/issues/${issueId}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => console.log('Issue updated:', data))
    .catch(error => console.error('Error updating issue:', error));
}

window.highlightIssue = function(issueId) {
    const allLists = document.querySelectorAll('.issue-list');
    let issueCard;

    allLists.forEach(list => {
        const card = list.querySelector(`[data-issue-id="${issueId}"]`);
        if (card) {
            issueCard = card;
            card.remove();
        }
    });

    if (issueCard) {
        const openList = document.getElementById('open-list');
        openList.insertBefore(issueCard, openList.firstChild);
        issueCard.classList.add('highlighted');

        issueCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

        setTimeout(() => {
            issueCard.classList.remove('highlighted');
        }, 3000);
    }
};
