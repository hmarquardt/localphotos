// This function will be called by main.js when the login view is loaded
function initLoginView() {
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');

    if (!loginForm) {
        console.error("Login form not found in the loaded view.");
        return;
    }

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission
        loginError.style.display = 'none'; // Hide previous errors

        const formData = new FormData(loginForm);
        // Note: FastAPI's OAuth2PasswordRequestForm expects 'username' and 'password'
        // We named the email input 'username' in the HTML form to match this.

        try {
            const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            if (response.data.access_token) {
                localStorage.setItem('accessToken', response.data.access_token);
                console.log("Login successful, token stored.");
                updateLoginStatus(); // Update nav bar (defined in main.js)
                // Redirect to the map view after successful login
                window.location.hash = '#map';
            } else {
                throw new Error("Access token not received.");
            }

        } catch (error) {
            console.error("Login failed:", error);
            let errorMessage = "Login failed. Please check your credentials.";
            if (error.response && error.response.data && error.response.data.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.message) {
                errorMessage = error.message;
            }
            loginError.textContent = errorMessage;
            loginError.style.display = 'block';
        }
    });
}

// Add registration logic later
// function initRegisterView() { ... }