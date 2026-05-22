import axios from 'axios';

// Choose a sensible default: prefer VITE_API_URL, otherwise
// when running on Vercel use the known Render backend, else use local '/api'.
const resolvedBase = (() => {
  const envBase = import.meta.env.VITE_API_URL;
  if (envBase) return envBase;
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    return 'https://trackit-uxil.onrender.com';
  }
  return '/api';
})();

const api = axios.create({
  baseURL: resolvedBase,
  withCredentials: true,
  xsrfCookieName: 'csrf_access_token',
  xsrfHeaderName: 'X-CSRF-TOKEN',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add JWT token (not needed for cookies, but keeping for custom headers if any)
api.interceptors.request.use((config) => {
  return config;
});

// Interceptor to handle unified 200 OK responses with error bodies
api.interceptors.response.use(
  (response) => {
    const { data } = response;
    
    // Check if the response indicates an error despite the 200 status code
    if (data && data.success === false) {
      if (data.status_code === 401) {
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
      // Construct an error object that axios would expect
      const error = new Error(data.message || 'API Error');
      (error as any).response = response;
      return Promise.reject(error);
    }
    
    return response;
  },
  (error) => {
    // This will catch non-JSON errors or unexpected status codes (if any)
    if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
