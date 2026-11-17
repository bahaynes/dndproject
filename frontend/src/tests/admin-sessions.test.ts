import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import AdminSessionsPage from '../routes/admin/sessions/+page.svelte';
import { api } from '../lib/api';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

vi.mock('$lib/api', () => ({
	api: vi.fn()
}));

vi.mock('$lib/auth', () => ({
	auth: {
		subscribe: (fn: (v: unknown) => void) => {
			fn({
				isAuthenticated: true,
				token: 'tok',
				user: { id: 1, username: 'dm', role: 'admin' },
				campaign: { id: 1, name: 'Test' }
			});
			return () => {};
		}
	}
}));

const sessionWithHexAndMission = {
	id: 3,
	name: 'Friday Run',
	session_date: new Date().toISOString(),
	status: 'Scheduled',
	min_players: 3,
	max_players: 5,
	players: [{ id: 7, name: 'Cassia', owner_id: 2 }],
	proposals: [
		{
			id: 20,
			session_id: 3,
			hex_id: 4,
			proposed_by_id: 2,
			status: 'proposed',
			hex: { id: 4, q: 1, r: -2, terrain: 'hills' },
			backers: []
		},
		{
			id: 21,
			session_id: 3,
			mission_id: 9,
			proposed_by_id: 2,
			status: 'proposed',
			mission: { id: 9, name: 'Iron Keep', status: 'Available', cooldown_days: 7, is_retired: false, is_discoverable: true, rewards: [{ id: 1, gold: 100, xp: 450, is_hidden: false }], players: [] },
			backers: [{ id: 7, name: 'Cassia', owner_id: 2 }]
		}
	]
};

describe('Admin Sessions Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		Object.defineProperty(window, 'localStorage', {
			value: { getItem: vi.fn(() => 'tok'), setItem: vi.fn(), removeItem: vi.fn(), clear: vi.fn() },
			writable: true
		});
		vi.mocked(api).mockImplementation((_m: string, path: string) => {
			if (path === '/sessions/') return Promise.resolve([sessionWithHexAndMission]);
			if (path === '/missions/')
				return Promise.resolve([
					{ id: 9, name: 'Iron Keep', status: 'Available', cooldown_days: 7, is_retired: false, is_discoverable: true, rewards: [{ id: 1, gold: 100, xp: 450, is_hidden: false }], players: [] }
				]);
			if (path === '/maps/') return Promise.resolve([]);
			return Promise.resolve({});
		});
	});

	test('renders hex proposals and defaults Complete Session to top-voted quest', async () => {
		render(AdminSessionsPage);
		await waitFor(() => expect(screen.getByText('Explore Hex (1, -2)')).toBeInTheDocument());

		await fireEvent.click(screen.getByText('Complete & Award Rewards'));
		await waitFor(() => expect(screen.getByText('Finalize & Award')).toBeInTheDocument());

		await fireEvent.click(screen.getByText('Finalize & Award'));
		await waitFor(() =>
			expect(api).toHaveBeenCalledWith(
				'POST',
				'/sessions/3/complete',
				expect.objectContaining({
					result: 'success',
					mission_id: 9,
					gold_earned: 100,
					xp_earned: 450
				})
			)
		);
	});
});
