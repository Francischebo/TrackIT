import axios from 'axios';

// Choose a sensible default: prefer VITE_API_URL, otherwise
// when running on Vercel use the known Render backend, else use local '/api'.
const resolvedBase = (() => {
  const envBase = import.meta.env.VITE_API_URL;
  if (envBase) {
    console.log('[API] Using VITE_API_URL:', envBase);
    return envBase;
  }
  if (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')) {
    console.log('[API] Running on Vercel, using Render backend: https://trackit-uxil.onrender.com');
    return 'https://trackit-uxil.onrender.com';
  }
  console.log('[API] Using local /api endpoint');
  return '/api';
})();

console.log('[API] Resolved base URL:', resolvedBase);

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
    console.log('[API] Response:', response.status, response.config.url, data);
    
    // Check if the response indicates an error despite the 200 status code
    if (data && data.success === false) {
      console.warn('[API] Error in response body:', data.message);
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
    console.error('[API] Request error:', error.response?.status, error.config?.url, error.message);
    if (error.response?.data) {
      console.error('[API] Response data:', error.response.data);
    }
    if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
