// Global variable for the map instance
let map;
let markersLayer; // Layer group to hold markers for easy clearing

// Helper function to display messages on the map view
function displayMapMessage(message, type = 'info') { // type can be 'info', 'success', 'warning', 'danger'
    const messageElement = document.getElementById('map-message');
    const errorElement = document.getElementById('map-error');

    // Ensure elements exist before proceeding
    if (!messageElement || !errorElement) {
        console.error("Map message or error element not found in the DOM.");
        // Fallback to alert if elements are missing
        alert(`(${type.toUpperCase()}) ${message}`);
        return;
    }

    // Clear previous messages/errors first
    messageElement.style.display = 'none';
    messageElement.textContent = '';
    messageElement.className = 'alert mt-2'; // Reset classes
    errorElement.style.display = 'none';
    errorElement.textContent = '';

    let targetElement;
    let alertClass;

    if (type === 'danger') {
        targetElement = errorElement;
        alertClass = 'alert-danger';
    } else {
        targetElement = messageElement;
        // Map type to Bootstrap alert class (info, success, warning)
        alertClass = `alert-${type === 'info' ? 'info' : type === 'success' ? 'success' : 'warning'}`;
    }

    targetElement.textContent = message;
    targetElement.classList.add(alertClass);
    targetElement.style.display = 'block';

    // Optional: Hide the message after a few seconds for non-errors
    if (type !== 'danger') {
        setTimeout(() => {
            // Check if the element still exists and is visible before hiding
            if (targetElement && targetElement.style.display !== 'none') {
                 targetElement.style.display = 'none';
            }
        }, 3000); // Hide after 3 seconds
    }
}


// Function to initialize the map view
function initMapView() {
    const mapElement = document.getElementById('map');
    const mapErrorElement = document.getElementById('map-error'); // Keep reference for initial setup
    const mapMessageElement = document.getElementById('map-message'); // Get message element

    if (!mapElement) {
        console.error("Map container element not found.");
        return;
    }
    // Hide messages initially
    if (mapErrorElement) mapErrorElement.style.display = 'none';
    if (mapMessageElement) mapMessageElement.style.display = 'none';


    // --- Initialize Leaflet Map ---
    // Default center (e.g., San Francisco) if geolocation fails or is denied
    const defaultCoords = [37.7749, -122.4194];
    const defaultZoom = 13;

    // Check if map is already initialized, remove if it is
    if (map) {
        map.remove();
    }

    map = L.map('map').setView(defaultCoords, defaultZoom);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Initialize marker layer group
    markersLayer = L.layerGroup().addTo(map);

    // --- Get User Location and Fetch Data ---
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const userCoords = [position.coords.latitude, position.coords.longitude];
                map.setView(userCoords, defaultZoom); // Center map on user
                fetchAndDisplayMarkers(position.coords.latitude, position.coords.longitude);
            },
            (error) => {
                console.warn(`Geolocation error (${error.code}): ${error.message}`);
                displayMapMessage("Could not get your location. Showing default area.", 'warning');
                // Fetch data for default location if geolocation fails
                fetchAndDisplayMarkers(defaultCoords[0], defaultCoords[1]);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 } // Geolocation options
        );
    } else {
        console.warn("Geolocation is not supported by this browser.");
        displayMapMessage("Geolocation not supported. Showing default area.", 'warning');
        // Fetch data for default location if geolocation is not supported
        fetchAndDisplayMarkers(defaultCoords[0], defaultCoords[1]);
    }

    // --- Add event listener for radius slider ---
    const radiusSlider = document.getElementById('radius-slider');
    const radiusValueSpan = document.getElementById('radius-value');

    if (radiusSlider && radiusValueSpan) {
        // Use 'input' event for immediate feedback as slider moves
        radiusSlider.addEventListener('input', () => {
            const radiusKm = radiusSlider.value;
            radiusValueSpan.textContent = `${radiusKm} km`;
        });
        // Use 'change' event to trigger API call only when user releases slider
        radiusSlider.addEventListener('change', () => {
            const radiusKm = radiusSlider.value;
            const center = map.getCenter(); // Get current map center
            fetchAndDisplayMarkers(center.lat, center.lng, radiusKm);
        });
    } else {
        console.warn("Radius slider or value span not found.");
    }

    // --- Add event listener for popup button clicks (using delegation) ---
    map.on('popupopen', function(e) {
        const popupNode = e.popup.getElement();
        if (!popupNode) return;

        popupNode.addEventListener('click', async (event) => {
            const button = event.target.closest('.thumb-btn'); // Find closest button
            if (button) {
                const action = button.getAttribute('data-action');
                const submissionId = button.getAttribute('data-id');
                if (action && submissionId) {
                    await handleThumbAction(submissionId, action, button.closest('.leaflet-popup-content'));
                }
            }
        });
    });

}

