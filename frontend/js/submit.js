let currentStream = null; // Global variable to hold the camera stream

// Function to initialize the submit view
function initSubmitView() {
    const submitForm = document.getElementById('submit-form');
    const imageFile = document.getElementById('image-file');
    const description = document.getElementById('description');
    const latitudeInput = document.getElementById('latitude');
    const longitudeInput = document.getElementById('longitude');
    const locationStatus = document.getElementById('location-status');
    const submitBtn = document.getElementById('submit-btn');
    const submitMessage = document.getElementById('submit-message');

    // Camera elements
    const useCameraBtn = document.getElementById('use-camera-btn');
    const cameraView = document.getElementById('camera-view');
    const cameraVideo = document.getElementById('camera-video');
    const captureBtn = document.getElementById('capture-btn');
    const cancelCameraBtn = document.getElementById('cancel-camera-btn');
    const cameraCanvas = document.getElementById('camera-canvas');
    const imagePreview = document.getElementById('image-preview');

    // --- Get Geolocation ---
    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                latitudeInput.value = position.coords.latitude;
                longitudeInput.value = position.coords.longitude;
                locationStatus.textContent = `Location acquired: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`;
                locationStatus.classList.remove('text-muted');
                locationStatus.classList.add('text-success');
                submitBtn.disabled = false; // Enable submit button
            },
            (error) => {
                console.error(`Geolocation error (${error.code}): ${error.message}`);
                locationStatus.textContent = `Error getting location: ${error.message}. Please ensure location services are enabled.`;
                locationStatus.classList.remove('text-muted');
                locationStatus.classList.add('text-danger');
                submitBtn.disabled = true; // Keep button disabled
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    } else {
        locationStatus.textContent = "Geolocation is not supported by this browser.";
        locationStatus.classList.remove('text-muted');
        locationStatus.classList.add('text-warning');
        submitBtn.disabled = true; // Keep button disabled
    }

    // --- Camera Logic ---

    async function startCamera() {
        try {
            if (currentStream) {
                stopCamera(); // Stop existing stream first
            }
            currentStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
            cameraVideo.srcObject = currentStream;
            cameraView.style.display = 'block';
            imagePreview.style.display = 'none'; // Hide file preview if camera is active
            imageFile.value = ''; // Clear file input if camera is used
            displaySubmitMessage('Camera started. Point and capture.', 'info');
        } catch (err) {
            console.error("Error accessing camera:", err);
            displaySubmitMessage(`Error accessing camera: ${err.message}`, 'danger');
            stopCamera(); // Ensure cleanup if error occurs
        }
    }

    function stopCamera() {
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
            cameraVideo.srcObject = null;
        }
        cameraView.style.display = 'none';
    }

    function capturePhoto() {
        if (!currentStream) {
            displaySubmitMessage('Camera not active.', 'warning');
            return;
        }
        const context = cameraCanvas.getContext('2d');
        // Set canvas dimensions to video dimensions
        cameraCanvas.width = cameraVideo.videoWidth;
        cameraCanvas.height = cameraVideo.videoHeight;
        // Draw the current video frame onto the canvas
        context.drawImage(cameraVideo, 0, 0, cameraCanvas.width, cameraCanvas.height);

        // Convert canvas to blob, then to File
        cameraCanvas.toBlob(async (blob) => {
            if (blob) {
                // Create a File object
                const capturedFile = new File([blob], `capture-${Date.now()}.jpg`, { type: 'image/jpeg' });

                // Use DataTransfer to set the file input's files property
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(capturedFile);
                imageFile.files = dataTransfer.files;

                // Show preview
                const reader = new FileReader();
                reader.onload = (e) => {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                }
                reader.readAsDataURL(capturedFile);

                displaySubmitMessage('Photo captured!', 'success');
            } else {
                 displaySubmitMessage('Failed to capture photo.', 'danger');
            }
             stopCamera(); // Stop camera after capture
        }, 'image/jpeg', 0.9); // Use JPEG format with 90% quality
    }

    // Event Listeners for Camera Buttons
    useCameraBtn.addEventListener('click', startCamera);
    captureBtn.addEventListener('click', capturePhoto);
    cancelCameraBtn.addEventListener('click', stopCamera);

    // --- Image File Preview ---
    imageFile.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                stopCamera(); // Stop camera if a file is selected
            }
            reader.readAsDataURL(file);
        } else {
            imagePreview.src = '#'; // Clear preview if no file selected
            imagePreview.style.display = 'none';
        }
    });


    // --- Handle Form Submission ---
    submitForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default submission
        submitMessage.style.display = 'none'; // Hide previous messages
        submitMessage.className = 'alert'; // Reset classes
        submitBtn.disabled = true; // Disable button during submission

        const token = localStorage.getItem('accessToken');
        if (!token) {
            displaySubmitMessage("Authentication error. Please log in again.", 'danger');
            submitBtn.disabled = false; // Re-enable button
            return;
        }

        // Create FormData object
        const formData = new FormData();
        // Ensure there's a file selected either via input or camera
        if (!imageFile.files || imageFile.files.length === 0) {
             displaySubmitMessage("Please select a photo or capture one using the camera.", 'warning');
             submitBtn.disabled = false; // Re-enable button
             return;
        }
        formData.append('image', imageFile.files[0]); // Use 'image' key to match backend endpoint parameter
        formData.append('description', description.value);
        formData.append('latitude', latitudeInput.value);
        formData.append('longitude', longitudeInput.value);

        try {
            const response = await axios.post(`${API_BASE_URL}/submissions/`, formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    // 'Content-Type': 'multipart/form-data' // Axios sets this automatically for FormData
                }
            });

            console.log("Submission successful:", response.data);
            displaySubmitMessage("Photo submitted successfully!", 'success');
            submitForm.reset(); // Clear the form fields
            imagePreview.style.display = 'none'; // Hide preview
            imagePreview.src = '#';
            stopCamera(); // Ensure camera is off
            locationStatus.textContent = "Fetching location..."; // Reset location status
            locationStatus.className = 'mb-3 text-muted'; // Reset classes
            // Re-fetch location? Or assume it's still valid? For now, just reset text.
            // Re-enable button after short delay to prevent double submission
            setTimeout(() => { submitBtn.disabled = false; }, 500);
            // Optionally redirect after success
            // window.location.hash = '#map';

        } catch (error) {
            console.error("Submission failed:", error);
            // Log the raw error and the full response object if available
            console.error("Submission failed. Raw error object:", error);
            if (error.response) {
                console.error("Backend response details:", JSON.stringify(error.response, null, 2));
            }
            let message = "Submission failed. Please try again.";
             if (error.response && error.response.data && error.response.data.detail) {
                 if (typeof error.response.data.detail === 'string') {
                     message = `Error: ${error.response.data.detail}`;
                 } else if (Array.isArray(error.response.data.detail)) { // Handle validation errors
                     message = error.response.data.detail.map(err => `${err.loc.slice(-1)[0]}: ${err.msg}`).join(', ');
                 }
             } else if (error.response && error.response.status === 401) {
                 message = "Authentication failed. Please log in again.";
             }
            displaySubmitMessage(message, 'danger');
        } finally {
            // Re-enable button unless successful and redirected
            // Re-enable button immediately on failure
            submitBtn.disabled = false;
        }
    });
}

// Helper function to display messages on the submit view
function displaySubmitMessage(message, type = 'info') { // type can be 'info', 'success', 'warning', 'danger'
    const messageElement = document.getElementById('submit-message');
    if (!messageElement) return; // Exit if element not found

    messageElement.textContent = message;
    messageElement.className = `alert alert-${type} mt-2`; // Set Bootstrap class
    messageElement.style.display = 'block';

    // Optional: Hide after a delay for non-errors
    if (type !== 'danger') {
        setTimeout(() => {
            if (messageElement) messageElement.style.display = 'none';
        }, 3000);
    }
}