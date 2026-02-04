<script lang="ts">
  import { onMount } from 'svelte';
  import { auth } from '$lib/auth';
  import { get } from 'svelte/store';
  import { API_BASE_URL } from '$lib/config';
  import type { Item, StoreItem } from '$lib/types';
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
  import Modal from '$lib/components/Modal.svelte';
  import { goto } from '$app/navigation';

  let items: Item[] = [];
  let storeItems: StoreItem[] = [];
  let loading = true;
  let error = "";
  let success = "";

  // Item Create Form
  let newItemName = "";
  let newItemDescription = "";
  let showCreateItem = false;

  // Add to Store Form
  let selectedItem: Item | null = null;
  let storePrice = 0;
  let storeQuantity = 10;
  let showAddToStore = false;

  onMount(async () => {
    const authState = get(auth);
    if (!authState.isAuthenticated || authState.user?.role !== 'admin') {
      goto('/dashboard');
      return;
    }
    await reloadData();
  });

  async function reloadData() {
    loading = true;
    error = "";
    try {
      await Promise.all([fetchItems(), fetchStoreItems()]);
    } catch (e) {
      error = "Failed to load data.";
    } finally {
      loading = false;
    }
  }

  async function fetchItems() {
    const res = await fetch(`${API_BASE_URL}/items/`, {
      headers: { Authorization: `Bearer ${get(auth).token}` }
    });
    if (res.ok) items = await res.json();
  }

  async function fetchStoreItems() {
    const res = await fetch(`${API_BASE_URL}/store/items/`, {
      headers: { Authorization: `Bearer ${get(auth).token}` }
    });
    if (res.ok) storeItems = await res.json();
  }

  async function createItem() {
    try {
      const res = await fetch(`${API_BASE_URL}/items/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${get(auth).token}`
        },
        body: JSON.stringify({ name: newItemName, description: newItemDescription })
      });
      if (res.ok) {
        success = "Item created successfully.";
        newItemName = "";
        newItemDescription = "";
        showCreateItem = false;
        await fetchItems();
      }
    } catch (e) {
      error = "Failed to create item.";
    }
  }

  async function addToStore() {
    if (!selectedItem) return;
    try {
      const res = await fetch(`${API_BASE_URL}/store/items/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${get(auth).token}`
        },
        body: JSON.stringify({
          item_id: selectedItem.id,
          price: storePrice,
          quantity_available: storeQuantity
        })
      });
      if (res.ok) {
        success = "Item added to store.";
        showAddToStore = false;
        await fetchStoreItems();
      }
    } catch (e) {
      error = "Failed to add to store.";
    }
  }
</script>

<div class="container mx-auto p-4 max-w-6xl">
  <div class="flex flex-col sm:flex-row justify-between items-center mb-10 gap-4">
    <h1 class="text-4xl font-bold font-[var(--font-cinzel)] text-primary">Item Management</h1>
    <button class="btn btn-primary" on:click={() => showCreateItem = true}>+ Create New Base Item</button>
  </div>

  {#if error}
    <div class="alert alert-error mb-4">{error}</div>
  {/if}
  {#if success}
    <div class="alert alert-success mb-4">{success}</div>
  {/if}

  {#if loading}
    <LoadingSpinner size="lg" />
  {:else}
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Item Catalog -->
      <div class="flex flex-col gap-4">
        <h2 class="text-2xl font-bold border-b border-base-content/10 pb-2">Master Item Catalog</h2>
        <div class="overflow-x-auto bg-base-200 rounded-xl">
          <table class="table table-zebra w-full">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th class="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {#each items as item}
                <tr>
                  <td class="font-bold">{item.name}</td>
                  <td class="text-xs max-w-xs truncate">{item.description || "-"}</td>
                  <td class="text-right">
                    <button class="btn btn-ghost btn-xs text-primary" on:click={() => { selectedItem = item; showAddToStore = true; }}>Add to Store</button>
                  </td>
                </tr>
              {/each}
              {#if items.length === 0}
                <tr><td colspan="3" class="text-center py-8 opacity-50">No items defined yet.</td></tr>
              {/if}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Store Inventory -->
      <div class="flex flex-col gap-4">
        <h2 class="text-2xl font-bold border-b border-base-content/10 pb-2">Active Store Shelves</h2>
        <div class="overflow-x-auto bg-base-200 rounded-xl">
          <table class="table table-zebra w-full">
            <thead>
              <tr>
                <th>Item</th>
                <th>Price</th>
                <th>Stock</th>
                <th class="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {#each storeItems as sItem}
                <tr>
                  <td class="font-bold">{sItem.item.name}</td>
                  <td><div class="badge badge-primary badge-sm font-bold">{sItem.price}</div></td>
                  <td>{sItem.quantity_available}</td>
                  <td class="text-right">
                    <button class="btn btn-ghost btn-xs text-error">Remove</button>
                  </td>
                </tr>
              {/each}
              {#if storeItems.length === 0}
                <tr><td colspan="4" class="text-center py-8 opacity-50">Nothing for sale in this campaign.</td></tr>
              {/if}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  {/if}
</div>

<!-- Create Item Modal -->
<Modal show={showCreateItem} title="Create Base Item" onClose={() => showCreateItem = false}>
  <div class="form-control w-full gap-4">
    <div>
      <label class="label"><span class="label-text">Item Name</span></label>
      <input type="text" bind:value={newItemName} class="input input-bordered w-full" placeholder="e.g. Longsword +1" />
    </div>
    <div>
      <label class="label"><span class="label-text">Description</span></label>
      <textarea bind:value={newItemDescription} class="textarea textarea-bordered w-full" placeholder="Item properties..."></textarea>
    </div>
  </div>
  <div slot="action">
    <button class="btn btn-primary" on:click={createItem}>Create Item</button>
  </div>
</Modal>

<!-- Add to Store Modal -->
<Modal show={showAddToStore} title="Add to Store" onClose={() => showAddToStore = false}>
  {#if selectedItem}
    <div class="form-control w-full gap-4">
      <p class="mb-2 italic">Adding <strong>{selectedItem.name}</strong> to the mission store.</p>
      <div>
        <label class="label"><span class="label-text">Price (Scrip)</span></label>
        <input type="number" bind:value={storePrice} class="input input-bordered w-full" />
      </div>
      <div>
        <label class="label"><span class="label-text">Starting Stock</span></label>
        <input type="number" bind:value={storeQuantity} class="input input-bordered w-full" />
      </div>
    </div>
  {/if}
  <div slot="action">
    <button class="btn btn-primary" on:click={addToStore}>List in Store</button>
  </div>
</Modal>
