import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Define the shape of the user object
export interface User {
    username: string;
    email: string;
    role: string;
    is_active: boolean;
    id: number;
}

// Define the shape of the auth state
export interface AuthState {
    isAuthenticated: boolean;
    user: User | null;
    token: string | null;
}

const initialToken = browser ? window.localStorage.getItem('jwt_token') : null;

const createAuthStore = () => {
    const { subscribe, set, update } = writable<AuthState>({
        isAuthenticated: !!initialToken,
        user: null, // User will be fetched separately
        token: initialToken,
    });

    return {
        subscribe,
        login: (token: string) => {
            if (browser) {
                window.localStorage.setItem('jwt_token', token);
            }
            update(state => ({ ...state, isAuthenticated: true, token }));
        },
        logout: () => {
            if (browser) {
                window.localStorage.removeItem('jwt_token');
            }
            set({ isAuthenticated: false, user: null, token: null });
        },
        setUser: (user: User) => {
            update(state => ({ ...state, user }));
        }
    };
};

export const auth = createAuthStore();
