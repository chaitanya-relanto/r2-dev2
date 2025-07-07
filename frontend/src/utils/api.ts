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
    const url = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8015';
    console.log('🔍 API Base URL:', url);
    return url;
  }
}

/**
 * Creates a Basic Authentication header.
 * Reads credentials from environment variables.
 */
function getBasicAuthHeader(): { Authorization: string } | {} {
  const user = process.env.NEXT_PUBLIC_BASIC_AUTH_USER;
  const pass = process.env.NEXT_PUBLIC_BASIC_AUTH_PASS;

  console.log('🔍 Basic Auth Debug:', {
    user: user ? `${user.substring(0, 3)}...` : 'undefined',
    pass: pass ? `${pass.substring(0, 3)}...` : 'undefined',
    hasUser: !!user,
    hasPass: !!pass
  });

  if (user && pass) {
    const encoded = btoa(`${user}:${pass}`);
    const authHeader = { Authorization: `Basic ${encoded}` };
    console.log('✅ Basic Auth header created:', { 
      authHeaderPresent: !!authHeader.Authorization,
      encodedLength: encoded.length
    });
    return authHeader;
  }

  console.warn('⚠️ Basic Auth credentials are not set. Requests to protected endpoints may fail.');
  console.warn('Expected env vars: NEXT_PUBLIC_BASIC_AUTH_USER, NEXT_PUBLIC_BASIC_AUTH_PASS');
  
  return {};
}

export async function fetchSessions(userId: string) {
  const API_BASE_URL = getApiBaseUrl();
  const res = await fetch(`${API_BASE_URL}/chat/sessions/${userId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch sessions');
  }
  return res.json();
}

export async function fetchMessages(sessionId: string) {
  const API_BASE_URL = getApiBaseUrl();
  const res = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}/messages`);
  if (!res.ok) {
    throw new Error('Failed to fetch messages');
  }
  return res.json();
}

interface SendMessagePayload {
  user_id: string;
  query: string;
  session_id?: string;
}

export async function sendMessage(payload: SendMessagePayload) {
  const API_BASE_URL = getApiBaseUrl();
  const res = await fetch(`${API_BASE_URL}/chat/agent`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getBasicAuthHeader() 
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error('Failed to get a response from the agent.');
  }
  return res.json();
}

export async function renameSession(sessionId: string, newTitle: string) {
  const API_BASE_URL = getApiBaseUrl();
  const url = `${API_BASE_URL}/chat/sessions/${sessionId}/rename`;
  const payload = { new_title: newTitle };
  
  console.log('🔍 Rename API call:', { url, payload, sessionId, newTitle });
  
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  
  console.log('🔍 Rename API response:', { status: res.status, ok: res.ok });
  
  if (!res.ok) {
    const errorText = await res.text();
    console.error('❌ Rename API error:', { status: res.status, error: errorText });
    throw new Error(`Failed to rename session: ${res.status} ${errorText}`);
  }
  
  // Handle 204 No Content response (successful rename with no body)
  if (res.status === 204) {
    console.log('✅ Rename API success: Session renamed (204 No Content)');
    return { success: true };
  }
  
  // For other successful responses, try to parse JSON
  const result = await res.json();
  console.log('✅ Rename API success:', result);
  return result;
}

export async function deleteSession(sessionId: string) {
  const API_BASE_URL = getApiBaseUrl();
  const url = `${API_BASE_URL}/chat/sessions/${sessionId}`;
  
  console.log('🔍 Delete API call:', { url, sessionId });
  
  const res = await fetch(url, {
    method: 'DELETE',
    headers: {
      ...getBasicAuthHeader()
    }
  });
  
  console.log('🔍 Delete API response:', { status: res.status, ok: res.ok });
  
  if (!res.ok) {
    const errorText = await res.text();
    console.error('❌ Delete API error:', { status: res.status, error: errorText });
    throw new Error(`Failed to delete session: ${res.status} ${errorText}`);
  }
  
  // Handle 204 No Content response (successful deletion with no body)
  if (res.status === 204) {
    console.log('✅ Delete API success: Session deleted (204 No Content)');
    return { success: true };
  }
  
  // For other successful responses, try to parse JSON
  const result = await res.json();
  console.log('✅ Delete API success:', result);
  return result;
}

export async function getLastActiveSession(userId: string) {
  const API_BASE_URL = getApiBaseUrl();
  const url = `${API_BASE_URL}/chat/sessions/${userId}/last-active`;
  
  console.log('🔍 Last active session API call:', { url, userId });
  
  const res = await fetch(url);
  
  console.log('🔍 Last active session API response:', { status: res.status, ok: res.ok });
  
  if (!res.ok) {
    if (res.status === 404) {
      console.log('ℹ️ No active sessions found for user');
      return null;
    }
    const errorText = await res.text();
    console.error('❌ Last active session API error:', { status: res.status, error: errorText });
    throw new Error(`Failed to fetch last active session: ${res.status} ${errorText}`);
  }
  
  const result = await res.json();
  console.log('✅ Last active session API success:', result);
  return result;
}

