import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { goto } from '$app/navigation';
import { login } from '$lib/auth';
import LoginPage from './+page.svelte';

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$lib/auth', () => ({
	auth: {
		subscribe: (run: (value: { isAuthenticated: boolean }) => void) => {
			run({ isAuthenticated: false });
			return () => {};
		}
	},
	login: vi.fn()
}));

describe('Login Page', () => {
	beforeEach(() => {
		vi.restoreAllMocks();
	});

	it('should render the login button and hide dev login in production', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				ok: true,
				json: async () => ({ dev_login_enabled: false })
			})
		);

		render(LoginPage);
		expect(screen.getByText('Login with Discord')).toBeInTheDocument();
		expect(screen.getByRole('heading', { name: /The Board/i })).toBeInTheDocument();
		await waitFor(() => {
			expect(screen.queryByRole('button', { name: 'Dev Player' })).not.toBeInTheDocument();
		});
	});

	it('should log in via dev-token when dev-status is enabled without Discord OAuth', async () => {
		const mockUser = {
			id: 1,
			username: 'Dev Player',
			role: 'player',
			campaign: { id: 1, name: 'E2E Test Campaign' }
		};
		const fetchMock = vi.fn().mockImplementation((url: string) => {
			if (url.endsWith('/auth/dev-status')) {
				return Promise.resolve({
					ok: true,
					json: async () => ({ dev_login_enabled: true })
				});
			}
			if (url.endsWith('/auth/dev-token')) {
				return Promise.resolve({
					ok: true,
					json: async () => ({ access_token: 'dev-jwt-123', token_type: 'bearer', campaign_id: 1 })
				});
			}
			if (url.endsWith('/auth/me')) {
				return Promise.resolve({
					ok: true,
					json: async () => mockUser
				});
			}
			return Promise.reject(new Error(`Unexpected fetch: ${url}`));
		});
		vi.stubGlobal('fetch', fetchMock);

		render(LoginPage);
		const devPlayerBtn = await waitFor(() => screen.getByRole('button', { name: 'Dev Player' }));
		await fireEvent.click(devPlayerBtn);

		await waitFor(() => {
			expect(login).toHaveBeenCalledWith(mockUser, 'dev-jwt-123', mockUser.campaign);
			expect(goto).toHaveBeenCalledWith('/dashboard');
		});
	});
});
