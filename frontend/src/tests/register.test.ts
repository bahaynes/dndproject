import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import RegisterPage from '../routes/register/+page.svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { login } from '$lib/auth';
import { goto } from '$app/navigation';

// Mocks
vi.mock('$lib/auth', () => ({
  login: vi.fn(),
}));

vi.mock('$app/navigation', () => ({
  goto: vi.fn(),
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Register Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const usernameInput = () => screen.getByPlaceholderText('Username');
  const emailInput = () => screen.getByPlaceholderText('Email');
  const passwordInput = () => screen.getByPlaceholderText('Password');
  const confirmPasswordInput = () => screen.getByPlaceholderText('Confirm Password');
  const registerButton = () => screen.getByRole('button', { name: /register/i });

  test('renders the register form', () => {
    render(RegisterPage);
    expect(usernameInput()).toBeInTheDocument();
    expect(emailInput()).toBeInTheDocument();
    expect(passwordInput()).toBeInTheDocument();
    expect(confirmPasswordInput()).toBeInTheDocument();
    expect(registerButton()).toBeInTheDocument();
  });

  test('calls login and redirects on successful registration', async () => {
    const fakeToken = 'fake-access-token';
    const fakeUser = {
      id: 1,
      username: 'newuser',
      email: 'new@example.com',
      access_token: fakeToken,
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(fakeUser),
    });

    render(RegisterPage);
    await fireEvent.input(usernameInput(), { target: { value: 'newuser' } });
    await fireEvent.input(emailInput(), { target: { value: 'new@example.com' } });
    await fireEvent.input(passwordInput(), { target: { value: 'password123' } });
    await fireEvent.input(confirmPasswordInput(), { target: { value: 'password123' } });
    await fireEvent.click(registerButton());

    // Wait for the success message and redirect timeout
    expect(await screen.findByText('Registration successful! Logging you in...')).toBeInTheDocument();

    expect(mockFetch).toHaveBeenCalledWith('/users/', expect.any(Object));
    await vi.waitFor(() => expect(login).toHaveBeenCalledWith(fakeToken));

    // Check that goto is called after the timeout
    await new Promise(resolve => setTimeout(resolve, 1600));
    expect(goto).toHaveBeenCalledWith('/dashboard');
  });

  test('displays an error message on failed registration', async () => {
    const errorMessage = 'This email is already registered.';
    mockFetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: errorMessage }),
    });

    render(RegisterPage);
    await fireEvent.input(usernameInput(), { target: { value: 'testuser' } });
    await fireEvent.input(emailInput(), { target: { value: 'test@example.com' } });
    await fireEvent.input(passwordInput(), { target: { value: 'password123' } });
    await fireEvent.input(confirmPasswordInput(), { target: { value: 'password123' } });
    await fireEvent.click(registerButton());

    expect(await screen.findByText(errorMessage)).toBeInTheDocument();
    expect(login).not.toHaveBeenCalled();
    expect(goto).not.toHaveBeenCalled();
  });
});
