import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { goto } from '$app/navigation';
import CampaignsPage from './+page.svelte';

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$lib/auth', () => ({
	auth: {
		subscribe: (run: (value: { isAuthenticated: boolean; token: string | null }) => void) => {
			run({ isAuthenticated: true, token: 'test-token' });
			return () => {};
		}
	},
	login: vi.fn()
}));

describe('Campaigns Page', () => {
	beforeEach(() => {
		localStorage.clear();
		vi.clearAllMocks();
	});

	it('shows a resting border on campaign buttons and highlights the border when clicked', async () => {
		const fetchMock = vi.fn().mockImplementation((url: string) => {
			if (url.endsWith('/campaigns/mine')) {
				return Promise.resolve({
					ok: true,
					json: async () => [{ id: 1, name: 'Novacats' }]
				});
			}
			// Keep /campaigns/login pending so we can assert the clicked state
			return new Promise(() => {});
		});
		vi.stubGlobal('fetch', fetchMock);

		render(CampaignsPage);

		const button = await waitFor(() => screen.getByRole('button', { name: /Novacats/i }));
		expect(button).toHaveClass('border');
		expect(button).toHaveClass('border-base-content/15');
		expect(button).toHaveAttribute('aria-pressed', 'false');

		await fireEvent.click(button);

		expect(button).toHaveAttribute('aria-pressed', 'true');
		expect(button).toHaveClass('border-primary');
		expect(button).toHaveClass('ring-2');
		expect(button).toHaveClass('ring-primary/40');
	});

	it('replaces history state when navigating to dashboard after selecting a campaign', async () => {
		const fetchMock = vi.fn().mockImplementation((url: string) => {
			if (url.endsWith('/campaigns/mine')) {
				return Promise.resolve({
					ok: true,
					json: async () => [{ id: 1, name: 'Novacats' }]
				});
			}
			if (url.endsWith('/campaigns/login')) {
				return Promise.resolve({
					ok: true,
					json: async () => ({ access_token: 'campaign-token' })
				});
			}
			if (url.endsWith('/auth/me')) {
				return Promise.resolve({
					ok: true,
					json: async () => ({ id: 1, username: 'Player', campaign: { id: 1, name: 'Novacats' } })
				});
			}
			return Promise.resolve({ ok: false });
		});
		vi.stubGlobal('fetch', fetchMock);

		render(CampaignsPage);

		const button = await waitFor(() => screen.getByRole('button', { name: /Novacats/i }));
		await fireEvent.click(button);

		await waitFor(() => {
			expect(goto).toHaveBeenCalledWith('/dashboard', { replaceState: true });
		});
	});

	it('renders the Discord bot invite link when available', async () => {
		const fetchMock = vi.fn().mockImplementation((url: string) => {
			if (url.endsWith('/campaigns/mine')) {
				return Promise.resolve({
					ok: true,
					json: async () => []
				});
			}
			if (url.endsWith('/campaigns/bot-invite-url')) {
				return Promise.resolve({
					ok: true,
					json: async () => ({
						url: 'https://discord.com/oauth2/authorize?client_id=999&scope=bot&permissions=0'
					})
				});
			}
			return Promise.resolve({ ok: false });
		});
		vi.stubGlobal('fetch', fetchMock);

		render(CampaignsPage);

		const inviteLink = await waitFor(() =>
			screen.getByRole('link', { name: /Invite Bot to Discord/i })
		);
		expect(inviteLink).toHaveAttribute(
			'href',
			'https://discord.com/oauth2/authorize?client_id=999&scope=bot&permissions=0'
		);
		expect(screen.getByText(/Not seeing your server here\?/i)).toBeInTheDocument();
	});
});
