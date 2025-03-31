// Function to initialize the profile view
async function initProfileView() {
    console.log("Initializing Profile View");
    const profileError = document.getElementById('profile-error');
    const profileSuccess = document.getElementById('profile-success');
    const profileEmail = document.getElementById('profile-email');
    const profileAvatarUrl = document.getElementById('profile-avatar-url');
    const profileUpdateForm = document.getElementById('profile-update-form');
    const avatarUrlInput = document.getElementById('avatar-url');
    const homeLatInput = document.getElementById('home-latitude');
    const homeLonInput = document.getElementById('home-longitude');
    const defaultRadiusInput = document.getElementById('default-radius');
    const setHomeLocationBtn = document.getElementById('set-home-location-current');
    const submissionsListDiv = document.getElementById('profile-submissions-list'); // Get submissions container

    // Hide messages initially
    profileError.style.display = 'none';
    profileSuccess.style.display = 'none';

    // --- Fetch current user data ---
    try {
        const response = await axios.get(`${API_BASE_URL}/users/me`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
        });
        const user = response.data;
        console.log("User data received:", user);

        // Populate display fields
        profileEmail.textContent = user.email || 'N/A';
        profileAvatarUrl.textContent = user.avatar_url || 'None';

        // Populate form fields with current values
        avatarUrlInput.value = user.avatar_url || '';
        defaultRadiusInput.value = user.default_radius_km || 5.0;

        // Populate home location if available (requires parsing WKT)
        if (user.home_location) {
            const pointMatch = user.home_location.match(/POINT\(([-\d.]+) ([-\d.]+)\)/);
            if (pointMatch && pointMatch.length === 3) {
                homeLonInput.value = parseFloat(pointMatch[1]);
                homeLatInput.value = parseFloat(pointMatch[2]);
            } else {
                console.warn("Could not parse home_location WKT:", user.home_location);
            }
        }

    } catch (error) {
        console.error("Failed to fetch user profile:", error);
        profileError.textContent = "Failed to load profile data. Please try logging in again.";
        if (error.response && error.response.status === 401) {
             profileError.textContent = "Authentication failed. Please log in again.";
             // Optionally redirect to login: window.location.hash = '#login';
        }
        profileError.style.display = 'block';
        return; // Stop initialization if profile fetch fails
    }

    // --- Handle "Use Current Location" Button ---
    if (setHomeLocationBtn) {
        setHomeLocationBtn.addEventListener('click', () => {
            if ('geolocation' in navigator) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        homeLatInput.value = position.coords.latitude;
                        homeLonInput.value = position.coords.longitude;
                        profileSuccess.textContent = "Current location populated.";
                        profileSuccess.style.display = 'block';
                        setTimeout(() => profileSuccess.style.display = 'none', 3000);
                    },
                    (error) => {
                        console.warn(`Geolocation error (${error.code}): ${error.message}`);
                        profileError.textContent = "Could not get current location.";
                        profileError.style.display = 'block';
                    }
                );
            } else {
                profileError.textContent = "Geolocation is not supported by this browser.";
                profileError.style.display = 'block';
            }
        });
    }


    // --- Handle Profile Update Form Submission ---
    if (profileUpdateForm) {
        profileUpdateForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            profileError.style.display = 'none';
            profileSuccess.style.display = 'none';

            const formData = new FormData(profileUpdateForm);
            const updateData = {};

            const avatarUrl = formData.get('avatar_url');
            if (avatarUrl) {
                updateData.avatar_url = avatarUrl;
            }

            const defaultRadius = formData.get('default_radius_km');
            if (defaultRadius) {
                updateData.default_radius_km = parseFloat(defaultRadius);
            }

            const homeLat = formData.get('home_latitude');
            const homeLon = formData.get('home_longitude');

            // Only include home_location if both lat and lon are provided and valid numbers
            if (homeLat && homeLon && !isNaN(parseFloat(homeLat)) && !isNaN(parseFloat(homeLon))) {
                 // Convert to WKT string: SRID=4326;POINT(lon lat)
                updateData.home_location = `SRID=4326;POINT(${parseFloat(homeLon)} ${parseFloat(homeLat)})`;
            } else if (homeLat || homeLon) {
                // If only one is provided or they are invalid, show an error
                profileError.textContent = "Please provide both valid Latitude and Longitude for Home Location, or leave both blank.";
                profileError.style.display = 'block';
                return;
            }
            // If both are blank, home_location is implicitly excluded (or set to null by backend if desired)

            console.log("Submitting profile update:", updateData);

            try {
                const response = await axios.put(`${API_BASE_URL}/users/me`, updateData, {
                    headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
                });

                console.log("Profile update successful:", response.data);
                profileSuccess.textContent = "Profile updated successfully!";
                profileSuccess.style.display = 'block';

                // Optionally re-populate fields with updated data
                profileAvatarUrl.textContent = response.data.avatar_url || 'None';
                // Update form defaults as well if needed
                avatarUrlInput.value = response.data.avatar_url || '';
                defaultRadiusInput.value = response.data.default_radius_km || 5.0;
                 if (response.data.home_location) {
                    const pointMatch = response.data.home_location.match(/POINT\(([-\d.]+) ([-\d.]+)\)/);
                    if (pointMatch && pointMatch.length === 3) {
                        homeLonInput.value = parseFloat(pointMatch[1]);
                        homeLatInput.value = parseFloat(pointMatch[2]);
                    }
                } else {
                    homeLatInput.value = '';
                    homeLonInput.value = '';
                }


            } catch (error) {
                console.error("Profile update failed:", error);
                profileError.textContent = "Profile update failed. Please try again.";
                 if (error.response && error.response.data && error.response.data.detail) {
                    profileError.textContent = `Update failed: ${error.response.data.detail}`;
                 }
                profileError.style.display = 'block';
            }
        });
    }

    // --- Fetch and display user submissions ---
    if (submissionsListDiv) {
        await fetchAndDisplayUserSubmissions(submissionsListDiv, profileError);
    } else {
        console.warn("Submissions list container not found.");
    }
}

