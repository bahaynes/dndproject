<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { goto } from '$app/navigation';
  import { auth, type AuthState } from '$lib/auth';
  import type { User } from '$lib/types';

  let loading = true;
  let error: string | null = null;
  let users: User[] = [];

  async function loadRoster(currentAuth: AuthState) {
    if (!currentAuth.token) {
      error = 'Please log in as an admin to view the roster.';
      loading = false;
      goto('/login');
      return;
    }

    if (currentAuth.user?.role !== 'admin') {
      error = 'Admin access required to view the roster.';
      loading = false;
      goto('/dashboard');
      return;
    }

    try {
      const response = await fetch('/api/users/', {
        headers: {
          Authorization: `Bearer ${currentAuth.token}`,
        },
      });

      if (!response.ok) {
        const detail = (await response.json())?.detail;
        throw new Error(detail || 'Failed to load roster');
      }

      users = await response.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error loading roster';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    const currentAuth = get(auth);
    loadRoster(currentAuth);
  });
</script>

<div class="container mx-auto p-4 space-y-4">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-sm uppercase tracking-wide text-gray-500">Admin</p>
      <h1 class="text-2xl font-bold">User Roster</h1>
      <p class="text-sm text-gray-600">All players and their linked characters.</p>
    </div>
  </div>

  {#if loading}
    <p>Loading roster...</p>
  {:else if error}
    <div class="alert alert-error">
      <span>{error}</span>
    </div>
  {:else}
    <div class="overflow-x-auto">
      <table class="table w-full">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Character</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {#each users as user}
            <tr>
              <td class="font-semibold">{user.username}</td>
              <td>{user.email}</td>
              <td>
                <span class="badge {user.role === 'admin' ? 'badge-secondary' : 'badge-primary'}">{user.role}</span>
              </td>
              <td>{user.character ? user.character.name : 'No character'}</td>
              <td>
                <span class="badge {user.is_active ? 'badge-success' : 'badge-ghost'}">
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
