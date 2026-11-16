<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { Item, StoreItem } from '$lib/types';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import { goto } from '$app/navigation';

	let items: Item[] = [];
	let storeItems: StoreItem[] = [];
	let loading = true;
	let error = '';
	let success = '';

	// Item Create Form
	let newItemName = '';
	let newItemDescription = '';
	let showCreateItem = false;

	// Add to Store Form
	let selectedItem: Item | null = null;
	let storePrice = 0;
	let storeQuantity = 10;
	let showAddToStore = false;

	let dataLoaded = false;

	onMount(() => {
		if (!localStorage.getItem('accessToken')) goto('/dashboard');
	});

	$: if ($auth.isAuthenticated && $auth.user?.role === 'admin' && !dataLoaded) {
		dataLoaded = true;
		reloadData();
	}

	async function reloadData() {
		loading = true;
		error = '';
		try {
			await Promise.all([fetchItems(), fetchStoreItems()]);
		} catch (e) {
			error = 'Failed to load data.';
		} finally {
			loading = false;
		}
	}

	async function fetchItems() {
		items = await api('GET', '/items/');
	}

	async function fetchStoreItems() {
		storeItems = await api('GET', '/store/items/');
	}

	async function createItem() {
		error = '';
		try {
			await api('POST', '/items/', { name: newItemName, description: newItemDescription });
			success = 'Item created.';
			newItemName = '';
			newItemDescription = '';
			showCreateItem = false;
			await fetchItems();
		} catch (e) {
			error = 'Failed to create item.';
		}
	}

	async function addToStore() {
		if (!selectedItem) return;
		error = '';
		try {
			await api('POST', '/store/items/', {
				item_id: selectedItem.id,
				price: storePrice,
				quantity_available: storeQuantity
			});
			success = 'Item stocked in Quartermaster Store.';
			showAddToStore = false;
			await fetchStoreItems();
		} catch (e) {
			error = 'Failed to add to store.';
		}
	}

	async function removeStoreItem(storeItemId: number) {
		error = '';
		try {
			await api('DELETE', `/store/items/${storeItemId}`);
			success = 'Item removed from store.';
			await fetchStoreItems();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to remove item from store.';
		}
	}
</script>

<PageHeader
	title="Store & Items"
	subtitle="Manage the campaign item catalog and Quartermaster Store inventory (prices in GP)."
>
	<button slot="actions" class="btn btn-primary btn-sm" on:click={() => (showCreateItem = true)}>
		+ New Base Item
	</button>
</PageHeader>

{#if error}
	<div class="alert alert-error mb-4 text-sm">{error}</div>
{/if}
{#if success}
	<div class="alert alert-success mb-4 text-sm">{success}</div>
{/if}

{#if loading}
	<LoadingSpinner size="lg" />
{:else}
	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<!-- Master Item Catalog -->
		<section class="panel overflow-hidden">
			<div class="border-b border-base-content/10 px-5 py-3.5">
				<h2 class="text-sm font-semibold text-base-content">Master Item Catalog</h2>
			</div>
			<div class="overflow-x-auto">
				<table class="table table-sm">
					<thead class="bg-base-300/60 text-xs text-base-content/65">
						<tr>
							<th>Name</th>
							<th>Description</th>
							<th class="text-right">Action</th>
						</tr>
					</thead>
					<tbody>
						{#each items as item}
							<tr class="border-b border-base-content/5">
								<td class="font-medium">{item.name}</td>
								<td class="max-w-xs truncate text-xs text-base-content/65">
									{item.description || '—'}
								</td>
								<td class="text-right">
									<button
										class="btn btn-ghost btn-xs text-primary"
										on:click={() => {
											selectedItem = item;
											storePrice = 10;
											storeQuantity = 5;
											showAddToStore = true;
										}}
									>
										Stock
									</button>
								</td>
							</tr>
						{/each}
						{#if items.length === 0}
							<tr>
								<td colspan="3" class="py-8 text-center text-xs text-base-content/50">
									No items defined yet.
								</td>
							</tr>
						{/if}
					</tbody>
				</table>
			</div>
		</section>

		<!-- Active Store Shelves -->
		<section class="panel overflow-hidden">
			<div class="border-b border-base-content/10 px-5 py-3.5">
				<h2 class="text-sm font-semibold text-base-content">Active Store Shelves</h2>
			</div>
			<div class="overflow-x-auto">
				<table class="table table-sm">
					<thead class="bg-base-300/60 text-xs text-base-content/65">
						<tr>
							<th>Item</th>
							<th>Price (GP)</th>
							<th>Stock</th>
							<th class="text-right">Action</th>
						</tr>
					</thead>
					<tbody>
						{#each storeItems as sItem}
							<tr class="border-b border-base-content/5">
								<td class="font-medium">{sItem.item.name}</td>
								<td class="text-primary stat-num">{sItem.price} GP</td>
								<td class="stat-num">
									{sItem.quantity_available === -1 ? '∞' : sItem.quantity_available}
								</td>
								<td class="text-right">
									<button
										class="btn btn-ghost btn-xs text-error"
										on:click={() => removeStoreItem(sItem.id)}
									>
										Remove
									</button>
								</td>
							</tr>
						{/each}
						{#if storeItems.length === 0}
							<tr>
								<td colspan="4" class="py-8 text-center text-xs text-base-content/50">
									Nothing for sale in this campaign.
								</td>
							</tr>
						{/if}
					</tbody>
				</table>
			</div>
		</section>
	</div>
{/if}

<Modal show={showCreateItem} title="Create Base Item" onClose={() => (showCreateItem = false)}>
	<div class="space-y-4">
		<div>
			<label for="new-item-name" class="mb-1 block text-xs font-medium text-base-content/75">
				Item Name
			</label>
			<input
				id="new-item-name"
				type="text"
				bind:value={newItemName}
				class="input input-bordered input-sm w-full"
				placeholder="e.g. Longsword +1"
			/>
		</div>
		<div>
			<label for="new-item-desc" class="mb-1 block text-xs font-medium text-base-content/75">
				Description
			</label>
			<textarea
				id="new-item-desc"
				bind:value={newItemDescription}
				class="textarea textarea-bordered w-full text-sm"
				rows="3"
				placeholder="Properties, weight, or notes..."
			></textarea>
		</div>
	</div>
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showCreateItem = false)}>Cancel</button>
		<button class="btn btn-primary btn-sm" disabled={!newItemName.trim()} on:click={createItem}>
			Create Item
		</button>
	</div>
</Modal>

<Modal
	show={showAddToStore}
	title="Stock in Store: {selectedItem?.name ?? ''}"
	onClose={() => (showAddToStore = false)}
>
	<div class="grid grid-cols-2 gap-3">
		<div>
			<label for="store-price" class="mb-1 block text-xs font-medium text-base-content/75">
				Price (GP)
			</label>
			<input
				id="store-price"
				type="number"
				min="0"
				bind:value={storePrice}
				class="input input-bordered input-sm w-full stat-num"
			/>
		</div>
		<div>
			<label for="store-qty" class="mb-1 block text-xs font-medium text-base-content/75">
				Quantity (-1 = Unlimited)
			</label>
			<input
				id="store-qty"
				type="number"
				min="-1"
				bind:value={storeQuantity}
				class="input input-bordered input-sm w-full stat-num"
			/>
		</div>
	</div>
	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showAddToStore = false)}>Cancel</button>
		<button class="btn btn-primary btn-sm" on:click={addToStore}>Add to Store</button>
	</div>
</Modal>
