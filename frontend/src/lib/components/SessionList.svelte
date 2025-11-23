<script lang="ts">
  import type { GameSessionWithPlayers } from '$lib/types';

  export let sessions: GameSessionWithPlayers[] = [];
  export let myCharacterId: number | undefined = undefined;
  export let isLoading = false;
  export let error: string | null = null;
  export let pendingSessionId: string | null = null;
  export let showEmptyState = true;
  export let onToggleSignup: (session: GameSessionWithPlayers) => void = () => {};
  export let isSignedUp: (session: GameSessionWithPlayers) => boolean = () => false;

  const formatDate = (value: string) => {
    const date = new Date(value);
    return date.toLocaleString();
  };
</script>

{#if isLoading}
  <div class="panel p-4">Loading sessions...</div>
{:else if error}
  <div class="alert alert-error">{error}</div>
{:else if sessions.length === 0 && showEmptyState}
  <div class="panel p-4">
    <p class="muted">No sessions scheduled. Check back soon.</p>
  </div>
{:else}
  <div class="board-grid">
    {#each sessions as session}
      <div class="card">
        <div class="card-body space-y-3">
          <div class="flex items-start justify-between gap-3">
            <div class="space-y-1">
              <p class="pill w-fit">Session</p>
              <h3 class="text-xl font-semibold leading-tight">{session.title}</h3>
              {#if session.gm_notes}
                <p class="muted text-sm leading-relaxed">{session.gm_notes}</p>
              {/if}
            </div>
            <span
              class={`badge ${
                session.status === 'completed'
                  ? 'badge-success'
                  : session.status === 'cancelled'
                    ? 'badge-error'
                    : 'badge-info'
              }`}
            >
              {session.status}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-3 text-sm md:text-base">
            <div class="panel panel-strong p-3">
              <p class="text-amber-100 uppercase tracking-wide text-xs">Date</p>
              <p class="font-semibold mt-1">{formatDate(session.session_date)}</p>
            </div>
            <div class="panel panel-strong p-3">
              <p class="text-amber-100 uppercase tracking-wide text-xs">Players</p>
              <p class="font-semibold mt-1">{session.players.length}</p>
            </div>
          </div>

          {#if session.route_data && session.route_data.length}
            <div class="text-sm muted">
              <span class="font-semibold text-amber-50">Route:</span> {session.route_data.join(' -> ')}
            </div>
          {/if}

          <div class="space-y-1 text-sm">
            <p class="font-semibold">Roster</p>
            <div class="flex flex-wrap gap-2">
              {#if session.players.length === 0}
                <span class="muted">No signups yet.</span>
              {:else}
                {#each session.players as player}
                  <span class="badge badge-ghost">{player.name}</span>
                {/each}
              {/if}
            </div>
          </div>

          {#if session.status === 'open'}
            <div class="card-actions">
              <button
                class={`btn ${isSignedUp(session) ? 'btn-muted' : 'btn-primary'}`}
                on:click={() => onToggleSignup(session)}
                disabled={pendingSessionId === session.id || !myCharacterId}
              >
                {#if pendingSessionId === session.id}
                  Saving...
                {:else}
                  {#if !myCharacterId}
                    Add a character to join
                  {:else}
                    {isSignedUp(session) ? 'Cancel signup' : 'Sign up to play'}
                  {/if}
                {/if}
              </button>
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
{/if}
