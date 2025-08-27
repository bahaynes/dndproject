// src/lib/auth.ts
import { writable, type Writable } from 'svelte/store';

export interface User {
  username: string;
  email?: string;
  // add more fields as needed
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}

export const auth: Writable<AuthState> = writable({
  user: null,
  isAuthenticated: false,
});

export function login(user: User) {
  auth.set({ user, isAuthenticated: true });
}

export function logout() {
  auth.set({ user: null, isAuthenticated: false });
}
