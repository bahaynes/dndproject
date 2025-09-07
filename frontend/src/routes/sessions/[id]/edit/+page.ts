import { authedFetch } from '$lib/auth';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, params }) => {
    try {
        const response = await authedFetch(`/api/sessions/${params.id}`, { fetch });
        if (response.ok) {
            const session = await response.json();
            return { session };
        } else {
            const errorData = await response.json();
            return { session: null, error: errorData.detail || 'Failed to load session.' };
        }
    } catch (error) {
        return { session: null, error: 'An error occurred while fetching the session.' };
    }
};
