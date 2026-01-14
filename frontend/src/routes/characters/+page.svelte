<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/auth';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';
  import type { Character } from '$lib/types';
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

  let character: Character | null = null;
  let loading = true;
  let error = "";
  let isEditing = false;
  let editName = "";
  let editDescription = "";
  let editCharacterSheetUrl = "";

  onMount(async () => {
    await fetchCharacter();
  });

  async function fetchCharacter() {
    loading = true;
    error = "";
    try {
      const authState = get(auth);
      const characterId = authState.user?.character?.id;
      
      if (!characterId) {
        // We don't set an error here anymore, we just let character be null
        loading = false;
        return;
      }

      const res = await fetch(`${API_BASE_URL}/characters/${characterId}`, {
        headers: {
          Authorization: `Bearer ${authState.token}`
        }
      });

      if (res.ok) {
        character = await res.json();
        if (character) {
          editName = character.name;
          editDescription = character.description || "";
          editCharacterSheetUrl = character.character_sheet_url || "";
        }
      } else {
        error = "Failed to load character details.";
      }
    } catch (e) {
      error = "An error occurred while loading your character.";
    } finally {
      loading = false;
    }
  }

  async function createCharacter() {
    loading = true;
    error = "";
    try {
      const authState = get(auth);
      const res = await fetch(`${API_BASE_URL}/characters/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authState.token}`
        },
        body: JSON.stringify({
          name: `${authState.user?.username}'s Hero`,
          description: "A new adventurer ready for glory."
        })
      });

      if (res.ok) {
        const newChar = await res.json();
        // Update auth store with the new character info so dashboard/other pages know
        auth.update(state => {
          if (state.user) {
            return {
              ...state,
              user: { ...state.user, character: newChar }
            };
          }
          return state;
        });
        await fetchCharacter();
      } else {
        const errData = await res.json();
        error = errData.detail || "Failed to create character.";
      }
    } catch (e) {
      error = "An error occurred while creating character.";
    } finally {
      loading = false;
    }
  }

  async function handleUpdate() {
    if (!character) return;
    
    try {
      const authState = get(auth);
      const res = await fetch(`${API_BASE_URL}/characters/${character.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authState.token}`
        },
        body: JSON.stringify({
          name: editName,
          description: editDescription,
          character_sheet_url: editCharacterSheetUrl
        })
      });

      if (res.ok) {
        character = await res.json();
        isEditing = false;
        // Optionally update the auth store if we want the dashboard to reflect changes
      } else {
        const errData = await res.json();
        error = errData.detail || "Failed to update character.";
      }
    } catch (e) {
      error = "An error occurred while saving.";
    }
  }
</script>

