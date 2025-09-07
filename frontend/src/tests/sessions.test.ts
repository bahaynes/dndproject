import { render, screen, fireEvent } from '@testing-library/svelte';
import SessionsPage from '../routes/sessions/+page.svelte';
import NewSessionPage from '../routes/sessions/new/+page.svelte';
import EditSessionPage from '../routes/sessions/[id]/edit/+page.svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { writable } from 'svelte/store';
import { auth, authedFetch } from '$lib/auth';
import { goto, invalidateAll } from '$app/navigation';

// Mocks
vi.mock('$app/navigation', () => ({
    goto: vi.fn(),
    invalidateAll: vi.fn(),
}));

vi.mock('$lib/auth', async (importOriginal) => {
    const { writable } = await import('svelte/store');
    const mockAuthStore = writable({
        user: null,
        token: null,
        isAuthenticated: false,
    });

    return {
        ...(await importOriginal() as any),
        auth: mockAuthStore,
        authedFetch: vi.fn(),
    };
});

const mockSessions = [
    { id: 1, name: 'Session 1', description: 'A test session', session_date: new Date().toISOString(), status: 'Scheduled', players: [] },
    { id: 2, name: 'Session 2', description: 'Another test session', session_date: new Date().toISOString(), status: 'Completed', players: [{id: 1, name: 'Player 1'}] },
];

describe('Game Session Management', () => {
    let authStore;

    beforeEach(async () => {
        vi.clearAllMocks();
        authStore = (await import('$lib/auth')).auth;
    });

    describe('Sessions List Page', () => {
        test('renders the sessions list', async () => {
            render(SessionsPage, { data: { sessions: mockSessions } });
            expect(screen.getByText('Session 1')).toBeInTheDocument();
            expect(screen.getByText('Session 2')).toBeInTheDocument();
        });

        test('shows New Session button for admins', () => {
            authStore.set({ user: { role: 'admin' }, isAuthenticated: true });
            render(SessionsPage, { data: { sessions: mockSessions } });
            expect(screen.getByText('New Session')).toBeInTheDocument();
        });

        test('hides New Session button for players', () => {
            authStore.set({ user: { role: 'player', character: {id: 1} }, isAuthenticated: true });
            render(SessionsPage, { data: { sessions: mockSessions } });
            expect(screen.queryByText('New Session')).not.toBeInTheDocument();
        });

        test('player can sign up for a session', async () => {
            authStore.set({ user: { role: 'player', character: {id: 2} }, isAuthenticated: true });
            render(SessionsPage, { data: { sessions: mockSessions } });

            const signUpButton = screen.getByText('Sign Up');
            (authedFetch as any).mockResolvedValue({ ok: true });

            await fireEvent.click(signUpButton);

            expect(authedFetch).toHaveBeenCalledWith('/api/sessions/1/signup', { method: 'POST' });
            expect(invalidateAll).toHaveBeenCalled();
        });
    });

    describe('New Session Page', () => {
        test('can create a new session', async () => {
            render(NewSessionPage);

            await fireEvent.input(screen.getByLabelText('Session Name'), {target: {value: 'New Quest'}});
            await fireEvent.input(screen.getByLabelText('Description'), {target: {value: 'A brand new adventure'}});
            await fireEvent.input(screen.getByLabelText('Session Date and Time'), {target: {value: '2025-10-10T10:00'}});

            (authedFetch as any).mockResolvedValue({ ok: true });

            await fireEvent.click(screen.getByText('Create Session'));

            expect(authedFetch).toHaveBeenCalledWith('/api/sessions/', expect.any(Object));
            expect(goto).toHaveBeenCalledWith('/sessions');
        });
    });

    describe('Edit Session Page', () => {
        test('can edit a session', async () => {
            const sessionToEdit = mockSessions[0];
            render(EditSessionPage, { data: { session: sessionToEdit } });

            await fireEvent.input(screen.getByLabelText('Session Name'), {target: {value: 'Updated Quest Name'}});

            (authedFetch as any).mockResolvedValue({ ok: true });

            await fireEvent.click(screen.getByText('Save Changes'));

            expect(authedFetch).toHaveBeenCalledWith(`/api/sessions/${sessionToEdit.id}`, expect.any(Object));
            expect(goto).toHaveBeenCalledWith('/sessions');
        });
    });
});
