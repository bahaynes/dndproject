import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import SessionCard from '../lib/components/SessionCard.svelte';
import { api } from '../lib/api';

vi.mock('../lib/api', () => ({
	api: vi.fn(() => Promise.resolve({}))
}));

const baseSession = {
	id: 1,
	name: 'Thursday Table',
	description: 'Open exploration',
	session_date: new Date(Date.now() + 86400000).toISOString(),
	status: 'Scheduled',
	min_players: 3,
	max_players: 5,
	players: [],
	proposals: [
		{
			id: 10,
			session_id: 1,
			mission_id: 5,
			proposed_by_id: 2,
			status: 'proposed' as const,
			mission: {
				id: 5,
				name: 'Sunken Vault',
				tier: 'Tier 1',
				status: 'Available',
				cooldown_days: 7,
				is_retired: false,
				is_discoverable: true,
				rewards: [],
				players: []
			},
			backers: []
		},
		{
			id: 11,
			session_id: 1,
			hex_id: 8,
			proposed_by_id: 2,
			status: 'proposed' as const,
			hex: { id: 8, q: 2, r: -1, terrain: 'forest', linked_location_name: 'Old Watchtower' },
			backers: []
		}
	]
};

describe('SessionCard', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	test('unseated player sees I\'m Playing button and can claim a seat', async () => {
		const onRefresh = vi.fn();
		render(SessionCard, {
			props: { session: baseSession, userId: 1, activeCharacterId: 7, myCharacters: [], onRefresh }
		});

		const btn = screen.getByText("I'm Playing (0/5)");
		await fireEvent.click(btn);
		await waitFor(() => expect(api).toHaveBeenCalledWith('POST', '/sessions/1/signup'));
		expect(onRefresh).toHaveBeenCalled();
	});

	test('seated player with multiple active characters can swap character and vote', async () => {
		const seatedSession = {
			...baseSession,
			players: [{ id: 7, name: 'Cassia', class_name: 'Rogue', level: 3, owner_id: 1 }]
		};
		const myCharacters = [
			{ id: 7, name: 'Cassia', class_name: 'Rogue', level: 3, status: 'Active' as const, owner_id: 1, missions_completed: 0, stats: { id: 1, character_id: 7, gold: 0, xp: 0 }, inventory: [], missions: [], game_sessions: [] },
			{ id: 8, name: 'Bram', class_name: 'Wizard', level: 3, status: 'Active' as const, owner_id: 1, missions_completed: 0, stats: { id: 2, character_id: 8, gold: 0, xp: 0 }, inventory: [], missions: [], game_sessions: [] }
		];

		render(SessionCard, {
			props: { session: seatedSession, userId: 1, activeCharacterId: 7, myCharacters }
		});

		expect(screen.getByText('Explore Hex (2, -1) — Old Watchtower')).toBeInTheDocument();
		expect(screen.getAllByText('Vote')).toHaveLength(2);

		const select = screen.getByLabelText('Swap character for this session') as HTMLSelectElement;
		await fireEvent.change(select, { target: { value: '8' } });
		await waitFor(() =>
			expect(api).toHaveBeenCalledWith('POST', '/sessions/1/swap-character', { character_id: 8 })
		);
	});
});
