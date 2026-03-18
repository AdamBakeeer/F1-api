/**
 * API Configuration
 * Determines the API base URL based on environment
 */

// Get API URL from environment variable or derive from window location
const API_BASE_URL = (import.meta.env.VITE_API_URL || (() => {
  // In production, use current domain
  if (import.meta.env.PROD) {
    return `${window.location.protocol}//${window.location.host}`
  }
  // In development, use local backend
  return 'http://127.0.0.1:8000'
})()).replace(/\/$/, '') // Remove trailing slash if present

export { API_BASE_URL }
