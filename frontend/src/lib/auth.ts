import { writable } from 'svelte/store';
import { browser } from '$app/environment';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  avatar_url?: string;
  discord_id: string;
  campaign_id: number;
}

interface Campaign {
  id: number;
  name: string;
  discord_guild_id: string;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  campaign: Campaign | null; // Currently selected campaign
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
      update(state => ({
        ...state,
        isAuthenticated: true,
        user,
        token,
        campaign: campaign || state.campaign
      }));
    },
    logout: () => {
      if (browser) {
        localStorage.removeItem('accessToken');
      }
      set(initialState);
    },
    setCampaign: (campaign: Campaign) => {
      update(state => ({ ...state, campaign }));
    }
  };
}

export const auth = createAuthStore();
export const login = auth.login;
export const logout = auth.logout;
