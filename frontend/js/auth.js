// This function will be called by main.js when the login view is loaded
function initLoginView() {
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    const googleLoginBtn = document.getElementById('google-login-btn'); // Get Google button

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

    // Add event listener for Google Login button
    if (googleLoginBtn) {
        googleLoginBtn.addEventListener('click', () => {
            // Redirect the user to the backend endpoint that starts the Google OAuth flow
            window.location.href = `${API_BASE_URL}/auth/google`;
        });
    } else {
        console.warn("Google login button not found.");
    }
}

// This function will be called by main.js when the register view is loaded
function initRegisterView() {
    const registerForm = document.getElementById('register-form');
    const registerError = document.getElementById('register-error');

    if (!registerForm) {
        console.error("Register form not found in the loaded view.");
        return;
    }

    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission
        registerError.style.display = 'none'; // Hide previous errors
        registerError.classList.remove('alert-success', 'alert-danger'); // Reset classes

        const formData = new FormData(registerForm);
        const email = formData.get('email');
        const password = formData.get('password');
        // Consider adding password confirmation input in HTML and validation here

        try {
            const response = await axios.post(`${API_BASE_URL}/auth/register`, {
                email: email,
                password: password
                // Add any other fields required by UserCreate model (e.g., home_location if needed at registration)
            });

            console.log("Registration successful:", response.data);
            // Show success message in the error div
            registerError.textContent = "Registration successful! Redirecting to login...";
            registerError.classList.add('alert-success'); // Use success class
            registerError.style.display = 'block';

            // Redirect to login after a short delay
            setTimeout(() => {
                window.location.hash = '#login';
            }, 2000); // Redirect after 2 seconds

        } catch (error) {
            console.error("Registration failed:", error);
            let errorMessage = "Registration failed. Please try again.";
            if (error.response && error.response.data && error.response.data.detail) {
                // Handle specific error messages from the backend
                if (typeof error.response.data.detail === 'string') {
                    errorMessage = error.response.data.detail;
                } else if (Array.isArray(error.response.data.detail) && error.response.data.detail.length > 0) {
                    // Handle validation errors (if backend returns Pydantic errors)
                    errorMessage = error.response.data.detail.map(err => `${err.loc[1]}: ${err.msg}`).join(', ');
                }
            } else if (error.message) {
                errorMessage = error.message;
            }
            registerError.textContent = errorMessage;
            registerError.classList.add('alert-danger'); // Use danger class for errors
            registerError.style.display = 'block';
        }
    });
}