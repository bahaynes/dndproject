import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { User, GlobalUser } from './types';


interface Campaign {
  id: number;
  name: string;
  discord_guild_id: string;
}

interface AuthState {
  isAuthenticated: boolean;
  isGlobalAuthenticated: boolean;
  user: User | null;
  globalUser: GlobalUser | null;
  campaign: Campaign | null; // Currently selected campaign
  token: string | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  isGlobalAuthenticated: false,
  user: null,
  globalUser: null,
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
        isGlobalAuthenticated: true,
        user,
        globalUser: { username: user.username, discord_id: user.discord_id, avatar_url: user.avatar_url },
        token,
        campaign: campaign || state.campaign
      }));
    },
    globalLogin: (user: GlobalUser, token: string) => {
      // We assume token is already in storage if needed, or we set it here.
      // Usually handled by callback page but good to sync.
      if (browser) {
        // If checking persistence, we might not want to overwrite if token is same
      }
      update(state => ({
        ...state,
        isGlobalAuthenticated: true,
        isAuthenticated: false, // Explicitly false since not campaign-authed
        globalUser: user,
        user: null,
        campaign: null,
        token: token
      }));
    },
    logout: () => {
      if (browser) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('tempGlobalToken');
        localStorage.removeItem('tempDiscordToken');
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
export const globalLogin = auth.globalLogin;
export const logout = auth.logout;