<div class="container mx-auto p-4 max-w-4xl">
  {#if loading}
    <LoadingSpinner size="lg" />
  {:else if error}
    <div class="alert alert-error shadow-lg mb-6">
      <div>
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <span>{error}</span>
      </div>
    </div>
    <button class="btn btn-primary" on:click={fetchCharacter}>Retry</button>
  {:else if !character}
    <div class="flex flex-col items-center justify-center p-12 bg-base-200 rounded-3xl border-2 border-dashed border-primary/20 text-center max-w-2xl mx-auto shadow-xl">
      <div class="text-7xl mb-6">🎭</div>
      <h2 class="text-3xl font-bold font-[var(--font-cinzel)] text-primary mb-4">No Hero Found</h2>
      <p class="text-lg opacity-70 mb-8">Every legend begins somewhere. Your story in this campaign hasn't started yet.</p>
      <button class="btn btn-primary btn-lg px-12 animate-bounce" on:click={createCharacter}>
        Forge Your Hero
      </button>
    </div>
  {:else if character}
    <div class="flex flex-col md:flex-row gap-6">
      <!-- Profile Card -->
      <div class="w-full md:w-1/3">
        <div class="card bg-base-200 shadow-xl border border-primary/10 h-full">
          <figure class="px-6 pt-6">
            {#if character.image_url}
              <img src={character.image_url} alt={character.name} class="rounded-xl w-full object-cover aspect-square shadow-lg" />
            {:else}
              <div class="bg-primary/20 text-primary-content flex items-center justify-center rounded-xl w-full aspect-square text-6xl font-bold">
                {character.name.charAt(0)}
              </div>
            {/if}
          </figure>
          <div class="card-body items-center text-center">
            {#if isEditing}
              <div class="form-control w-full">
                <label class="label"><span class="label-text">Character Name</span></label>
                <input type="text" bind:value={editName} class="input input-bordered input-primary w-full" />
              </div>
            {:else}
              <h2 class="card-title text-3xl font-[var(--font-cinzel)] text-primary">{character.name}</h2>
            {/if}
            
            <p class="opacity-70 text-sm">Level 1 Adventurer</p>
            
            <div class="flex flex-wrap gap-2 justify-center mt-4">
              <div class="badge badge-outline">XP: {character.stats.xp}</div>
              <div class="badge badge-outline badge-primary">Scrip: {character.stats.scrip}</div>
            </div>

            <div class="card-actions mt-6 w-full flex-col">
              {#if isEditing}
                <button class="btn btn-primary w-full" on:click={handleUpdate}>Save Changes</button>
                <button class="btn btn-ghost w-full" on:click={() => { isEditing = false; editName = character?.name || ""; editDescription = character?.description || ""; }}>Cancel</button>
              {:else}
                <button class="btn btn-outline btn-primary w-full" on:click={() => isEditing = true}>Edit Profile</button>
              {/if}
            </div>
          </div>
        </div>
      </div>

      <!-- Details Column -->
      <div class="w-full md:w-2/3 flex flex-col gap-6">
        <!-- Description -->
        <div class="card bg-base-100 shadow-xl border border-base-content/10">
          <div class="card-body">
            <h3 class="card-title font-[var(--font-cinzel)] border-b border-base-content/10 pb-2 mb-4">Backstory & Details</h3>
            {#if isEditing}
              <div class="form-control w-full">
                <textarea bind:value={editDescription} class="textarea textarea-bordered textarea-primary h-32" placeholder="Tell your story..."></textarea>
              </div>
              <div class="form-control w-full mt-4">
                <label class="label"><span class="label-text">External Character Sheet URL</span></label>
                <input type="url" bind:value={editCharacterSheetUrl} class="input input-bordered input-primary" placeholder="https://..." />
              </div>
            {:else}
              <p class="whitespace-pre-wrap leading-relaxed">
                {character.description || "No backstory provided yet. Click edit to add one!"}
              </p>
              
              {#if character.character_sheet_url}
                <div class="mt-6">
                  <a href={character.character_sheet_url} target="_blank" class="btn btn-secondary btn-outline gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                      <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                    </svg>
                    View External Sheet
                  </a>
                </div>
              {/if}
            {/if}
          </div>
        </div>

        <!-- Navigation Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <a href="/characters/inventory" class="btn btn-lg h-auto py-6 bg-base-200 hover:bg-primary hover:text-primary-content flex flex-col gap-2 transition-all">
            <span class="text-2xl">🎒</span>
            <span class="font-bold">Inventory</span>
          </a>
          <a href="/missions" class="btn btn-lg h-auto py-6 bg-base-200 hover:bg-primary hover:text-primary-content flex flex-col gap-2 transition-all">
            <span class="text-2xl">📜</span>
            <span class="font-bold">Missions</span>
          </a>
          <a href="/sessions" class="btn btn-lg h-auto py-6 bg-base-200 hover:bg-primary hover:text-primary-content flex flex-col gap-2 transition-all">
            <span class="text-2xl">📅</span>
            <span class="font-bold">Sessions</span>
          </a>
          <a href="/store" class="btn btn-lg h-auto py-6 bg-base-200 hover:bg-primary hover:text-primary-content flex flex-col gap-2 transition-all">
            <span class="text-2xl">⚖️</span>
            <span class="font-bold">Store</span>
          </a>
        </div>
      </div>
    </div>
  {/if}
</div>
