import { render, screen } from '@testing-library/svelte';
import { vi } from 'vitest';
import { readable } from 'svelte/store';
import PlayerSessions from './+page.svelte';

// Mock the auth store
vi.mock('$lib/auth', () => {
    return {
        auth: readable({ user: { role: 'player', character: { id: 1 } }, token: 'fake-token' })
    };
});

// Mock onMount to avoid running fetch on component initialization
vi.mock('svelte', async () => {
    const svelte: any = await vi.importActual('svelte');
    return {
        ...svelte,
        onMount: vi.fn(),
    };
});

describe('PlayerSessions Component', () => {
    it('renders the main heading', () => {
        render(PlayerSessions);
        const heading = screen.getByRole('heading', { name: 'Session Schedule' });
        expect(heading).toBeTruthy();
    });
});
