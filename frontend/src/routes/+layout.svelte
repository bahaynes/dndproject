<script lang="ts">
  import '../app.css';
  import { auth } from '$lib/auth';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';

  // Fetch user profile on mount if authenticated but no user data
  onMount(async () => {
    if (browser) {
      const currentAuth = get(auth);
      if (currentAuth.isAuthenticated && !currentAuth.user) {
        try {
          const response = await fetch('http://localhost:8000/users/me/', {
            headers: { Authorization: `Bearer ${currentAuth.token}` }
          });
          if (response.ok) {
            const user = await response.json();
            auth.setUser(user);
          } else {
            auth.logout();
          }
        } catch (e) {
          console.error('Failed to fetch user profile', e);
          auth.logout();
        }
      }
    }
  });

  function handleLogout() {
    auth.logout();
    if (browser) goto('/login');
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

