// src/lib/auth.ts
import { writable, type Writable } from 'svelte/store';
import type { User } from './types';
export type { User };

export interface AuthState {
	user: User | null;
	isAuthenticated: boolean;
	token?: string;
}

export const auth: Writable<AuthState> = writable({
	user: null,
	isAuthenticated: false,
	token: undefined
});

export function login(user: User, token?: string) {
	auth.set({ user, isAuthenticated: true, token });
}

export function logout() {
	auth.set({ user: null, isAuthenticated: false, token: undefined });
}
