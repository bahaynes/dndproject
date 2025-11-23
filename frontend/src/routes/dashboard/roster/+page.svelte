<script lang="ts">
  import { onMount } from 'svelte';
  import { get } from 'svelte/store';
  import { auth } from '$lib/auth';
  import SectionHeader from '$lib/components/SectionHeader.svelte';
  import type { Character, CharacterStatus } from '$lib/types';
  import {
    fetchMyCharacters,
    createCharacter as apiCreateCharacter,
    updateCharacter as apiUpdateCharacter,
  } from '$lib/api';

  const statusOptions: CharacterStatus[] = ['ready', 'deployed', 'fatigued', 'medical_leave'];

  let characters: Character[] = [];
  let loading = true;
  let error: string | null = null;
  let createFeedback: string | null = null;
  let editFeedback: string | null = null;
  let creating = false;
  let savingId: number | null = null;

  const blankStats = () => ({
    xp: 0,
    commendations: 0,
    current_hp: 0,
    short_rest_available: true,
  });

  let createForm = {
    name: '',
    description: '',
    image_url: '',
    status: 'ready' as CharacterStatus,
    stats: blankStats(),
  };

  let editForm = {
    name: '',
    description: '',
    image_url: '',
    status: 'ready' as CharacterStatus,
    stats: blankStats(),
  };
  let editingId: number | null = null;

  onMount(loadRoster);

  async function loadRoster() {
    loading = true;
    error = null;
    try {
      const token = get(auth).token;
      if (!token) {
        throw new Error('Please log in to manage your roster.');
      }
      characters = await fetchMyCharacters(token);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load roster';
    } finally {
      loading = false;
    }
  }

  function mapCharacterToForm(character: Character) {
    editFeedback = null;
    editForm = {
      name: character.name,
      description: character.description || '',
      image_url: character.image_url || '',
      status: character.status || 'ready',
      stats: {
        xp: character.stats?.xp ?? 0,
        commendations: character.stats?.commendations ?? 0,
        current_hp: character.stats?.current_hp ?? 0,
        short_rest_available: character.stats?.short_rest_available ?? true,
      },
    };
    editingId = character.id;
  }

  async function createCharacter() {
    createFeedback = null;
    if (!createForm.name) {
      createFeedback = 'Name is required.';
      return;
    }

    const token = get(auth).token;
    if (!token) {
      createFeedback = 'Please log in to create a character.';
      return;
    }

    creating = true;
    try {
      await apiCreateCharacter(
        {
          name: createForm.name,
          description: createForm.description || null,
          image_url: createForm.image_url || null,
          status: createForm.status,
          stats: createForm.stats,
        },
        token,
      );
      createFeedback = 'Character added to your roster.';
      createForm = {
        name: '',
        description: '',
        image_url: '',
        status: 'ready',
        stats: blankStats(),
      };
      await loadRoster();
    } catch (err) {
      createFeedback = err instanceof Error ? err.message : 'Failed to create character';
    } finally {
      creating = false;
    }
  }

  async function saveCharacter() {
    editFeedback = null;
    if (editingId === null) return;

    const token = get(auth).token;
    if (!token) {
      editFeedback = 'Please log in to edit a character.';
      return;
    }

    savingId = editingId;
    try {
      await apiUpdateCharacter(
        editingId,
        {
          name: editForm.name,
          description: editForm.description || null,
          image_url: editForm.image_url || null,
          status: editForm.status,
          stats: editForm.stats,
        },
        token,
      );
      editFeedback = 'Character updated.';
      editingId = null;
      await loadRoster();
    } catch (err) {
      editFeedback = err instanceof Error ? err.message : 'Failed to update character';
    } finally {
      savingId = null;
    }
  }

  const setNumber = (value: string) => Number(value || 0);
</script>

