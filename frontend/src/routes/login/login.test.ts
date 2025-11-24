import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import LoginPage from './+page.svelte';
import { goto } from '$app/navigation';
import { login } from '$lib/auth';

// Mock the external dependencies
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$lib/auth', () => ({
	login: vi.fn()
}));

describe('Login Page', () => {
	it('should render the login form', () => {
		render(LoginPage);
		expect(screen.getByText('Login to your account')).toBeInTheDocument();
		expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
		expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
	});

	it('should successfully log in and redirect on valid credentials', async () => {
		// Mock the fetch function
		const mockFetch = vi
			.fn()
			.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({ access_token: 'fake_token' })
			})
			.mockResolvedValueOnce({
				ok: true,
				json: () => Promise.resolve({ username: 'testuser', email: 'test@example.com' })
			});
		vi.spyOn(global, 'fetch').mockImplementation(mockFetch);

		// Mock localStorage
		const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');

		render(LoginPage);

		const usernameInput = screen.getByPlaceholderText('Username');
		const passwordInput = screen.getByPlaceholderText('Password');
		const loginButton = screen.getByText('Login');

		await fireEvent.input(usernameInput, { target: { value: 'testuser' } });
		await fireEvent.input(passwordInput, { target: { value: 'password' } });
		await fireEvent.click(loginButton);

		// Wait for the async operations to complete
		await screen.findByText('Login'); // This is a bit of a hack to wait

		// 1. Check if fetch was called correctly for the token
		expect(mockFetch).toHaveBeenCalledWith('/api/token', expect.any(Object));

		// 2. Check if fetch was called correctly for the user details
		expect(mockFetch).toHaveBeenCalledWith('/api/users/me/', {
			headers: { Authorization: 'Bearer fake_token' }
		});

		// 3. Check if localStorage was updated
		expect(setItemSpy).toHaveBeenCalledWith('accessToken', 'fake_token');

		// 4. Check if the auth state was updated
		expect(login).toHaveBeenCalledWith(
			{ username: 'testuser', email: 'test@example.com' },
			'fake_token'
		);

		// 5. Check if the user was redirected
		expect(goto).toHaveBeenCalledWith('/dashboard');
	});

	it('should display an error message on failed login', async () => {
		const mockFetch = vi.fn().mockResolvedValue({
			ok: false,
			json: () => Promise.resolve({ detail: 'Incorrect username or password' })
		});
		vi.spyOn(global, 'fetch').mockImplementation(mockFetch);

		render(LoginPage);

		const usernameInput = screen.getByPlaceholderText('Username');
		const passwordInput = screen.getByPlaceholderText('Password');
		const loginButton = screen.getByText('Login');

		await fireEvent.input(usernameInput, { target: { value: 'testuser' } });
		await fireEvent.input(passwordInput, { target: { value: 'wrongpassword' } });
		await fireEvent.click(loginButton);

		const errorMessage = await screen.findByText('Incorrect username or password');
		expect(errorMessage).toBeInTheDocument();
	});
});
