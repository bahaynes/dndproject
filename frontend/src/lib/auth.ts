import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { User } from './types';

// ---------------------------------------------------------------------------
// Auth is intentionally simple. There is ONE token: accessToken.
// It is always campaign-scoped (has both discord_id and campaign_id).
//
// Flow:
//   1. Discord OAuth → backend issues a temporary "pending" token
//   2. /login/callback stores it as pendingToken, redirects to /campaigns
//   3. /campaigns lets the user pick a campaign, exchanges for accessToken
//   4. All other pages just read accessToken via this store
//
// DO NOT add more token types or auth states here.
// ---------------------------------------------------------------------------

interface Campaign {
	id: number;
	name: string;
	discord_guild_id: string;
}

interface AuthState {
	isAuthenticated: boolean;
	user: User | null;
	campaign: Campaign | null;
	token: string | null;
}

const initialState: AuthState = {
	isAuthenticated: false,
	user: null,
	campaign: null,
	token: null
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,
		login: (user: User, token: string, campaign?: Campaign) => {
			if (browser) {
				localStorage.setItem('accessToken', token);
			}
			update((state) => ({
				...state,
				isAuthenticated: true,
				user,
				token,
				campaign: campaign ?? state.campaign
			}));
		},
		logout: () => {
			if (browser) {
				localStorage.removeItem('accessToken');
				localStorage.removeItem('pendingToken');
				localStorage.removeItem('pendingDiscordToken');
			}
			set(initialState);
		}
	};
}

export const auth = createAuthStore();
export const login = auth.login;
export const logout = auth.logout;
