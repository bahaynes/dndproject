<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { Mission } from '../../lib/types';
  import { auth } from '../../lib/auth';
  import { get } from 'svelte/store';
  import { serverEvents } from '$lib/events';

  let missions: Mission[] = [];
  let error: string | null = null;
  let myCharacterId: number | undefined;

  const unsubscribe = serverEvents.subscribe(event => {
      if (event && event.type === 'mission_update') {
          fetchMissions();
      }
  });

  onMount(async () => {
    const authState = get(auth);
    myCharacterId = authState.user?.character?.id;
    await fetchMissions();
  });

  onDestroy(() => {
      unsubscribe();
  });

  async function fetchMissions() {
    error = null;
    try {
      const response = await fetch('/api/missions/');
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch missions');
      }
      missions = await response.json();
    } catch (err) {
      if (err instanceof Error) {
        error = err.message;
      } else {
        error = 'An unknown error occurred';
      }
    }
  }

  function isSignedUp(mission: Mission): boolean {
    if (!myCharacterId) return false;
    return mission.players.some(p => p.id === myCharacterId);
  }

  async function signup(mission: Mission) {
    error = null;
    const token = get(auth).token;
    if (!token) {
      error = 'You must be logged in to sign up.';
      return;
    }

    const url = `/api/missions/${mission.id}/signup`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sign up');
      }

      await fetchMissions();

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
  <h1 class="text-2xl font-bold">Mission Board</h1>

  {#if error}
    <div class="alert alert-error my-4">
      <div class="flex-1">
        <span>{error}</span>
      </div>
    </div>
  {/if}

  {#if missions.length === 0 && !error}
    <p class="mt-4">There are no missions available at this time.</p>
  {:else}
    <div class="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {#each missions as mission}
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title">{mission.name}</h2>
            <p>{mission.description}</p>
             <div class="my-2">
              <span class="font-bold">Status:</span>
              <span class="badge {mission.status === 'Completed' ? 'badge-success' : 'badge-info'} ml-2">{mission.status}</span>
            </div>

            <div class="my-2">
                <span class="font-bold">Rewards:</span>
                <ul class="list-disc list-inside">
                    {#each mission.rewards as reward}
                        <li>
                            {#if reward.xp} {reward.xp} XP {/if}
                            {#if reward.scrip} {reward.scrip} Scrip {/if}
                            {#if reward.item} {reward.item.name} {/if}
                        </li>
                    {/each}
                </ul>
            </div>

             <p><strong>Players ({mission.players.length}):</strong></p>
              <ul class="list-disc list-inside">
                {#each mission.players as player}
                  <li>{player.name}</li>
                {/each}
              </ul>

            <div class="card-actions justify-end mt-4">
              {#if mission.status !== 'Completed' && !isSignedUp(mission)}
                <button
                  class="btn btn-primary"
                  on:click={() => signup(mission)}
                  disabled={!myCharacterId}
                >
                  Sign Up
                </button>
              {:else if isSignedUp(mission)}
                  <span class="badge badge-success p-4">Signed Up</span>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
