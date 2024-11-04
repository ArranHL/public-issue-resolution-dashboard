// static/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    initMap();          // Initialize the map on page load
    loadIssues();       // Load issues and update the list and map
    initModal();        // Initialize the modal for issue details

    const applyFiltersButton = document.getElementById('apply-filters');
    applyFiltersButton.addEventListener('click', applyFiltersAndSort);

    const resetFiltersButton = document.getElementById('reset-filters');
    resetFiltersButton.addEventListener('click', resetFilters);
});

async function loadIssues(filters = {}) {
    try {
        const queryParams = new URLSearchParams(filters);
        console.log('Query Params:', queryParams.toString());

        const response = await fetch(`/api/issues?${queryParams}`);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        const issues = await response.json();
        console.log('Issues fetched from API:', issues);

        updateIssuesList(issues);  // Update the issues list
        updateMap(issues);         // Update the map with the new issues
    } catch (error) {
        console.error('Error loading issues:', error);
    }
}


function applyFiltersAndSort() {
    const searchQuery = document.getElementById('search-input').value.trim().toLowerCase();
    const stateFilter = document.getElementById('state-filter').value.trim().toLowerCase();
    const severityFilter = document.getElementById('severity-filter').value.trim().toLowerCase();
    const timeframeFilter = document.getElementById('timeframe-filter').value.trim().toLowerCase();

    // Add date filters
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    const filters = {
        search: searchQuery,
        state: stateFilter,
        severity: severityFilter,
        timeframe: timeframeFilter,
        start_date: startDate,
        end_date: endDate
    };

    loadIssues(filters);
}


// static/js/app.js

function updateIssuesList(issues, append = false) {
    const issuesList = document.getElementById('issues-list');
    const issueCountElement = document.getElementById('issue-count');

    if (!append) {
        issuesList.innerHTML = '';  // Clear existing issues
    }

    // Update the issue count
    issueCountElement.textContent = issues.length;

    issues.forEach(issue => {
        const issueElement = document.createElement('div');
        issueElement.className = 'issue-card';
        issueElement.dataset.issueId = issue.id;

        // Build issue card content
        let imageHtml = '';
        if (issue.image) {
            imageHtml = `<img src="data:image/jpeg;base64,${issue.image}" alt="${issue.label}" class="issue-image" onerror="this.style.display='none';" />`;
        }

        const createdDate = new Date(issue.created_at).toLocaleString();

        issueElement.innerHTML = `
            <h3>${issue.label}</h3>
            ${imageHtml}
            <p><strong>Type:</strong> ${issue.type || 'Not specified'}</p>
            <p><strong>Description:</strong> ${issue.description}</p>
            <p><strong>Severity:</strong> ${issue.severity}</p>
            <p><strong>Status:</strong> ${issue.status}</p>
            <p><strong>Created:</strong> ${createdDate}</p>
        `;

        // Add click event listener to open the modal
        issueElement.addEventListener('click', () => openModal(issue));

        issuesList.appendChild(issueElement);
    });
}


async function openModal(issue) {
    const modal = document.getElementById('issue-modal');
    const modalContent = document.getElementById('modal-content');

    let imageHtml = '';
    if (issue.image) {
        imageHtml = `<img src="data:image/jpeg;base64,${issue.image}" alt="${issue.label}" class="issue-image">`;
    }

    const createdDate = new Date(issue.created_at).toLocaleString();

    modalContent.innerHTML = `
        <h2>${issue.label}</h2>
        ${imageHtml}
        <p><strong>Type:</strong> ${issue.type || 'Not specified'}</p>
        <p><strong>Created:</strong> ${createdDate}</p>
        <p><strong>Description:</strong> ${issue.description || 'No Description'}</p>
        <p><strong>Severity:</strong> ${issue.severity}</p>
        <p><strong>Status:</strong> ${issue.status}</p>
        <p><strong>Timeframe:</strong> ${issue.timeframe || 'Not specified'}</p>
        <p><strong>Action Taken:</strong> ${issue.action_taken || 'No action taken yet'}</p>
        <p><strong>Cost (USD):</strong> ${issue.costusd || 'Not specified'}</p>
        <p><strong>Recommended Contact:</strong> ${issue.recommended_contact || 'Not specified'}</p>
        <h3 class="carousel-title">Issue History</h3>
        <div id="response-carousel" class="carousel">
            <div class="carousel-content"></div>
            <button class="carousel-prev">&#10094;</button>
            <button class="carousel-next">&#10095;</button>
        </div>
    `;

    modal.style.display = 'block';

    // Fetch and display response data
    try {
        const response = await fetch(`/api/responses/${issue.id}`);
        const responseData = await response.json();
        updateCarousel(responseData);
    } catch (error) {
        console.error('Error fetching response data:', error);
    }
}

function updateCarousel(responseData) {
    const carouselContent = document.querySelector('.carousel-content');
    carouselContent.innerHTML = '';

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
    const carousel = document.querySelector('.carousel');
    const slides = carousel.querySelectorAll('.carousel-slide');
    const prevButton = carousel.querySelector('.carousel-prev');
    const nextButton = carousel.querySelector('.carousel-next');
    let currentSlide = 0;

    // Ensure slides are displayed correctly
    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.style.display = i === index ? 'flex' : 'none';
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

    // Check if there are multiple slides
    if (slides.length > 1) {
        prevButton.style.display = 'block';
        nextButton.style.display = 'block';

        nextButton.addEventListener('click', nextSlide);
        prevButton.addEventListener('click', prevSlide);
    } else {
        // Hide buttons if there's only one slide
        prevButton.style.display = 'none';
        nextButton.style.display = 'none';
    }

    showSlide(currentSlide);
}

function initModal() {
    const modal = document.getElementById('issue-modal');
    const closeButton = document.querySelector('.close-modal');

    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Close the modal when clicking outside of it
    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
}
