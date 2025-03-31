// Define the base URL for the backend API
// Adjust this if your backend runs on a different port or domain
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

// You can also configure Axios defaults here if needed
// Example: Setting up interceptors to add the auth token automatically
/*
axios.interceptors.request.use(config => {
    const token = localStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => {
    return Promise.reject(error);
});
*/