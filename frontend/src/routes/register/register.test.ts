import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import RegisterPage from './+page.svelte';
import { goto } from '$app/navigation';
import { login } from '$lib/auth';

// Mock the external dependencies
vi.mock('$app/navigation', () => ({
    goto: vi.fn(),
}));

vi.mock('$lib/auth', () => ({
    login: vi.fn(),
}));

describe('Register Page', () => {
    it('should render the registration form', () => {
        render(RegisterPage);
        expect(screen.getByText('Create an account')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Confirm Password')).toBeInTheDocument();
    });

    it('should successfully register, log in, and redirect', async () => {
        const mockUser = { id: 1, username: 'newuser', email: 'new@example.com', is_active: true, role: 'player', character: null };
        const mockResponse = { ...mockUser, access_token: 'new_fake_token' };

        const mockFetch = vi.fn().mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockResponse),
        });
        vi.spyOn(global, 'fetch').mockImplementation(mockFetch);

        const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');

        render(RegisterPage);

        await fireEvent.input(screen.getByPlaceholderText('Username'), { target: { value: 'newuser' } });
        await fireEvent.input(screen.getByPlaceholderText('Email'), { target: { value: 'new@example.com' } });
        await fireEvent.input(screen.getByPlaceholderText('Password'), { target: { value: 'password123' } });
        await fireEvent.input(screen.getByPlaceholderText('Confirm Password'), { target: { value: 'password123' } });
        await fireEvent.click(screen.getByText('Register'));

        // Wait for success message to appear to ensure async operations complete
        await screen.findByText('Registration successful! Logging you in...');

        // 1. Check if fetch was called correctly
        expect(mockFetch).toHaveBeenCalledWith('/api/users/', expect.any(Object));

        // 2. Check if auth state was updated
        expect(login).toHaveBeenCalledWith(mockUser);

        // 3. Check if localStorage was updated
        expect(setItemSpy).toHaveBeenCalledWith('accessToken', 'new_fake_token');

        // 4. Check if user was redirected (might need to advance timers if timeout is long)
        // For now, we assume the test is fast enough or setTimeout is mocked/handled.
        // A more robust way would be to use vi.useFakeTimers()
        await new Promise(r => setTimeout(r, 1600)); // Wait for timeout
        expect(goto).toHaveBeenCalledWith('/dashboard');
    });

    it('should display an error if passwords do not match', async () => {
        render(RegisterPage);

        await fireEvent.input(screen.getByPlaceholderText('Username'), { target: { value: 'testuser' } });
        await fireEvent.input(screen.getByPlaceholderText('Email'), { target: { value: 'test@example.com' } });
        await fireEvent.input(screen.getByPlaceholderText('Password'), { target: { value: 'password123' } });
        await fireEvent.input(screen.getByPlaceholderText('Confirm Password'), { target: { value: 'password456' } });
        await fireEvent.click(screen.getByText('Register'));

        expect(await screen.findByText('Passwords do not match!')).toBeInTheDocument();
    });

    it('should display an error message on failed registration', async () => {
        const mockFetch = vi.fn().mockResolvedValue({
            ok: false,
            json: () => Promise.resolve({ detail: 'Username already in use' }),
        });
        vi.spyOn(global, 'fetch').mockImplementation(mockFetch);

        render(RegisterPage);

        await fireEvent.input(screen.getByPlaceholderText('Username'), { target: { value: 'existinguser' } });
        await fireEvent.input(screen.getByPlaceholderText('Email'), { target: { value: 'new@example.com' } });
        await fireEvent.input(screen.getByPlaceholderText('Password'), { target: { value: 'password123' } });
        await fireEvent.input(screen.getByPlaceholderText('Confirm Password'), { target: { value: 'password123' } });
        await fireEvent.click(screen.getByText('Register'));

        expect(await screen.findByText('Username already in use')).toBeInTheDocument();
    });
});
