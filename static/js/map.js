// static/js/map.js

let map;
let markers = [];

function initMap() {
    // Initialize the map and set its view to the chosen geographical coordinates and a zoom level
    map = L.map('map').setView([0, 0], 2);  // Center the map at the equator with a global view

    // Use CARTO's Voyager basemap
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
        tileSize: 256,
        zoomOffset: 0
    }).addTo(map);
}

// Function to update map markers based on issue data
function updateMap(issues) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    // Add new markers based on issues data
    issues.forEach(issue => {
        if (issue.latitude && issue.longitude) {
            const marker = L.marker([issue.latitude, issue.longitude]).addTo(map);
            const popupContent = `
                <b>${issue.label}</b><br>
                ${issue.description}<br>
                Status: ${issue.status}<br>
            `;
            marker.bindPopup(popupContent);
            markers.push(marker);

            // Highlight the issue card when marker is clicked
            marker.on('click', () => {
                highlightIssue(issue.id);
            });
        }
    });

    // Adjust map to fit all markers
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds());
    }
}

function highlightIssue(issueId) {
    // Find the issue card in the Reported Issues list
    const issueCard = document.querySelector(`#issues-list .issue-card[data-issue-id="${issueId}"]`);
    if (issueCard) {
        // Remove the issue card from its current position
        issueCard.remove();

        // Insert the issue card at the top of the list
        const issuesList = document.getElementById('issues-list');
        issuesList.insertBefore(issueCard, issuesList.firstChild);

        // Add a highlight effect
        issueCard.classList.add('highlighted');

        // Scroll the issue card into view
        issueCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Remove the highlight effect after 3 seconds
        setTimeout(() => {
            issueCard.classList.remove('highlighted');
        }, 3000);
    }
}
