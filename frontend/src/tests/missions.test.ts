import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import MissionsPage from '../routes/missions/+page.svelte';
import { api } from '../lib/api';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));
vi.mock('$app/stores', () => ({
	page: {
		subscribe: (fn: (v: unknown) => void) => {
			fn({ url: { pathname: '/missions' } });
			return () => {};
		}
	}
}));

vi.mock('$lib/api', () => ({
	api: vi.fn()
}));

vi.mock('$lib/auth', () => ({
	auth: {
		subscribe: (fn: (v: unknown) => void) => {
			fn({
				isAuthenticated: true,
				token: 'tok',
				user: { id: 1, username: 'p1', active_character: { id: 7, name: 'Cassia' } },
				campaign: { id: 1, name: 'Test' }
			});
			return () => {};
		}
	}
}));

const sampleMission = {
	id: 5,
	name: 'Crypt of Ash',
	tier: 'Tier 1',
	status: 'Available',
	cooldown_days: 7,
	is_retired: false,
	is_discoverable: true,
	rewards: [{ id: 1, gold: 50, xp: 300, is_hidden: false }],
	players: []
};

describe('Missions Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	test('guides unseated player to join a session before proposing', async () => {
		vi.mocked(api).mockImplementation((_m: string, path: string) => {
			if (path === '/missions/') return Promise.resolve([sampleMission]);
			if (path === '/sessions/') return Promise.resolve([{ id: 1, status: 'Scheduled', players: [] }]);
			return Promise.resolve([]);
		});

		render(MissionsPage);
		await waitFor(() => expect(screen.getByText('Crypt of Ash')).toBeInTheDocument());
		expect(screen.getByText('Join a Session to Propose →')).toBeInTheDocument();
	});

	test('shows Propose for Session when player is seated', async () => {
		vi.mocked(api).mockImplementation((_m: string, path: string) => {
			if (path === '/missions/') return Promise.resolve([sampleMission]);
			if (path === '/sessions/')
				return Promise.resolve([{ id: 1, name: 'Thu', session_date: new Date().toISOString(), status: 'Scheduled', players: [{ id: 7, owner_id: 1, name: 'Cassia' }] }]);
			return Promise.resolve([]);
		});

		render(MissionsPage);
		await waitFor(() => expect(screen.getByText('Propose for Session')).toBeInTheDocument());
	});
});