// --- Helper function to fetch and display user submissions ---
async function fetchAndDisplayUserSubmissions(container, errorElement) {
    container.innerHTML = '<p>Loading your submissions...</p>'; // Show loading state
    errorElement.style.display = 'none';

    try {
        const response = await axios.get(`${API_BASE_URL}/users/me/submissions`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
        });
        const submissions = response.data;
        console.log("User submissions received:", submissions);

        if (!submissions || submissions.length === 0) {
            container.innerHTML = '<p>You have not submitted any photos yet.</p>';
            return;
        }

        // Clear loading message
        container.innerHTML = '';

        // Create list group
        const listGroup = document.createElement('ul');
        listGroup.className = 'list-group';

        submissions.forEach(sub => {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item d-flex justify-content-between align-items-center flex-wrap';
            listItem.setAttribute('data-submission-id', sub.id); // Add ID for reference

            // Calculate if editable (within 10 minutes)
            const uploadedDate = new Date(sub.uploaded_at + 'Z'); // Assume UTC
            const now = new Date();
            const isEditable = (now - uploadedDate) < (10 * 60 * 1000); // 10 minutes in milliseconds

            // Content Div
            const contentDiv = document.createElement('div');
            contentDiv.innerHTML = `
                <img src="${sub.image_url}" alt="Thumbnail" width="60" height="60" class="me-3 float-start">
                <p class="mb-1">${sub.description || '<em>No description</em>'}</p>
                <small class="text-muted">Uploaded: ${uploadedDate.toLocaleString()}</small>
            `;

            // Buttons Div
            const buttonsDiv = document.createElement('div');
            buttonsDiv.className = 'mt-2 mt-md-0'; // Margin top on small screens

            const editButton = document.createElement('button');
            editButton.className = 'btn btn-sm btn-outline-secondary me-2 edit-submission-btn';
            editButton.textContent = 'Edit';
            editButton.disabled = !isEditable; // Disable if past 10 minutes
            if (!isEditable) {
                editButton.title = "Editing only allowed within 10 minutes of upload.";
            }

            const deleteButton = document.createElement('button');
            deleteButton.className = 'btn btn-sm btn-outline-danger delete-submission-btn';
            deleteButton.textContent = 'Delete';

            buttonsDiv.appendChild(editButton);
            buttonsDiv.appendChild(deleteButton);

            listItem.appendChild(contentDiv);
            listItem.appendChild(buttonsDiv);
            listGroup.appendChild(listItem);
        });

        container.appendChild(listGroup);

        // Add event listener using event delegation
        container.addEventListener('click', (event) => {
            const target = event.target;
            const submissionItem = target.closest('.list-group-item');
            if (!submissionItem) return;

            const submissionId = submissionItem.getAttribute('data-submission-id');

            if (target.classList.contains('edit-submission-btn')) {
                handleEditSubmission(submissionId);
            } else if (target.classList.contains('delete-submission-btn')) {
                handleDeleteSubmission(submissionId, submissionItem); // Pass item to remove from UI
            }
        });

    } catch (error) {
        console.error("Failed to fetch user submissions:", error);
        container.innerHTML = ''; // Clear loading message
        errorElement.textContent = "Failed to load your submissions.";
        errorElement.style.display = 'block';
    }
}

