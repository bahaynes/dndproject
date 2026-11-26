import { render, screen, waitFor } from '@testing-library/svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import AdminMissionsPage from '../routes/admin/missions/+page.svelte';
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

const draftedByMcp = {
	id: 12,
	name: 'Into the Barrow',
	status: 'Available',
	cooldown_days: 7,
	is_retired: false,
	is_discoverable: false,
	foundry_module: 'oneshot-into-the-barrow',
	rewards: [],
	players: []
};

describe('Admin Missions Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
		Object.defineProperty(window, 'localStorage', {
			value: { getItem: vi.fn(() => 'tok'), setItem: vi.fn(), removeItem: vi.fn(), clear: vi.fn() },
			writable: true
		});
		vi.mocked(api).mockImplementation((_m: string, path: string) => {
			if (path === '/missions/?include_hidden=true') return Promise.resolve([draftedByMcp]);
			if (path === '/items/') return Promise.resolve([]);
			if (path === '/maps/') return Promise.resolve([]);
			return Promise.resolve([]);
		});
	});

	test('lists hidden missions with their Foundry module', async () => {
		render(AdminMissionsPage);
		await waitFor(() => expect(screen.getByText('Into the Barrow')).toBeInTheDocument());
		expect(screen.getByText('Hidden')).toBeInTheDocument();
		expect(screen.getByText('Foundry: oneshot-into-the-barrow')).toBeInTheDocument();
		expect(api).toHaveBeenCalledWith('GET', '/missions/?include_hidden=true');
	});
});
