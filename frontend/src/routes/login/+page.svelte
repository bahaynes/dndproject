<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth, login } from '$lib/auth';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';

  let isDev = false;
  let devLoading = false;
  let devError = '';

  onMount(async () => {
    const { isAuthenticated } = get(auth);
    if (isAuthenticated) {
      goto('/dashboard');
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/auth/dev-status`);
      if (res.ok) {
        const data = await res.json();
        isDev = Boolean(data.dev_login_enabled);
      }
    } catch {
      isDev = false;
    }
  });

  function handleLogin() {
    window.location.href = `${API_BASE_URL}/auth/discord/login`;
  }

  async function handleDevLogin(role: 'player' | 'admin') {
    devLoading = true;
    devError = '';
    try {
      const payload =
        role === 'admin'
          ? { discord_id: 'e2e_admin_001', username: 'Dev DM', role: 'admin' }
          : { discord_id: 'e2e_player_001', username: 'Dev Player', role: 'player' };

      const tokenRes = await fetch(`${API_BASE_URL}/auth/dev-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!tokenRes.ok) {
        const err = await tokenRes.json().catch(() => ({}));
        devError = err.detail || `Dev login failed (${tokenRes.status}).`;
        return;
      }

      const { access_token } = await tokenRes.json();
      const userRes = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      });

      if (!userRes.ok) {
        devError = 'Failed to load dev user profile.';
        return;
      }

      const user = await userRes.json();
      login(user, access_token, user.campaign);
      goto('/dashboard');
    } catch {
      devError = 'Error connecting to dev login endpoint.';
    } finally {
      devLoading = false;
    }
  }
</script>

<div class="flex items-center justify-center min-h-screen bg-base-200">
  <div class="w-full max-w-md p-8 bg-base-100 shadow-md rounded-lg text-center">
    <h1 class="text-2xl font-bold mb-6">Login to DnD Westmarches</h1>
    <p class="mb-4 text-base-content/70">Please sign in using your Discord account.</p>

    <button
      on:click={handleLogin}
      class="btn btn-primary flex items-center justify-center w-full"
    >
      <svg class="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 127.14 96.36" xmlns="http://www.w3.org/2000/svg">
        <path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/>
      </svg>
      Login with Discord
    </button>

    {#if isDev}
      <div class="mt-6 border-t border-base-content/15 pt-5">
        <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-base-content/50">
          Dev Login (No Discord Required)
        </p>
        {#if devError}
          <div role="alert" class="alert alert-error mb-3 py-2 text-left text-sm">
            {devError}
          </div>
        {/if}
        <div class="grid grid-cols-2 gap-2">
          <button
            type="button"
            disabled={devLoading}
            on:click={() => handleDevLogin('player')}
            class="btn btn-outline btn-sm"
          >
            Dev Player
          </button>
          <button
            type="button"
            disabled={devLoading}
            on:click={() => handleDevLogin('admin')}
            class="btn btn-outline btn-secondary btn-sm"
          >
            Dev DM (Admin)
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>
