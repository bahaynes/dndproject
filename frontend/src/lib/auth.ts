// src/lib/auth.ts
import { writable, type Writable } from 'svelte/store';

// --- Character Related Interfaces ---
export interface Item {
    id: number;
    name: string;
    description: string | null;
}

export interface InventoryItem {
    id: number;
    quantity: number;
    item: Item;
}

export interface CharacterStats {
    id: number;
    xp: number;
    scrip: number;
}

export interface Character {
    id: number;
    name: string;
    description: string | null;
    image_url: string | null;
    owner_id: number;
    stats: CharacterStats;
    inventory: InventoryItem[];
}

// --- User and Auth Interfaces ---
export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  character: Character | null;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;
}

export const auth: Writable<AuthState> = writable({
  user: null,
  isAuthenticated: false,
  token: null,
});

export function login(user: User, token: string) {
  auth.set({ user, isAuthenticated: true, token });
  localStorage.setItem('token', token);
  localStorage.setItem('user', JSON.stringify(user));
}

export function logout() {
  auth.set({ user: null, isAuthenticated: false, token: null });
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

// Function to check for persisted auth state
export function initializeAuth() {
    if (typeof window !== 'undefined') {
        const token = localStorage.getItem('token');
        const userJson = localStorage.getItem('user');
        if (token && userJson) {
            try {
                const user = JSON.parse(userJson);
                auth.set({ user, isAuthenticated: true, token });
            } catch (e) {
                console.error("Failed to parse user from localStorage", e);
                logout(); // Clear corrupted data
            }
        }
    }
}