<div class="page-container space-y-6">
  <SectionHeader
    eyebrow="Roster"
    title="Manage your characters"
    description="Keep multiple adventurers ready for deployment, update readiness, and prep their stats before signups."
  >
    <div slot="actions" class="flex gap-2">
      <a class="btn btn-ghost" href="/">Back to hub</a>
      <button class="btn btn-muted" on:click={loadRoster} disabled={loading}>Refresh</button>
    </div>
  </SectionHeader>

  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}

  <div class="split-grid">
    <div class="panel p-6 space-y-4">
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-lg font-semibold">Add a new character</h3>
        <span class="pill">Player tool</span>
      </div>
      <form class="space-y-3" on:submit|preventDefault={createCharacter}>
        <div class="space-y-1">
          <label class="label" for="name">Name</label>
          <input
            id="name"
            class="input-field"
            type="text"
            placeholder="E.g., Varyn the Scout"
            required
            bind:value={createForm.name}
          />
        </div>
        <div class="space-y-1">
          <label class="label" for="description">Bio</label>
          <textarea
            id="description"
            class="input-field min-h-[90px]"
            placeholder="Role, background, or roster notes."
            bind:value={createForm.description}
          ></textarea>
        </div>
        <div class="grid md:grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="label" for="image">Portrait URL</label>
            <input
              id="image"
              class="input-field"
              type="url"
              placeholder="https://..."
              bind:value={createForm.image_url}
            />
          </div>
          <div class="space-y-1">
            <label class="label" for="status">Status</label>
            <select id="status" class="input-field" bind:value={createForm.status}>
              {#each statusOptions as status}
                <option value={status}>{status}</option>
              {/each}
            </select>
          </div>
        </div>
        <div class="grid md:grid-cols-2 gap-3">
          <div class="space-y-1">
            <label class="label" for="xp">XP</label>
            <input
              id="xp"
              type="number"
              class="input-field"
              min="0"
              on:input={(e) => (createForm.stats.xp = setNumber(e.currentTarget.value))}
              value={createForm.stats.xp}
            />
          </div>
          <div class="space-y-1">
            <label class="label" for="commendations">Commendations</label>
            <input
              id="commendations"
              type="number"
              class="input-field"
              min="0"
              on:input={(e) => (createForm.stats.commendations = setNumber(e.currentTarget.value))}
              value={createForm.stats.commendations}
            />
          </div>
          <div class="space-y-1">
            <label class="label" for="hp">Current HP</label>
            <input
              id="hp"
              type="number"
              class="input-field"
              min="0"
              on:input={(e) => (createForm.stats.current_hp = setNumber(e.currentTarget.value))}
              value={createForm.stats.current_hp}
            />
          </div>
          <div class="space-y-2">
            <label class="label" for="rest">Short rest available</label>
            <div class="flex items-center gap-2">
              <input
                id="rest"
                type="checkbox"
                class="h-4 w-4"
                bind:checked={createForm.stats.short_rest_available}
              />
              <span class="muted text-sm">Mark if this character can take a short rest</span>
            </div>
          </div>
        </div>
        {#if createFeedback}
          <p class="text-sm text-amber-200">{createFeedback}</p>
        {/if}
        <div class="flex gap-2">
          <button class="btn btn-primary" type="submit" disabled={creating}>
            {creating ? 'Creating...' : 'Add character'}
          </button>
          <button
            class="btn btn-muted"
            type="button"
            on:click={() => {
              createForm = { name: '', description: '', image_url: '', status: 'ready', stats: blankStats() };
              createFeedback = null;
            }}
          >
            Reset
          </button>
        </div>
      </form>
    </div>

    <div class="panel p-6 space-y-4">
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-lg font-semibold">Your roster</h3>
        <span class="pill">{characters.length} character{characters.length === 1 ? '' : 's'}</span>
      </div>
      {#if editFeedback}
        <p class="text-sm text-amber-200">{editFeedback}</p>
      {/if}

      {#if loading}
        <div class="panel p-4">Loading characters...</div>
      {:else if characters.length === 0}
        <div class="panel p-4">
          <p class="muted">No characters yet. Add one to start scheduling sessions.</p>
        </div>
      {:else}
        <div class="board-grid">
          {#each characters as character}
            <div class="card">
              <div class="card-body space-y-3">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="pill w-fit mb-2">Character</p>
                    <h3 class="text-xl font-semibold">{character.name}</h3>
                    <p class="muted text-sm">{character.description || 'No bio added yet.'}</p>
                  </div>
                  <span class="badge badge-info uppercase text-xs">{character.status}</span>
                </div>

                {#if editingId === character.id}
                  <div class="space-y-3">
                    <div class="grid md:grid-cols-2 gap-3">
                      <div class="space-y-1">
                        <label class="label" for={`edit-name-${character.id}`}>Name</label>
                        <input
                          id={`edit-name-${character.id}`}
                          class="input-field"
                          type="text"
                          bind:value={editForm.name}
                        />
                      </div>
                      <div class="space-y-1">
                        <label class="label" for={`edit-status-${character.id}`}>Status</label>
                        <select
                          id={`edit-status-${character.id}`}
                          class="input-field"
                          bind:value={editForm.status}
                        >
                          {#each statusOptions as status}
                            <option value={status}>{status}</option>
                          {/each}
                        </select>
                      </div>
                    </div>
                    <div class="space-y-1">
                      <label class="label" for={`edit-desc-${character.id}`}>Bio</label>
                      <textarea
                        id={`edit-desc-${character.id}`}
                        class="input-field min-h-[80px]"
                        bind:value={editForm.description}
                      ></textarea>
                    </div>
                    <div class="space-y-1">
                      <label class="label" for={`edit-img-${character.id}`}>Portrait URL</label>
                      <input
                        id={`edit-img-${character.id}`}
                        class="input-field"
                        type="url"
                        bind:value={editForm.image_url}
                      />
                    </div>
                    <div class="grid md:grid-cols-2 gap-3">
                      <div class="space-y-1">
                        <label class="label" for={`edit-xp-${character.id}`}>XP</label>
                        <input
                          id={`edit-xp-${character.id}`}
                          type="number"
                          class="input-field"
                          min="0"
                          on:input={(e) => (editForm.stats.xp = setNumber(e.currentTarget.value))}
                          value={editForm.stats.xp}
                        />
                      </div>
                      <div class="space-y-1">
                        <label class="label" for={`edit-commendations-${character.id}`}>Commendations</label>
                        <input
                          id={`edit-commendations-${character.id}`}
                          type="number"
                          class="input-field"
                          min="0"
                          on:input={(e) => (editForm.stats.commendations = setNumber(e.currentTarget.value))}
                          value={editForm.stats.commendations}
                        />
                      </div>
                      <div class="space-y-1">
                        <label class="label" for={`edit-hp-${character.id}`}>Current HP</label>
                        <input
                          id={`edit-hp-${character.id}`}
                          type="number"
                          class="input-field"
                          min="0"
                          on:input={(e) => (editForm.stats.current_hp = setNumber(e.currentTarget.value))}
                          value={editForm.stats.current_hp}
                        />
                      </div>
                      <div class="space-y-2">
                        <label class="label" for={`edit-rest-${character.id}`}>Short rest available</label>
                        <div class="flex items-center gap-2">
                          <input
                            id={`edit-rest-${character.id}`}
                            type="checkbox"
                            class="h-4 w-4"
                            bind:checked={editForm.stats.short_rest_available}
                          />
                          <span class="muted text-sm">Mark if this character can take a short rest</span>
                        </div>
                      </div>
                    </div>
                    <div class="flex gap-2">
                      <button
                        class="btn btn-primary"
                        type="button"
                        on:click={saveCharacter}
                        disabled={savingId === character.id}
                      >
                        {savingId === character.id ? 'Saving...' : 'Save'}
                      </button>
                      <button class="btn btn-muted" type="button" on:click={() => (editingId = null)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                {:else}
                  <div class="grid grid-cols-2 gap-3 text-sm">
                    <div class="panel panel-strong p-3">
                      <p class="text-amber-100 uppercase tracking-wide text-xs">XP</p>
                      <p class="font-semibold mt-1">{character.stats?.xp ?? 0}</p>
                    </div>
                    <div class="panel panel-strong p-3">
                      <p class="text-amber-100 uppercase tracking-wide text-xs">Commendations</p>
                      <p class="font-semibold mt-1">{character.stats?.commendations ?? 0}</p>
                    </div>
                    <div class="panel panel-strong p-3">
                      <p class="text-amber-100 uppercase tracking-wide text-xs">Current HP</p>
                      <p class="font-semibold mt-1">{character.stats?.current_hp ?? 0}</p>
                    </div>
                    <div class="panel panel-strong p-3">
                      <p class="text-amber-100 uppercase tracking-wide text-xs">Short Rest</p>
                      <p class="font-semibold mt-1">
                        {character.stats?.short_rest_available ? 'Available' : 'Unavailable'}
                      </p>
                    </div>
                  </div>
                  <div class="card-actions">
                    <button class="btn btn-ghost" on:click={() => mapCharacterToForm(character)}>Edit</button>
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
