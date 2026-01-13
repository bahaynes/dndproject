<script lang="ts">
  import '../app.css';
  import { auth, login, logout } from '$lib/auth';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';

  onMount(async () => {
    if (browser) {
      const token = localStorage.getItem('accessToken');
      const currentAuth = get(auth);

      if (token && !currentAuth.isAuthenticated) {
        try {
          // Check if token is valid and get user info
          const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (response.ok) {
            const user = await response.json();
            // We assume if /auth/me succeeds with a campaign-scoped token,
            // the user object has campaign info or we can fetch it.
            // My User model in backend has `campaign` relationship.
            login(user, token, user.campaign);
          } else {
            // Token is invalid
            handleLogout();
          }
        } catch (e) {
          console.error('Failed to fetch user profile', e);
          handleLogout();
        }
      }
    }
  });

  function handleLogout() {
    logout();
    if (browser) {
      localStorage.removeItem('accessToken');
      goto('/login');
    }
  }
</script>

<header class="bg-gray-800 text-white p-4">
  <nav class="container mx-auto flex justify-between items-center">
    <a href="/" class="font-bold text-xl">DnD Westmarches</a>
    <div class="flex items-center space-x-4">
      {#if $auth.isAuthenticated}
        {#if $auth.campaign}
            <span class="bg-indigo-700 px-3 py-1 rounded text-sm">{$auth.campaign.name}</span>
        {/if}
        <a href="/dashboard" class="hover:text-gray-300">Dashboard</a>
        <a href="/campaigns" class="hover:text-gray-300">Switch Campaign</a>
        {#if $auth.user}
          <span class="hidden md:inline">{$auth.user.username}</span>
        {/if}
        <button on:click={handleLogout} class="hover:text-red-400">Logout</button>
      {:else}
        <a href="/login" class="hover:text-gray-300">Login</a>
      {/if}
    </div>
  </nav>
</header>

<main class="min-h-screen bg-gray-50">
  <slot />
</main>
