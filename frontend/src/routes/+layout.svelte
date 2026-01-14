<script lang="ts">
  import '../app.css';
  import { auth, login, logout } from '$lib/auth';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';
  import ThemeSwitcher from '$lib/components/ThemeSwitcher.svelte';

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

<div class="min-h-screen flex flex-col">
  <nav class="navbar bg-base-300 shadow-lg border-b border-base-content/10">
    <div class="navbar-start">
      <div class="dropdown">
        <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8m-8 6h16" /></svg>
        </div>
        <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-200 rounded-box w-52">
          {#if $auth.isAuthenticated}
             <li><a href="/dashboard">Dashboard</a></li>
             <li><a href="/campaigns">Switch Campaign</a></li>
             <li><button on:click={handleLogout}>Logout</button></li>
          {:else}
             <li><a href="/login">Login</a></li>
          {/if}
        </ul>
      </div>
      <a href="/" class="btn btn-ghost text-xl font-[var(--font-cinzel)] tracking-wider">DnD Westmarches</a>
    </div>

    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal px-1 gap-2">
        {#if $auth.isAuthenticated}
          <li><a href="/dashboard" class="font-semibold">Dashboard</a></li>
          <li><a href="/campaigns" class="font-semibold">Switch Campaign</a></li>
        {/if}
      </ul>
    </div>

    <div class="navbar-end gap-2">
      {#if $auth.isAuthenticated}
        {#if $auth.campaign}
            <div class="badge badge-primary hidden md:flex font-bold">{$auth.campaign.name}</div>
        {/if}
        {#if $auth.user}
          <div class="text-sm font-bold hidden md:block opacity-70 mr-2">{$auth.user.username}</div>
        {/if}
        <button on:click={handleLogout} class="btn btn-sm btn-error hidden lg:flex">Logout</button>
      {:else}
        <a href="/login" class="btn btn-primary btn-sm hidden lg:flex">Login</a>
      {/if}
      <ThemeSwitcher />
    </div>
  </nav>

  <main class="flex-grow bg-base-100">
    <slot />
  </main>
</div>
