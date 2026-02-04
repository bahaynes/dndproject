import { browser } from '$app/environment';
import { auth } from '$lib/auth';
import { get } from 'svelte/store';
import { redirect } from '@sveltejs/kit';

export const load = async () => {
    // We only run this check on the client-side, because our auth store is client-side only.
    // A more robust implementation would handle this on the server with cookies.
    if (browser) {
        const { isAuthenticated } = get(auth);
        const hasToken = localStorage.getItem('accessToken');

        if (!isAuthenticated && !hasToken) {
            throw redirect(307, '/login');
        }
    }
    // For SSR, we'll let it render and the client-side redirect will catch it.
    // This avoids issues with trying to access localStorage on the server.
    return {};
};
