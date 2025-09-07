import { render, screen, fireEvent } from '@testing-library/svelte';
import LoginPage from '../routes/login/+page.svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { login } from '$lib/auth';
import { goto } from '$app/navigation';
import { writable } from 'svelte/store';
import type { Page } from '@sveltejs/kit';

// Mocks
vi.mock('$lib/auth', () => ({
  login: vi.fn(),
}));

vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
}));

// Mock the page store
vi.mock('$app/stores', async (importOriginal) => {
    const { writable } = await import('svelte/store');
    const mockPageStore = writable<Page>({
        url: new URL('http://localhost/login'),
        params: {},
        route: { id: 'login' },
        status: 200,
        error: null,
        data: {},
        form: {},
    });

    return {
        __esModule: true,
        ...await importOriginal(),
        page: mockPageStore,
    };
});


// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Login Page', () => {
    let page;

    beforeEach(async () => {
        vi.clearAllMocks();
        page = (await import('$app/stores')).page;
        // Reset page store to default before each test
        page.set({
            url: new URL('http://localhost/login'),
            params: {},
            route: { id: 'login' },
            status: 200,
            error: null,
            data: {},
            form: {},
        });
    });

  const usernameInput = () => screen.getByPlaceholderText('Username');
  const passwordInput = () => screen.getByPlaceholderText('Password');
  const loginButton = () => screen.getByRole('button', { name: /login/i });

  test('renders the login form', () => {
    render(LoginPage);
    expect(usernameInput()).toBeInTheDocument();
    expect(passwordInput()).toBeInTheDocument();
    expect(loginButton()).toBeInTheDocument();
  });

  test('allows user to type in username and password', async () => {
    render(LoginPage);
    await fireEvent.input(usernameInput(), { target: { value: 'testuser' } });
    await fireEvent.input(passwordInput(), { target: { value: 'password123' } });
    expect(usernameInput()).toHaveValue('testuser');
    expect(passwordInput()).toHaveValue('password123');
  });

  test('calls login and redirects on successful submission', async () => {
    const fakeToken = 'fake-access-token';
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ access_token: fakeToken }),
    });

    render(LoginPage);
    await fireEvent.input(usernameInput(), { target: { value: 'testuser' } });
    await fireEvent.input(passwordInput(), { target: { value: 'password123' } });
    await fireEvent.click(loginButton());

    expect(mockFetch).toHaveBeenCalledWith('/token', expect.any(Object));
    await vi.waitFor(() => expect(login).toHaveBeenCalledWith(fakeToken));
    await vi.waitFor(() => expect(goto).toHaveBeenCalledWith('/dashboard'));
  });

  test('handles redirectTo parameter', async () => {
    const fakeToken = 'fake-access-token';
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ access_token: fakeToken }),
    });

    page.update(p => {
        p.url = new URL('http://localhost/login?redirectTo=%2Fmy-secret-page');
        return p;
    });

    render(LoginPage);
    await fireEvent.input(usernameInput(), { target: { value: 'testuser' } });
    await fireEvent.input(passwordInput(), { target: { value: 'password123' } });
    await fireEvent.click(loginButton());

    await vi.waitFor(() => expect(login).toHaveBeenCalledWith(fakeToken));
    await vi.waitFor(() => expect(goto).toHaveBeenCalledWith('/my-secret-page'));
  });

  test('displays an error message on failed login', async () => {
    const errorMessage = 'Incorrect username or password';
    mockFetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: errorMessage }),
    });

    render(LoginPage);
    await fireEvent.input(usernameInput(), { target: { value: 'testuser' } });
    await fireEvent.input(passwordInput(), { target: { value: 'wrongpassword' } });
    await fireEvent.click(loginButton());

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
    expect(goto).not.toHaveBeenCalled();
  });
});
