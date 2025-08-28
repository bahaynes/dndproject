import { render, screen } from '@testing-library/svelte';
import Layout from '../routes/+layout.svelte';
import { auth } from '$lib/auth';
import { beforeEach, test, expect } from 'vitest';

beforeEach(() => {
  // Replace the value of the existing auth store
  auth.set({
    isAuthenticated: true,
    user: { username: 'testuser' },
    token: 'fake-token'
  });
});

test('renders Logout button and welcome text when authenticated', async () => {
  render(Layout);

  // Dashboard link
  expect(screen.getByText('Dashboard')).toBeInTheDocument();

  // Welcome text
  expect(screen.getByText('Welcome, testuser')).toBeInTheDocument();

  // Logout button
  expect(screen.getByText('Logout')).toBeInTheDocument();
});

