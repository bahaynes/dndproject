// src/lib/auth.ts
import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';

// Define a more detailed User interface based on the backend schema
export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: 'player' | 'admin';
  character: {
    id: number;
    name: string;
  } | null;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

// Create a writable store for the authentication state
export const auth = writable<AuthState>({
  user: null,
  token: null,
  isAuthenticated: false,
});

// Helper function to get the token from local storage
function getTokenFromLocalStorage(): string | null {
  if (!browser) return null;
  return localStorage.getItem('jwt_token');
}

// Helper function to get user data from the backend
async function fetchUser(token: string): Promise<User | null> {
  try {
    // We assume the API is running on the same host or is configured via a proxy
    const response = await fetch(`/api/users/me/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (response.ok) {
      const user: User = await response.json();
      return user;
    }
  } catch (error) {
    console.error('Failed to fetch user:', error);
  }
  return null;
}

// Function to initialize the auth state when the app loads
export async function initializeAuth() {
  if (!browser) return;

  const token = getTokenFromLocalStorage();
  if (token && !get(auth).isAuthenticated) {
    const user = await fetchUser(token);
    if (user) {
      auth.set({
        user,
        token,
        isAuthenticated: true,
      });
    } else {
      // Token is invalid or expired, log out
      logout();
    }
  }
}

// Login function
export async function login(token: string) {
  if (!browser) return;

  localStorage.setItem('jwt_token', token);
  const user = await fetchUser(token);
  if (user) {
    auth.set({
      user,
      token,
      isAuthenticated: true,
    });
  }
}

// Logout function
export function logout() {
  if (!browser) return;

  localStorage.removeItem('jwt_token');
  auth.set({
    user: null,
    token: null,
    isAuthenticated: false,
  });
  // Optional: redirect to login page
  // goto('/login');
}

// A simple wrapper for fetch that includes the auth token
export async function authedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = get(auth).token || getTokenFromLocalStorage();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  options.headers = headers;
  return fetch(url, options);
}
