import { browser } from '$app/environment';
import { auth, initializeAuth } from '$lib/auth';
import { get } from 'svelte/store';
import { redirect } from '@sveltejs/kit';

export const load = async ({ url }) => {
    if (browser) {
        // Wait for the auth state to be initialized
        await initializeAuth();
        const { isAuthenticated } = get(auth);

        if (!isAuthenticated) {
            // Store the intended destination to redirect after login
            const fromUrl = url.pathname + url.search;
            throw redirect(307, `/login?redirectTo=${encodeURIComponent(fromUrl)}`);
        }
    }
    // For SSR, we don't block. The check will happen on the client.
    return {};
};
