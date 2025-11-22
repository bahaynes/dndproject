<script lang="ts">
  import { onMount } from 'svelte';
  import type { GameSessionWithPlayers } from '../../lib/types';
  import { auth } from '../../lib/auth';
  import { get } from 'svelte/store';

  let sessions: GameSessionWithPlayers[] = [];
  let error: string | null = null;
  let myCharacterId: number | undefined;

  onMount(async () => {
    const authState = get(auth);
    myCharacterId = authState.user?.character?.id;
    await fetchSessions();
  });

  async function fetchSessions() {
    error = null;
    try {
      const token = get(auth).token;
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }
      const response = await fetch('/api/sessions/', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch sessions');
      }
      sessions = await response.json();
    } catch (err) {
      if (err instanceof Error) {
        error = err.message;
      } else {
        error = 'An unknown error occurred';
      }
    }
  }

  function isSignedUp(session: GameSessionWithPlayers): boolean {
    if (!myCharacterId) return false;
    return session.players.some(p => p.id === myCharacterId);
  }

  async function toggleSignup(session: GameSessionWithPlayers) {
    error = null;
    const token = get(auth).token;
    if (!token) {
      error = 'You must be logged in to sign up.';
      return;
    }

    const method = isSignedUp(session) ? 'DELETE' : 'POST';
    const url = `/api/sessions/${session.id}/signup`;

    try {
      const response = await fetch(url, {
        method: method,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update signup status');
      }

      // Refresh the session list to show the change
      await fetchSessions();

    } catch (err) {
      if (err instanceof Error) {
        error = err.message;
      } else {
        error = 'An unknown error occurred';
      }
    }
  }
</script>

<div class="page-container space-y-6">
  <div class="flex flex-col gap-2">
    <p class="text-sm uppercase tracking-wide text-amber-200">Session board</p>
    <h1 class="text-3xl font-bold">Game Sessions</h1>
    <p class="muted">Sign up your character, review party slots, and keep the frontier organized.</p>
  </div>

  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}

  {#if sessions.length === 0 && !error}
    <div class="panel p-6">
      <p class="muted">There are no scheduled sessions at this time. Check back later!</p>
    </div>
  {:else}
    <div class="card-grid">
      {#each sessions as session}
        <div class="card">
          <div class="card-body">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="pill w-fit mb-2">Session</p>
                <h2 class="card-title">{session.name}</h2>
              </div>
              <span class="badge {session.status === 'Completed' ? 'badge-success' : 'badge-info'}">{session.status}</span>
            </div>
            <p class="muted">{session.description}</p>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div class="panel panel-strong p-3">
                <p class="text-amber-100 uppercase tracking-wide text-xs">Date</p>
                <p class="font-semibold mt-1">{new Date(session.session_date).toLocaleString()}</p>
              </div>
              <div class="panel panel-strong p-3">
                <p class="text-amber-100 uppercase tracking-wide text-xs">Players</p>
                <p class="font-semibold mt-1">{session.players.length}</p>
              </div>
            </div>
            <div class="space-y-1 text-sm">
              <p class="font-semibold">Roster</p>
              <ul class="list-disc list-inside muted">
                {#each session.players as player}
                  <li>{player.name}</li>
                {/each}
              </ul>
            </div>
            <div class="card-actions mt-2">
              {#if session.status === 'Scheduled'}
                <button
                  class="btn {isSignedUp(session) ? 'btn-muted' : 'btn-primary'}"
                  on:click={() => toggleSignup(session)}
                  disabled={!myCharacterId}
                >
                  {isSignedUp(session) ? 'Cancel signup' : 'Sign up'}
                </button>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
