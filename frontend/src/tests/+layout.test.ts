import { render, screen, fireEvent } from '@testing-library/svelte';
import Layout from '../routes/+layout.svelte';
import { auth, initializeAuth, logout } from '$lib/auth';
import { goto } from '$app/navigation';
import { describe, beforeEach, test, expect, vi } from 'vitest';
import { tick } from 'svelte';
import { writable } from 'svelte/store';

// Mock SvelteKit's browser and navigation modules
vi.mock('$app/environment', () => ({
  browser: true,
}));

vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
}));

// Mock our auth module
vi.mock('$lib/auth', async (importOriginal) => {
  const { writable } = await import('svelte/store');
  const mockAuthStore = writable({
    user: null,
    token: null,
    isAuthenticated: false,
  });

  return {
    ...(await importOriginal() as any),
    auth: mockAuthStore,
    initializeAuth: vi.fn(),
    logout: vi.fn(),
  };
});

describe('Layout', () => {
    let authStore;

    beforeEach(async () => {
        vi.clearAllMocks();
        // get the mock store from the mocked module
        authStore = (await import('$lib/auth')).auth;
    });

  test('renders Login and Register when not authenticated', () => {
    authStore.set({ user: null, token: null, isAuthenticated: false });
    render(Layout);

    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Register')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.queryByText('Logout')).not.toBeInTheDocument();
  });

  test('calls initializeAuth on mount', async () => {
    render(Layout);
    await tick(); // Wait for onMount to run
    expect(initializeAuth).toHaveBeenCalled();
  });

  describe('when authenticated', () => {
    const testUser = {
      id: 1,
      username: 'tester',
      email: 'test@example.com',
      is_active: true,
      role: 'player',
      character: { id: 1, name: 'Test Character' },
    };

    beforeEach(() => {
      // Set the store to an authenticated state
      authStore.set({
        user: testUser,
        token: 'fake-jwt-token',
        isAuthenticated: true,
      });
    });

    test('renders Dashboard, welcome message, and Logout button', () => {
      render(Layout);
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText(`Welcome, ${testUser.username}`)).toBeInTheDocument();
      expect(screen.getByText('Logout')).toBeInTheDocument();
      expect(screen.queryByText('Login')).not.toBeInTheDocument();
    });

    test('calls logout and redirects when logout button is clicked', async () => {
      render(Layout);

      const logoutButton = screen.getByText('Logout');
      await fireEvent.click(logoutButton);

      expect(logout).toHaveBeenCalled();
      expect(goto).toHaveBeenCalledWith('/login');
    });
  });
});