// --- Placeholder functions for Edit/Delete ---
function handleEditSubmission(submissionId) {
    console.log(`Edit button clicked for submission ID: ${submissionId}`);
    // TODO: Implement edit logic (e.g., show modal with description input)
    // 1. Fetch submission details GET /submissions/{submissionId} (optional, might have data already)
    // 2. Prompt user for new description (e.g., using prompt() or a modal)
    const newDescription = prompt(`Enter new description for submission ${submissionId}:`);
    if (newDescription === null) return; // User cancelled

    // 3. Send PUT request to /submissions/{submissionId}
    axios.put(`${API_BASE_URL}/submissions/${submissionId}`, { description: newDescription }, {
        headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
    })
    .then(response => {
        console.log("Update successful:", response.data);
        alert("Submission updated successfully!");
        // Update the description in the UI
        const listItem = document.querySelector(`.list-group-item[data-submission-id="${submissionId}"]`);
        if (listItem) {
            const descElement = listItem.querySelector('p.mb-1');
            if (descElement) {
                descElement.innerHTML = response.data.description || '<em>No description</em>';
            }
        }
    })
    .catch(error => {
        console.error("Update failed:", error);
        let message = "Failed to update submission.";
        if (error.response && error.response.data && error.response.data.detail) {
            message = `Update failed: ${error.response.data.detail}`;
        }
        alert(message);
    });
}

async function handleDeleteSubmission(submissionId, listItemElement) {
    console.log(`Delete button clicked for submission ID: ${submissionId}`);
    if (window.confirm(`Are you sure you want to delete submission ${submissionId}? This cannot be undone.`)) {
        // TODO: Implement delete logic
        // 1. Send DELETE request to /submissions/{submissionId}
        try {
            const response = await axios.delete(`${API_BASE_URL}/submissions/${submissionId}`, {
                 headers: { Authorization: `Bearer ${localStorage.getItem('accessToken')}` }
            });
            console.log("Delete successful:", response.data);
            alert("Submission deleted successfully!");
            // 2. Remove the list item from the UI
            listItemElement.remove();
        } catch (error) {
             console.error("Delete failed:", error);
             let message = "Failed to delete submission.";
             if (error.response && error.response.data && error.response.data.detail) {
                 message = `Delete failed: ${error.response.data.detail}`;
             }
             alert(message);
        }
    }
}