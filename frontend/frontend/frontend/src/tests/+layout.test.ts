import { render, screen } from '@testing-library/svelte';
import Layout from '../routes/+layout.svelte';
import { auth } from '../lib/auth';
import { writable } from 'svelte/store';

describe('+layout.svelte', () => {
	it('renders a logout button when authenticated', () => {
		// Mock the auth store
		const mockAuth = {
			...auth,
			...writable({ isAuthenticated: true, user: { username: 'testuser' } })
		};

		render(Layout, { props: { auth: mockAuth } });

		const logoutButton = screen.getByText('Logout');
		expect(logoutButton).toBeInTheDocument();
	});
});
