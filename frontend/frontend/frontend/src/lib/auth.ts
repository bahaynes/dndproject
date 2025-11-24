import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export interface User {
	id: number;
	username: string;
	email: string;
}

export interface AuthState {
	isAuthenticated: boolean;
	user: User | null;
	token: string | null;
}

function createAuth() {
	const { subscribe, set, update } = writable<AuthState>({
		isAuthenticated: false,
		user: null,
		token: null
	});

	return {
		subscribe,
		login: (token: string) => {
			if (browser) {
				localStorage.setItem('token', token);
			}
			update((state) => ({ ...state, isAuthenticated: true, token }));
		},
		logout: () => {
			if (browser) {
				localStorage.removeItem('token');
			}
			set({ isAuthenticated: false, user: null, token: null });
		},
		setUser: (user: User) => {
			update((state) => ({ ...state, user }));
		}
	};
}

export const auth = createAuth();
