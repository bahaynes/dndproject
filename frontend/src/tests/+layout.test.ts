import { render, screen, fireEvent } from '@testing-library/svelte';
import Layout from '../routes/+layout.svelte';
import { auth, logout } from '$lib/auth';
import { goto } from '$app/navigation';
import { describe, beforeEach, test, expect, vi } from 'vitest';

// Mock dependencies
vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
}));

vi.mock('$lib/auth', async () => {
  let value = { isAuthenticated: false, user: null };
  const subscribers = new Set<any>();
  const auth = {
    subscribe: (fn: any) => {
      fn(value);
      subscribers.add(fn);
      return () => subscribers.delete(fn);
    },
    set: (v: any) => {
      value = v;
      subscribers.forEach(fn => fn(value));
    }
  };
  return {
    auth,
    login: vi.fn((user) => auth.set({ isAuthenticated: true, user })),
    logout: vi.fn(() => auth.set({ isAuthenticated: false, user: null })),
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
    // There are multiple "Dashboard" links (mobile/desktop), so we check getAll
    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
    // Updated expectation to match new layout (no "Welcome, " prefix)
    // There are multiple "testuser" elements (one for desktop, one for mobile)
    expect(screen.getAllByText('testuser')[0]).toBeInTheDocument();
    // There are multiple "Logout" buttons
    expect(screen.getAllByText('Logout')[0]).toBeInTheDocument();
  });

  test('calls logout and redirects when logout button is clicked', async () => {
    const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem');
    render(Layout, {});

    // Click the first available logout button (likely the desktop one or mobile one, doesn't matter logic is same)
    const logoutButtons = screen.getAllByText('Logout');
    await fireEvent.click(logoutButtons[0]);

    // Check that our mocked logout function was called
    expect(logout).toHaveBeenCalled();

    // Check that localStorage was cleared
    expect(removeItemSpy).toHaveBeenCalledWith('accessToken');

    // Check that user was redirected
    expect(goto).toHaveBeenCalledWith('/login');
  });
});
