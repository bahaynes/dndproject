<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/auth';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';
  import type { Character, InventoryItem } from '$lib/types';
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

  let character: Character | null = null;
  let loading = true;
  let error = "";

  onMount(async () => {
    await fetchInventory();
  });

  async function fetchInventory() {
    loading = true;
    error = "";
    try {
      const authState = get(auth);
      const characterId = authState.user?.character?.id;
      
      if (!characterId) {
        error = "No character found.";
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
      } else {
        error = "Failed to load inventory.";
      }
    } catch (e) {
      error = "An error occurred while loading inventory.";
    } finally {
      loading = false;
    }
  }

  async function removeItem(inventoryItem: InventoryItem) {
    if (!character) return;
    
    // We confirm removal usually, but for simple MVP let's just do it
    try {
      const authState = get(auth);
      // Backend expects inventory_item_id as path param for removal
      // Based on inventory_router.py: @router.delete("/{inventory_item_id}", tags=["Inventory"])
      const res = await fetch(`${API_BASE_URL}/characters/${character.id}/inventory/${inventoryItem.id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${authState.token}`
        }
      });

      if (res.ok) {
        // Refresh local list
        await fetchInventory();
      } else {
        const errData = await res.json();
        error = errData.detail || "Failed to remove item.";
      }
    } catch (e) {
      error = "An error occurred while removing the item.";
    }
  }
</script>

<div class="container mx-auto p-4 max-w-4xl">
  <div class="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
    <div>
      <h1 class="text-4xl font-bold font-[var(--font-cinzel)] text-primary tracking-tight">Inventory</h1>
      {#if character}
        <p class="text-sm opacity-60">Backpack of {character.name}</p>
      {/if}
    </div>
    <div class="flex gap-2">
      <a href="/characters" class="btn btn-outline btn-sm">Back to Sheet</a>
      <a href="/store" class="btn btn-primary btn-sm">Visit Store</a>
    </div>
  </div>

  {#if loading}
    <LoadingSpinner size="lg" />
  {:else if error}
    <div class="alert alert-error shadow-lg mb-6">
      <div>
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <span>{error}</span>
      </div>
    </div>
    <button class="btn btn-primary" on:click={fetchInventory}>Retry</button>
  {:else if character}
    {#if character.inventory.length === 0}
      <div class="bg-base-200 rounded-2xl p-12 text-center border-2 border-dashed border-base-content/20">
        <span class="text-6xl mb-4 block">🎒</span>
        <h2 class="text-2xl font-bold mb-2">Backpack is Empty</h2>
        <p class="opacity-70 mb-6">You haven't acquired any items yet. Venture out on missions or visit the local store!</p>
        <a href="/store" class="btn btn-primary px-8">Browse the Store</a>
      </div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#each character.inventory as invItem}
          <div class="card bg-base-100 shadow-md border border-base-content/10 hover:border-primary/30 transition-all group">
            <div class="card-body">
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="card-title text-xl font-bold">{invItem.item.name}</h3>
                  <div class="badge badge-primary badge-sm mt-1">Qty: {invItem.quantity}</div>
                </div>
                <button 
                  class="btn btn-circle btn-xs btn-ghost text-error opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Remove Item"
                  on:click={() => removeItem(invItem)}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
              <p class="text-sm opacity-70 mt-2">{invItem.item.description || "No description available."}</p>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>
