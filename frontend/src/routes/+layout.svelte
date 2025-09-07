<script lang="ts">
  import '../app.css';
  import { auth, initializeAuth, logout } from '$lib/auth';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  onMount(async () => {
    if (browser) {
      // Initialize authentication state when the component mounts
      await initializeAuth();
    }
  });

  function handleLogout() {
    logout();
    goto('/login');
  }
</script>

<header class="bg-gray-800 text-white p-4">
  <nav class="container mx-auto flex justify-between items-center">
    <a href="/" class="font-bold">DnD Hub</a>
    <div>
      {#if $auth.isAuthenticated}
        <a href="/dashboard" class="px-4 hover:underline">Dashboard</a>
        <a href="/sessions" class="px-4 hover:underline">Sessions</a>
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

<main class="p-4">
  <slot />
</main>
