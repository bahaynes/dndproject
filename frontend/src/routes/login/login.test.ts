import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi } from 'vitest';
import LoginPage from './+page.svelte';

// Mock the external dependencies
vi.mock('$app/navigation', () => ({
    goto: vi.fn(),
}));

vi.mock('$lib/auth', () => ({
    auth: { subscribe: (run: any) => { run({ isAuthenticated: false }); return () => { }; } },
    login: vi.fn(),
}));

describe('Login Page', () => {
    it('should render the login button', () => {
        render(LoginPage);
        expect(screen.getByText('Login with Discord')).toBeInTheDocument();
        expect(screen.getByText('Login to DnD Westmarches')).toBeInTheDocument();
    });
});