// Function to fetch submissions and display markers
async function fetchAndDisplayMarkers(latitude, longitude, radiusKm = 5.0) {
    console.log(`Fetching markers near ${latitude}, ${longitude} within ${radiusKm}km`);
    // Clear previous errors/messages when fetching new markers
    const mapErrorElement = document.getElementById('map-error');
    const mapMessageElement = document.getElementById('map-message');
    if (mapErrorElement) mapErrorElement.style.display = 'none';
    if (mapMessageElement) mapMessageElement.style.display = 'none';


    try {
        const response = await axios.get(`${API_BASE_URL}/submissions/nearby`, {
            params: {
                latitude: latitude,
                longitude: longitude,
                radius_km: radiusKm
            }
        });

        const submissions = response.data;
        console.log("Received submissions:", submissions);

        // Clear existing markers
        markersLayer.clearLayers();

        if (submissions.length === 0) {
            // Optionally display a message if no submissions are found
            console.log("No nearby submissions found.");
            displayMapMessage("No nearby submissions found in this area.", 'info');
            return;
        }

        // Add new markers
        submissions.forEach(sub => {
            // GeoAlchemy returns WKT: "SRID=4326;POINT(lon lat)"
            // We need to parse lat/lon from this string
            // Use the 'location_wkt' field provided by the backend response model
            // Corrected regex: Removed extra escaped parenthesis after POINT
            const pointMatch = sub.location_wkt.match(/POINT \(([-\d.]+) ([-\d.]+)\)/);
            if (pointMatch && pointMatch.length === 3) {
                const lon = parseFloat(pointMatch[1]);
                const lat = parseFloat(pointMatch[2]);

                const marker = L.marker([lat, lon]);

                // Create popup content with unique IDs for counts
                const popupContentId = `popup-content-${sub.id}`;
                let popupContent = `<div id="${popupContentId}">`; // Wrap content for easier update
                popupContent += `<b>${sub.description || 'No description'}</b><br>`;
                popupContent += `<img src="${sub.image_url}" alt="Submission thumbnail" width="100"><br>`; // Basic image display
                popupContent += `<small>Uploaded: ${new Date(sub.uploaded_at).toLocaleString()}</small><br>`;
                // Add thumbs up/down buttons and counts
                popupContent += `
                    <button class="btn btn-sm btn-outline-success thumb-btn me-1" data-id="${sub.id}" data-action="up">
                        👍 <span class="thumb-count-up">${sub.thumbs_up_count}</span>
                    </button>
                    <button class="btn btn-sm btn-outline-danger thumb-btn" data-id="${sub.id}" data-action="down">
                        👎 <span class="thumb-count-down">${sub.thumbs_down_count}</span>
                    </button>
                `;
                popupContent += `</div>`; // Close wrapper div

                marker.bindPopup(popupContent);
                markersLayer.addLayer(marker);
            } else {
                console.warn("Could not parse location WKT:", sub.location_wkt);
            }
        });

    } catch (error) {
        console.error("Failed to fetch or display markers:", error);
        let message = "Failed to load nearby photos. Please try again later.";
        if (error.response && error.response.data && error.response.data.detail) {
             message = `Error: ${error.response.data.detail}`;
        }
        displayMapMessage(message, 'danger');
    }
}

// Ensure Leaflet is loaded before calling initMapView
// This might require adjustments based on how/when Leaflet script is loaded in index.html
// For now, assuming Leaflet is available when main.js calls initMapView

// --- Function to handle Thumbs Up/Down clicks ---
async function handleThumbAction(submissionId, action, popupContentElement) {
    const endpoint = `${API_BASE_URL}/submissions/${submissionId}/thumbs_${action}`;
    console.log(`Sending POST to ${endpoint}`);

    try {
        const response = await axios.post(endpoint, {}, { // Added empty object for POST data
             headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
        });
        const updatedSubmission = response.data;
        console.log(`Thumbs ${action} successful:`, updatedSubmission);

        // Update the counts directly in the popup content if it's still open/available
        if (popupContentElement) {
            const upCountSpan = popupContentElement.querySelector('.thumb-count-up');
            const downCountSpan = popupContentElement.querySelector('.thumb-count-down');
            if (upCountSpan) upCountSpan.textContent = updatedSubmission.thumbs_up_count;
            if (downCountSpan) downCountSpan.textContent = updatedSubmission.thumbs_down_count;
        }
        // Optionally disable the button clicked or provide other feedback

    } catch (error) {
        console.error(`Failed to add thumbs ${action}:`, error);
        // Show error to user
        let message = `Failed to record vote.`;
         if (error.response && error.response.data && error.response.data.detail) {
             message = `Error: ${error.response.data.detail}`;
         } else if (error.response && error.response.status === 401) {
             message = "Authentication required to vote. Please log in.";
         }
        displayMapMessage(message, 'danger'); // Use helper function
    }
}