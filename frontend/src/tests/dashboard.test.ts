import { render, screen, waitFor } from '@testing-library/svelte';
import Dashboard from '../routes/dashboard/+page.svelte';
import { describe, beforeEach, test, expect, vi } from 'vitest';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));

const mockShip = {
    id: 1, campaign_id: 1, name: 'The Meridian', level: 2, essence: 30,
    motd: 'Stay sharp.', status: 'nominal', long_rest_cost: 4,
    next_threshold: 50, essence_to_next_level: 20, created_at: '2026-01-01T00:00:00Z',
};

const mockSession = {
    id: 1, name: 'Into the Substrata', description: 'Deep run.',
    session_date: new Date(Date.now() + 86400000 * 3).toISOString(),
    status: 'Open', min_players: 4, max_players: 6, players: [],
    proposals: [{
        id: 10, session_id: 1, mission_id: 5, proposed_by_id: 2,
        status: 'proposed',
        mission: { id: 5, name: 'The Bone Market', tier: 'Tier 1', region: 'Substrata', description: null,
            status: 'active', cooldown_days: 7, is_retired: false, is_discoverable: true,
            last_run_date: null, rewards: [], players: [] },
        backers: [{ id: 2, name: 'Vesper', description: null, image_url: null, owner_id: 99 }],
    }],
};

const mockMissions = [
    { id: 5, name: 'The Bone Market', tier: 'Tier 1', region: 'Substrata', description: 'A grim place.',
      status: 'active', cooldown_days: 7, is_retired: false, is_discoverable: true,
      last_run_date: null, rewards: [], players: [] },
    { id: 6, name: 'The Pale Gate', tier: 'Tier 2', region: 'Cathedral', description: null,
      status: 'active', cooldown_days: 14, is_retired: false, is_discoverable: true,
      last_run_date: null, rewards: [], players: [] },
];

vi.mock('$lib/api', () => ({
    api: vi.fn((_method: string, path: string) => {
        if (path.startsWith('/ship')) return Promise.resolve(mockShip);
        if (path.startsWith('/sessions')) return Promise.resolve([mockSession]);
        if (path.startsWith('/missions')) return Promise.resolve(mockMissions);
        return Promise.resolve(null);
    }),
}));

vi.mock('$lib/auth', () => ({
    auth: {
        subscribe: (fn: any) => {
            fn({
                isAuthenticated: true,
                token: 'test-token',
                user: {
                    id: 1, username: 'testplayer', discord_id: '123', email: 'test@test.com',
                    role: 'player', is_active: true,
                    active_character: {
                        id: 7, name: 'Cassia Vell', class_name: 'Rogue', level: 3,
                        status: 'Active', missions_completed: 5, owner_id: 1,
                        stats: { id: 1, character_id: 7, xp: 0, scrip: 10 },
                        inventory: [], missions: [], game_sessions: [],
                    },
                    characters: [],
                },
                campaign: { id: 1, name: 'The Inheritors' },
            });
            return () => {};
        },
    },
}));

describe('Dashboard', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        Object.defineProperty(window, 'localStorage', {
            value: { getItem: vi.fn(() => 'token'), setItem: vi.fn(), removeItem: vi.fn(), clear: vi.fn() },
            writable: true,
        });
    });

    test('shows character identity banner with name, class, and level', async () => {
        render(Dashboard);
        await waitFor(() => expect(screen.getByText('Cassia Vell')).toBeInTheDocument());
        expect(screen.getByText(/Rogue/)).toBeInTheDocument();
        expect(screen.getByText(/Level 3/)).toBeInTheDocument();
    });

    test('shows Mission Board section heading', async () => {
        render(Dashboard);
        await waitFor(() => expect(screen.getByText('Mission Board')).toBeInTheDocument());
    });

    test('shows upcoming session with its proposal', async () => {
        render(Dashboard);
        await waitFor(() => expect(screen.getByText('Into the Substrata')).toBeInTheDocument());
        // 'The Bone Market' appears in the proposal list and the missions section
        expect(screen.getAllByText('The Bone Market').length).toBeGreaterThanOrEqual(1);
    });

    test('shows available contracts section', async () => {
        render(Dashboard);
        await waitFor(() => expect(screen.getByText('Available Contracts')).toBeInTheDocument());
        expect(screen.getByText('The Pale Gate')).toBeInTheDocument();
    });

    test('shows ship name in ship compact panel', async () => {
        render(Dashboard);
        await waitFor(() => expect(screen.getByText('🚀 The Meridian')).toBeInTheDocument());
    });
});
