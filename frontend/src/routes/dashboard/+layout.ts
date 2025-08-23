import { browser } from '$app/environment';
import { auth } from '$lib/stores/auth';
import { goto } from '$app/navigation';
import { get } from 'svelte/store';

export const load = async () => {
    if (browser) {
        const authState = get(auth);
        if (!authState.isAuthenticated) {
            await goto('/login');
        }
    }
    return {};
};
