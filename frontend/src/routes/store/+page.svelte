<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { StoreItem } from '$lib/types';
	import { ADVENTURERS_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';

	let storeItems: StoreItem[] = [];
	let loading = true;
	let error = '';
	let successMessage = '';

	let selectedItem: StoreItem | null = null;
	let purchaseQuantity = 1;
	let showPurchaseConfirm = false;

	$: activeCharacter = $auth.user?.active_character;
	$: activeCharacterId = activeCharacter?.id;
	$: characterGold = activeCharacter?.stats?.gold ?? 0;

	onMount(fetchStoreItems);

	async function fetchStoreItems() {
		loading = true;
		try {
			storeItems = await api('GET', '/store/items/');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load store items.';
		} finally {
			loading = false;
		}
	}

	function openPurchaseModal(item: StoreItem) {
		selectedItem = item;
		purchaseQuantity = 1;
		showPurchaseConfirm = true;
	}

	async function handlePurchase() {
		if (!selectedItem || !activeCharacterId || !activeCharacter) return;
		error = '';
		successMessage = '';
		const totalCost = selectedItem.price * purchaseQuantity;
		try {
			await api('POST', `/store/items/${selectedItem.id}/purchase?quantity=${purchaseQuantity}`);
			successMessage = `Purchased ${purchaseQuantity}x ${selectedItem.item.name} for ${totalCost} GP.`;
			// Update local character gold immediately
			if ($auth.user && $auth.token && activeCharacter.stats) {
				const updatedChar = {
					...activeCharacter,
					stats: { ...activeCharacter.stats, gold: Math.max(0, activeCharacter.stats.gold - totalCost) }
				};
				auth.login({ ...$auth.user, active_character: updatedChar }, $auth.token, $auth.campaign ?? undefined);
			}
			showPurchaseConfirm = false;
			await fetchStoreItems();
			setTimeout(() => (successMessage = ''), 5000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Purchase failed.';
		}
	}
</script>

<div class="page-container">
	<SubNav items={ADVENTURERS_NAV} />

	<PageHeader
		title="Quartermaster Store"
		subtitle="Acquire equipment, consumables, and supplies using Gold (GP)."
	>
		<div slot="actions">
			{#if activeCharacter}
				<div class="panel px-4 py-2 text-right">
					<p class="section-label">Available Gold</p>
					<p class="text-lg font-semibold text-primary stat-num">{characterGold} GP</p>
				</div>
			{/if}
		</div>
	</PageHeader>

	{#if error}
		<div class="alert alert-error mb-6 text-sm">{error}</div>
	{/if}
	{#if successMessage}
		<div class="alert alert-success mb-6 text-sm">{successMessage}</div>
	{/if}

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else if storeItems.length === 0}
		<div class="panel p-12 text-center">
			<p class="text-base font-medium text-base-content/75">The store shelves are empty.</p>
			<p class="mt-1 text-sm text-base-content/50">The DM hasn't stocked any items for this campaign yet.</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
			{#each storeItems as item}
				<article class="panel panel-interactive flex flex-col p-5">
					<div class="mb-2 flex items-start justify-between gap-2">
						<h2 class="text-base font-semibold text-base-content">{item.item.name}</h2>
						<span class="badge badge-outline border-primary/40 text-primary badge-sm shrink-0 stat-num">
							{item.price} GP
						</span>
					</div>

					<p class="mb-4 line-clamp-3 flex-1 text-xs text-base-content/70">
						{item.item.description || 'No description provided.'}
					</p>

					<div class="mt-auto flex items-center justify-between border-t border-base-content/10 pt-3">
						<span class="text-xs stat-num {item.quantity_available === 0 ? 'text-warning' : 'text-base-content/60'}">
							{#if item.quantity_available === -1}
								Unlimited stock
							{:else if item.quantity_available > 0}
								{item.quantity_available} in stock
							{:else}
								Out of stock
							{/if}
						</span>

						<button
							class="btn btn-primary btn-xs"
							disabled={item.quantity_available === 0 || !activeCharacterId}
							on:click={() => openPurchaseModal(item)}
						>
							Purchase
						</button>
					</div>
				</article>
			{/each}
		</div>
	{/if}
</div>

<Modal show={showPurchaseConfirm} title="Confirm Purchase" onClose={() => (showPurchaseConfirm = false)}>
	{#if selectedItem}
		<div class="space-y-4">
			<p class="text-sm text-base-content/85">
				Purchase <strong class="text-primary">{selectedItem.item.name}</strong>?
			</p>

			<div>
				<div class="mb-1 flex justify-between text-xs text-base-content/70">
					<label for="purchase-qty">Quantity</label>
					<span class="stat-num">Total: {selectedItem.price * purchaseQuantity} GP</span>
				</div>
				<div class="flex items-center gap-2">
					<button
						class="btn btn-square btn-sm"
						on:click={() => (purchaseQuantity = Math.max(1, purchaseQuantity - 1))}
					>
						-
					</button>
					<input
						id="purchase-qty"
						type="number"
						bind:value={purchaseQuantity}
						min="1"
						max={selectedItem.quantity_available === -1 ? 99 : selectedItem.quantity_available}
						class="input input-bordered input-sm flex-1 text-center stat-num"
					/>
					<button
						class="btn btn-square btn-sm"
						on:click={() =>
							(purchaseQuantity = Math.min(
								selectedItem?.quantity_available === -1
									? 99
									: selectedItem?.quantity_available || 1,
								purchaseQuantity + 1
							))}
					>
						+
					</button>
				</div>
			</div>

			{#if characterGold < selectedItem.price * purchaseQuantity}
				<p class="text-xs font-medium text-error">Insufficient Gold ({characterGold} GP available).</p>
			{/if}
		</div>
	{/if}

	<div slot="action">
		<button class="btn btn-ghost btn-sm" on:click={() => (showPurchaseConfirm = false)}>Cancel</button>
		<button
			class="btn btn-primary btn-sm"
			disabled={!selectedItem ||
				!activeCharacterId ||
				characterGold < (selectedItem?.price ?? 0) * purchaseQuantity}
			on:click={handlePurchase}
		>
			Confirm Purchase
		</button>
	</div>
</Modal>
