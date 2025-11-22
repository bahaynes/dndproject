// Central auth store holding user profile and bearer token
import { writable, type Writable } from 'svelte/store';
import type { User } from '$lib/types';

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
};

export const auth: Writable<AuthState> = writable(initialState);

export function setAuth(user: User, token: string) {
  auth.set({
    user,
    token,
    isAuthenticated: true,
  });
}

export function clearAuth() {
  auth.set(initialState);
}
