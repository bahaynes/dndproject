<script lang="ts">
  import { onMount } from 'svelte';
  import type { GameSessionWithPlayers } from '../../../../lib/types';
  import { auth } from '../../../../lib/auth';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';

  let sessions: GameSessionWithPlayers[] = [];
  let error: string | null = null;
  let showCreateForm = false;
  let managedSessionId: number | null = null;

  let newSession = {
    name: '',
    description: '',
    session_date: '',
  };

  let sessionToUpdate = {
      status: 'Scheduled' as 'Scheduled' | 'Completed',
      after_action_report: '',
      // We need to include all fields from GameSessionCreate, even if not updated
      name: '',
      description: '',
      session_date: '',
  };

  function toggleManage(sessionId: number) {
    if (managedSessionId === sessionId) {
      managedSessionId = null;
    } else {
      managedSessionId = sessionId;
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        sessionToUpdate = {
            name: session.name,
            description: session.description || '',
            session_date: session.session_date,
            status: session.status,
            after_action_report: session.after_action_report || ''
        };
      }
    }
  }

  async function updateSession(sessionId: number) {
    error = null;
    try {
        const token = get(auth).token;
        if (!token) {
            throw new Error('Not authenticated. Please log in.');
        }
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(sessionToUpdate),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update session');
        }
        managedSessionId = null;
        await fetchSessions(); // Refresh the list
    } catch (err) {
        if (err instanceof Error) {
            error = err.message;
        } else {
            error = 'An unknown error occurred';
        }
    }
  }

  onMount(async () => {
    await fetchSessions();
  });

  async function fetchSessions() {
    error = null;
    try {
      const token = get(auth).token;
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }
      const response = await fetch(`${API_BASE_URL}/sessions/`, {
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

  async function createSession() {
    error = null;
    try {
      const token = get(auth).token;
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }
      const response = await fetch(`${API_BASE_URL}/sessions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...newSession,
          session_date: new Date(newSession.session_date).toISOString(),
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create session');
      }
      showCreateForm = false;
      newSession = { name: '', description: '', session_date: '' };
      await fetchSessions(); // Refresh the list
    } catch (err) {
      if (err instanceof Error) {
        error = err.message;
      } else {
        error = 'An unknown error occurred';
      }
    }
  }
</script>

<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">Admin: Manage Game Sessions</h1>

    <div class="my-4">
        <button on:click={() => (showCreateForm = !showCreateForm)} class="btn btn-primary">
            {showCreateForm ? 'Cancel' : 'Schedule New Session'}
        </button>
    </div>

    {#if showCreateForm}
        <div class="card bg-base-200 shadow-xl p-4 my-4">
            <h2 class="text-xl font-bold mb-2">New Session</h2>
            <form on:submit|preventDefault={createSession}>
                <div class="form-control">
                    <label class="label" for="name">Name</label>
                    <input type="text" id="name" bind:value={newSession.name} class="input input-bordered" required />
                </div>
                <div class="form-control">
                    <label class="label" for="description">Description</label>
                    <textarea id="description" bind:value={newSession.description} class="textarea textarea-bordered"></textarea>
                </div>
                <div class="form-control">
                    <label class="label" for="session_date">Date</label>
                    <input type="datetime-local" id="session_date" bind:value={newSession.session_date} class="input input-bordered" required />
                </div>
                <div class="mt-4">
                    <button type="submit" class="btn btn-primary">Create</button>
                </div>
            </form>
        </div>
    {/if}

    {#if error}
        <p class="text-red-500">{error}</p>
  {:else if sessions.length === 0}
    <p>No game sessions found.</p>
  {:else}
    <div class="mt-4 space-y-4">
      {#each sessions as session}
        <div class="border p-4 rounded-lg">
          <h2 class="text-xl font-semibold">{session.name}</h2>
          <p>{session.description}</p>
          <p><strong>Date:</strong> {new Date(session.session_date).toLocaleString()}</p>
          <p><strong>Status:</strong> {session.status}</p>
          <p><strong>Players ({session.players.length}):</strong></p>
          <ul>
            {#each session.players as player}
              <li>{player.name}</li>
            {/each}
          </ul>
          <div class="mt-2">
            <button on:click={() => toggleManage(session.id)} class="btn btn-sm btn-secondary">
              {managedSessionId === session.id ? 'Close' : 'Manage'}
            </button>
          </div>

          {#if managedSessionId === session.id}
            <div class="mt-4 p-4 bg-base-300 rounded-lg">
              <h3 class="text-lg font-bold">Update Session</h3>
              <form on:submit|preventDefault={() => updateSession(session.id)}>
                <div class="form-control">
                  <label class="label" for="status-{session.id}">Status</label>
                  <select id="status-{session.id}" bind:value={sessionToUpdate.status} class="select select-bordered">
                    <option>Scheduled</option>
                    <option>Completed</option>
                  </select>
                </div>
                <div class="form-control mt-2">
                  <label class="label" for="aar-{session.id}">After-Action Report</label>
                  <textarea id="aar-{session.id}" bind:value={sessionToUpdate.after_action_report} class="textarea textarea-bordered"></textarea>
                </div>
                <div class="mt-4">
                  <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
              </form>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
