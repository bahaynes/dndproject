import { render, screen } from '@testing-library/svelte';
import { vi } from 'vitest';
import PlayerSessions from './+page.svelte';

// Mock the auth store
vi.mock('$lib/auth', () => {
    const { readable } = require('svelte/store');
    return {
        auth: readable({ user: { role: 'player', character: { id: 1 } }, token: 'fake-token' })
    };
});

// Mock onMount to avoid running fetch on component initialization
vi.mock('svelte', async (importOriginal) => {
    const svelte = await importOriginal();
    return {
        ...svelte,
        onMount: vi.fn(),
    };
});

describe('PlayerSessions Component', () => {
    it('renders the main heading', () => {
        render(PlayerSessions);
        const heading = screen.getByText('Game Sessions');
        expect(heading).toBeTruthy();
    });
});
