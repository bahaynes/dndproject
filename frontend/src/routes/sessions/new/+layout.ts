import { browser } from '$app/environment';
import { auth, initializeAuth } from '$lib/auth';
import { get } from 'svelte/store';
import { redirect } from '@sveltejs/kit';

export const load = async ({ url }) => {
    if (browser) {
        await initializeAuth();
        const { isAuthenticated, user } = get(auth);

        if (!isAuthenticated) {
            const fromUrl = url.pathname + url.search;
            throw redirect(307, `/login?redirectTo=${encodeURIComponent(fromUrl)}`);
        }

        if (user?.role !== 'admin') {
            throw redirect(307, '/sessions?error=unauthorized');
        }
    }
    return {};
};
