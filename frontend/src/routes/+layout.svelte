<script lang="ts">
  import '../app.css';
  import { auth, setAuth, clearAuth } from '$lib/auth';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';

  onMount(async () => {
    if (browser) {
      const token = localStorage.getItem('accessToken');
      const currentAuth = get(auth);

      if (token && !currentAuth.isAuthenticated) {
        try {
          const response = await fetch('/api/users/me/', {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (response.ok) {
            const user = await response.json();
            setAuth(user, token);
          } else {
            // Token is invalid, so log out
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
    clearAuth();
    if (browser) {
      localStorage.removeItem('accessToken');
      goto('/login');
    }
  }
</script>

<header>
  <nav class="page-container flex items-center justify-between py-4">
    <a href="/" class="brand-mark">
      <span>DnD</span>
      <span>Westmarches</span>
    </a>
    <div class="flex items-center gap-2">
      <a href="/sessions" class="nav-link">Sessions</a>
      <a href="/missions" class="nav-link">Missions</a>
      {#if $auth.isAuthenticated}
        <a href="/dashboard/roster" class="nav-link">Roster</a>
        <a href="/dashboard" class="nav-link">Dashboard</a>
        {#if $auth.user}
          <span class="nav-link">Welcome, {$auth.user.username}</span>
        {/if}
        <button on:click={handleLogout} class="nav-link">Logout</button>
      {:else}
        <a href="/login" class="nav-link">Login</a>
        <a href="/register" class="nav-link">Register</a>
      {/if}
    </div>
  </nav>
</header>

<main class="page-shell">
  <slot />
</main>
