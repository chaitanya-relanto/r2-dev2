/**
 * Get the appropriate API base URL based on the environment
 * Uses server-side URL for SSR/SSG and client-side URL for browser requests
 */
export function getApiBaseUrl(): string {
  // Check if we're running on the server (Node.js environment)
  if (typeof window === 'undefined') {
    // Server-side: use container-to-container communication
    return process.env.NEXT_PUBLIC_API_BASE_URL_SERVER || 'http://r2dev2-backend-container:8000';
  } else {
    // Client-side: use browser-to-host communication
    return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8015';
  }
} 