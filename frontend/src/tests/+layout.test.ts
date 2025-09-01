import { render, screen, fireEvent } from '@testing-library/svelte';
import Layout from '../routes/+layout.svelte';
import { auth, logout } from '$lib/auth';
import { goto } from '$app/navigation';
import { describe, beforeEach, test, expect, vi } from 'vitest';

// Mock dependencies
vi.mock('$app/navigation', () => ({
    goto: vi.fn(),
}));

vi.mock('$lib/auth', async (importOriginal) => {
  const { writable } = await import('svelte/store');
  const originalAuth = writable({ isAuthenticated: false, user: null });

  // Keep the original User interface if needed, or other exports
  const originalModule = await importOriginal();

  return {
    ...originalModule,
    auth: originalAuth,
    login: vi.fn((user) => originalAuth.set({ isAuthenticated: true, user })),
    logout: vi.fn(() => originalAuth.set({ isAuthenticated: false, user: null })),
  };
});


describe('Layout', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();

    // Set initial state to logged-in for these tests
    auth.set({
      isAuthenticated: true,
      user: { username: 'testuser' },
    });
  });

  test('renders Logout button and welcome text when authenticated', () => {
    render(Layout, {});
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Welcome, testuser')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  test('calls logout and redirects when logout button is clicked', async () => {
    const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem');
    render(Layout, {});

    const logoutButton = screen.getByText('Logout');
    await fireEvent.click(logoutButton);

    // Check that our mocked logout function was called
    expect(logout).toHaveBeenCalled();

    // Check that localStorage was cleared
    expect(removeItemSpy).toHaveBeenCalledWith('accessToken');

    // Check that user was redirected
    expect(goto).toHaveBeenCalledWith('/login');
  });
});
