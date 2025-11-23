<script lang="ts">
  import type { Mission } from '$lib/types';

  export let missions: Mission[] = [];
  export let isLoading = false;
  export let error: string | null = null;
  export let showEmptyState = true;
  export let limit: number | null = null;

  $: displayedMissions = limit ? missions.slice(0, limit) : missions;
</script>

{#if isLoading}
  <div class="panel p-4">Loading missions...</div>
{:else if error}
  <div class="alert alert-error">{error}</div>
{:else if displayedMissions.length === 0 && showEmptyState}
  <div class="panel p-4">
    <p class="muted">No missions logged yet. GMs can add dossiers to seed the board.</p>
  </div>
{:else}
  <div class="board-grid">
    {#each displayedMissions as mission}
      <div class="card">
        <div class="card-body space-y-3">
          <div class="flex items-start justify-between gap-3">
            <div class="space-y-1">
              <p class="pill w-fit">Mission</p>
              <h3 class="text-xl font-semibold leading-tight">{mission.title}</h3>
              <p class="muted text-sm leading-relaxed">{mission.summary || 'No summary added yet.'}</p>
            </div>
            <span class={`badge ${mission.status === 'available' ? 'badge-info' : 'badge-muted'}`}>
              {mission.status || 'draft'}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-3 text-sm md:text-base">
            <div class="panel panel-strong p-3">
              <p class="text-amber-100 uppercase tracking-wide text-xs">Target Hex</p>
              <p class="font-semibold mt-1">{mission.target_hex || 'Unassigned'}</p>
            </div>
            <div class="panel panel-strong p-3">
              <p class="text-amber-100 uppercase tracking-wide text-xs">Signup Pool</p>
              <p class="font-semibold mt-1">{mission.players?.length || 0}</p>
            </div>
          </div>

          {#if mission.players?.length}
            <div class="space-y-1 text-sm">
              <p class="font-semibold">Roster</p>
              <div class="flex flex-wrap gap-2">
                {#each mission.players as player}
                  <span class="badge badge-ghost">{player.name}</span>
                {/each}
              </div>
            </div>
          {/if}

          <div class="card-actions">
            <a href={`/missions/${mission.id}`} class="btn btn-ghost">Open dossier</a>
          </div>
        </div>
      </div>
    {/each}
  </div>
{/if}
