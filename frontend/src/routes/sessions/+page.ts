import { authedFetch } from '$lib/auth';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
    try {
        const response = await authedFetch('/api/sessions/', { fetch });
        if (response.ok) {
            const sessions = await response.json();
            return { sessions };
        } else {
            return { sessions: [], error: 'Failed to load game sessions.' };
        }
    } catch (error) {
        return { sessions: [], error: 'An error occurred while fetching game sessions.' };
    }
};
