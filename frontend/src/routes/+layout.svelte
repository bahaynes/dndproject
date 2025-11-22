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

<header class="bg-gray-800 text-white p-4">
  <nav class="container mx-auto flex justify-between items-center">
    <a href="/" class="font-bold">DnD Hub</a>
    <div>
      {#if $auth.isAuthenticated}
        <a href="/dashboard" class="px-4 hover:underline">Dashboard</a>
        {#if $auth.user}
          <span class="px-4">Welcome, {$auth.user.username}</span>
        {/if}
        <button on:click={handleLogout} class="px-4 hover:underline">Logout</button>
      {:else}
        <a href="/login" class="px-4 hover:underline">Login</a>
        <a href="/register" class="px-4 hover:underline">Register</a>
      {/if}
    </div>
  </nav>
</header>

<main>
  <slot />
</main>
