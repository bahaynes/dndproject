import { render, screen } from '@testing-library/svelte';
import { vi } from 'vitest';
import AdminSessions from './+page.svelte';

// Mock the auth store
vi.mock('$lib/auth', () => {
    const { readable } = require('svelte/store');
    return {
        auth: readable({ user: { role: 'admin' }, token: 'fake-token' })
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

describe('AdminSessions Component', () => {
    it('renders the main heading', () => {
        render(AdminSessions);
        const heading = screen.getByText('Admin: Manage Game Sessions');
        expect(heading).toBeTruthy();
    });
});