export async function getRecommendations(sessionId: string, numMessages: number = 5) {
  const API_BASE_URL = getApiBaseUrl();
  const url = `${API_BASE_URL}/recommendations`;
  
  console.log('🔍 Recommendations API call:', { url, sessionId, numMessages });
  
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getBasicAuthHeader(),
    },
    body: JSON.stringify({
      session_id: sessionId,
      num_messages: numMessages,
    }),
  });
  
  console.log('🔍 Recommendations API response:', { status: res.status, ok: res.ok });
  
  if (!res.ok) {
    const errorText = await res.text();
    console.error('❌ Recommendations API error:', { status: res.status, error: errorText });
    throw new Error(`Failed to fetch recommendations: ${res.status} ${errorText}`);
  }
  
  const result = await res.json();
  console.log('✅ Recommendations API success:', result);

  const cleanSuggestion = (s: string) => {
    // This regex removes any trailing characters that are backslashes, quotes, or commas.
    return s.trim().replace(/[\\",]+$/, '');
  };

  if (result.suggestions && Array.isArray(result.suggestions)) {
    result.suggestions = result.suggestions.map(cleanSuggestion);
  } else if (result.suggestions && typeof result.suggestions === 'string') {
    // This is fallback logic in case the API response format changes to a single string.
    try {
      const parsedSuggestions = JSON.parse(result.suggestions);
      if (Array.isArray(parsedSuggestions)) {
        result.suggestions = parsedSuggestions.map(cleanSuggestion);
      }
    } catch (e) {
        result.suggestions = result.suggestions
        .replace(/^"|"$/g, '')
        .split('","')
        .map(cleanSuggestion);
    }
  } else if (result.suggestions && !Array.isArray(result.suggestions)) {
      console.error('❌ Unexpected type for suggestions:', typeof result.suggestions);
      result.suggestions = [];
  }
  
  return result;
}

// Debug function to test basic auth - can be called from browser console
export function testBasicAuth() {
  console.log('🧪 Testing Basic Auth Configuration...');
  
  const user = process.env.NEXT_PUBLIC_BASIC_AUTH_USER;
  const pass = process.env.NEXT_PUBLIC_BASIC_AUTH_PASS;
  
  console.log('Environment Variables:', {
    NEXT_PUBLIC_BASIC_AUTH_USER: user || 'NOT SET',
    NEXT_PUBLIC_BASIC_AUTH_PASS: pass ? '***SET***' : 'NOT SET'
  });
  
  if (user && pass) {
    const encoded = btoa(`${user}:${pass}`);
    const expectedHeader = `Basic ${encoded}`;
    console.log('Generated Auth Header:', expectedHeader);
    
    // Test against expected backend credentials
    const expectedUser = 'r2-dev2';
    const expectedPass = 'MayThe404BeWithYou!';
    const expectedEncoded = btoa(`${expectedUser}:${expectedPass}`);
    const expectedBackendHeader = `Basic ${expectedEncoded}`;
    
    console.log('Expected Backend Header:', expectedBackendHeader);
    console.log('Headers Match:', expectedHeader === expectedBackendHeader);
    
    return {
      status: 'success',
      generated: expectedHeader,
      expected: expectedBackendHeader,
      match: expectedHeader === expectedBackendHeader
    };
  } else {
    console.error('❌ Missing environment variables!');
    return {
      status: 'error',
      message: 'Missing NEXT_PUBLIC_BASIC_AUTH_USER or NEXT_PUBLIC_BASIC_AUTH_PASS'
    };
  }
}

// Test function to directly call a protected endpoint
export async function testProtectedEndpoint() {
  console.log('🧪 Testing Protected Endpoint...');
  
  const API_BASE_URL = getApiBaseUrl();
  const authHeader = getBasicAuthHeader();
  
  console.log('API Base URL:', API_BASE_URL);
  console.log('Auth Header Object:', authHeader);
  
  try {
    const testUrl = `${API_BASE_URL}/recommendations`;
    const testPayload = {
      session_id: 'test-session-id',
      num_messages: 1
    };
    
    console.log('Test Request:', {
      url: testUrl,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader
      },
      body: testPayload
    });
    
    const response = await fetch(testUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeader
      },
      body: JSON.stringify(testPayload)
    });
    
    console.log('Response Status:', response.status);
    console.log('Response Headers:', Object.fromEntries(response.headers.entries()));
    
    if (response.status === 401) {
      console.error('❌ 401 Unauthorized - Check your credentials!');
      const errorText = await response.text();
      console.error('Error Response:', errorText);
      return { status: 'unauthorized', error: errorText };
    }
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('Non-200 Response:', errorText);
      return { status: 'error', error: errorText, httpStatus: response.status };
    }
    
    const result = await response.json();
    console.log('✅ Success! Response:', result);
    return { status: 'success', data: result };
    
  } catch (error) {
    console.error('❌ Network/Fetch Error:', error);
    return { status: 'network_error', error: error instanceof Error ? error.message : String(error) };
  }
}

// Make debug functions available globally for browser console testing
if (typeof window !== 'undefined') {
  (window as any).testBasicAuth = testBasicAuth;
  (window as any).testProtectedEndpoint = testProtectedEndpoint;
} 