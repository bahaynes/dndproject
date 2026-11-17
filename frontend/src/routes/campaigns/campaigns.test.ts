import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
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
		vi.restoreAllMocks();
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
});
