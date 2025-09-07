import { get } from 'svelte/store';
import { auth, initializeAuth, login, logout, type User } from '$lib/auth';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

// Mock SvelteKit's browser variable
vi.mock('$app/environment', () => ({
  browser: true,
}));

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

const testUser: User = {
  id: 1,
  username: 'tester',
  email: 'test@example.com',
  is_active: true,
  role: 'player',
  character: null,
};

describe('auth store', () => {
  beforeEach(() => {
    // Reset mocks and localStorage before each test
    vi.clearAllMocks();
    localStorageMock.clear();
    // Reset store to initial state
    auth.set({ user: null, token: null, isAuthenticated: false });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('logout', () => {
    test('should clear the auth store and remove token from localStorage', () => {
      // Setup initial state
      localStorageMock.setItem('jwt_token', 'fake-token');
      auth.set({ user: testUser, token: 'fake-token', isAuthenticated: true });

      logout();

      const state = get(auth);
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(localStorageMock.getItem('jwt_token')).toBeNull();
    });
  });

  describe('login', () => {
    test('should store token, fetch user, and update store', async () => {
      const fakeToken = 'my-fake-jwt';
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testUser,
      });

      await login(fakeToken);

      expect(localStorageMock.getItem('jwt_token')).toBe(fakeToken);
      expect(mockFetch).toHaveBeenCalledWith('/api/users/me/', {
        headers: { Authorization: `Bearer ${fakeToken}` },
      });

      const state = get(auth);
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(testUser);
      expect(state.token).toBe(fakeToken);
    });
  });

  describe('initializeAuth', () => {
    test('should do nothing if no token is in localStorage', async () => {
      await initializeAuth();
      expect(mockFetch).not.toHaveBeenCalled();
      const state = get(auth);
      expect(state.isAuthenticated).toBe(false);
    });

    test('should update store if a valid token is found', async () => {
      const fakeToken = 'valid-token';
      localStorageMock.setItem('jwt_token', fakeToken);
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => testUser,
      });

      await initializeAuth();

      expect(mockFetch).toHaveBeenCalledWith('/api/users/me/', {
        headers: { Authorization: `Bearer ${fakeToken}` },
      });
      const state = get(auth);
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).toEqual(testUser);
    });

    test('should call logout if token is invalid', async () => {
      const fakeToken = 'invalid-token';
      localStorageMock.setItem('jwt_token', fakeToken);
      mockFetch.mockResolvedValueOnce({ ok: false }); // Simulate failed fetch

      await initializeAuth();

      expect(mockFetch).toHaveBeenCalledWith('/api/users/me/', {
        headers: { Authorization: `Bearer ${fakeToken}` },
      });
      const state = get(auth);
      expect(state.isAuthenticated).toBe(false);
      expect(state.user).toBeNull();
      expect(localStorageMock.getItem('jwt_token')).toBeNull();
    });

    test('should not run if already authenticated', async () => {
        const fakeToken = 'valid-token';
        localStorageMock.setItem('jwt_token', fakeToken);
        auth.set({ user: testUser, token: fakeToken, isAuthenticated: true });

        await initializeAuth();

        expect(mockFetch).not.toHaveBeenCalled();
    });
  });
});
