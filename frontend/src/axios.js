// src/axios.js
import axios from 'axios';

// Determine the base URL for the API
// Use environment variable if available (good for production), otherwise default to localhost
// Ensure your FastAPI backend is running on port 8000 (or adjust if different)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL, // All requests will be prefixed with this URL
  headers: {
    'Content-Type': 'application/json', // Default content type for POST/PUT/PATCH requests
    'Accept': 'application/json',      // Specify that we expect JSON responses
  },
  // You can add other default configurations here, like timeout:
  // timeout: 10000, // Optional: 10 seconds timeout
});

// --- Optional: Interceptors ---
// You might want to add interceptors later for things like:
// - Adding Authorization tokens to requests
// - Handling global API errors (e.g., showing notifications, redirecting on 401 Unauthorized)

// Example Request Interceptor (e.g., for adding auth token)
/*
apiClient.interceptors.request.use(
  (config) => {
    // const token = localStorage.getItem('authToken'); // Or get from Pinia store
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    // Handle request error
    return Promise.reject(error);
  }
);
*/

// Example Response Interceptor (e.g., for global error handling)
/*
apiClient.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    // You might want to directly return response.data here if preferred
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    console.error('API Error:', error.response || error.message);

    // Example: Handle specific error codes globally
    // if (error.response && error.response.status === 401) {
    //   // Redirect to login or refresh token logic
    //   router.push('/login'); // Make sure router is accessible here or use event bus/store action
    // }

    // Show a user-friendly error message (e.g., using Element Plus notification)
    // ElNotification({ title: 'Error', message: error.response?.data?.detail || error.message, type: 'error' });


    return Promise.reject(error); // Important: reject the promise so downstream .catch() can handle it
  }
);
*/

export default apiClient;