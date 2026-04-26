<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { StoreItem } from '$lib/types';
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

	onMount(async () => {
		await fetchStoreItems();
	});

	async function fetchStoreItems() {
		loading = true;
		try {
			storeItems = await api('GET', '/store/items/');
		} catch (e) {
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
		if (!selectedItem || !activeCharacterId) return;
		error = '';
		successMessage = '';
		try {
			await api('POST', `/store/items/${selectedItem.id}/purchase?quantity=${purchaseQuantity}`);
			successMessage = `Successfully purchased ${purchaseQuantity}x ${selectedItem.item.name}!`;
			showPurchaseConfirm = false;
			await fetchStoreItems();
			setTimeout(() => (successMessage = ''), 5000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Purchase failed.';
		}
	}
</script>

<div class="container mx-auto max-w-5xl p-4">
	<div
		class="mb-8 flex flex-col items-start justify-between gap-4 border-b border-base-content/10 pb-4 md:flex-row md:items-center"
	>
		<div>
			<h1 class="text-4xl font-[var(--font-cinzel)] font-bold text-primary">Company Store</h1>
			<p class="text-sm text-base-content/65">
				Acquire equipment and supplies. Prices in GP.
			</p>
		</div>

		{#if activeCharacter}
			<div class="stats border border-primary/20 bg-base-200 shadow">
				<div class="stat px-4 py-2">
					<div class="stat-title text-[10px] font-bold text-primary uppercase">Your Gold</div>
					<div class="stat-value text-2xl text-primary">
						{characterGold} <span class="text-xs">GP</span>
					</div>
				</div>
			</div>
		{/if}
	</div>

	{#if error}
		<div class="mb-6 alert alert-error shadow-lg">
			<div>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-6 w-6 flex-shrink-0 stroke-current"
					fill="none"
					viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
					/></svg
				>
				<span>{error}</span>
			</div>
		</div>
	{/if}

	{#if successMessage}
		<div class="mb-6 alert alert-success shadow-lg">
			<div>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-6 w-6 flex-shrink-0 stroke-current"
					fill="none"
					viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
					/></svg
				>
				<span>{successMessage}</span>
			</div>
		</div>
	{/if}

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else if storeItems.length === 0}
		<div class="card bg-base-200 p-12 text-center opacity-70">
			<h2 class="text-xl font-bold">The store shelves are empty.</h2>
			<p>The quartermaster hasn't stocked any items for this campaign yet.</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
			{#each storeItems as item}
				<div
					class="group card border border-base-content/10 bg-base-100 shadow-xl transition-all hover:border-primary/50"
				>
					<div class="card-body">
						<div class="mb-2 flex items-start justify-between">
							<h2 class="card-title text-xl font-bold">{item.item.name}</h2>
							<div class="badge font-bold badge-primary">{item.price} GP</div>
						</div>

						<p class="mb-4 line-clamp-2 h-12 text-sm text-base-content/70">
							{item.item.description || 'No description provided.'}
						</p>

						<div class="mt-auto flex items-center justify-between">
							<div class="text-xs">
								{#if item.quantity_available > 0}
									<span class="font-bold text-success">In Stock: {item.quantity_available}</span>
								{:else}
									<span class="font-bold text-warning">Out of Stock</span>
								{/if}
							</div>

							<div class="card-actions">
								<button
									class="btn btn-sm btn-primary"
									disabled={item.quantity_available <= 0 || !activeCharacterId}
									on:click={() => openPurchaseModal(item)}
								>
									Purchase
								</button>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Purchase Confirmation Modal -->
<Modal
	show={showPurchaseConfirm}
	title="Confirm Purchase"
	onClose={() => (showPurchaseConfirm = false)}
>
	{#if selectedItem}
		<div class="text-center">
			<p class="mb-4 text-lg">
				Are you sure you want to purchase <strong>{selectedItem.item.name}</strong>?
			</p>

			<div class="form-control mx-auto mb-6 w-full max-w-xs">
				<label class="label">
					<span class="label-text">How many?</span>
					<span class="label-text-alt text-base-content/65"
						>Total Cost: {selectedItem.price * purchaseQuantity} GP</span
					>
				</label>
				<div class="flex items-center gap-2">
					<button
						class="btn btn-square btn-sm"
						on:click={() => (purchaseQuantity = Math.max(1, purchaseQuantity - 1))}>-</button
					>
					<input
						type="number"
						bind:value={purchaseQuantity}
						min="1"
						max={selectedItem.quantity_available}
						class="input-bordered input input-sm w-full text-center"
					/>
					<button
						class="btn btn-square btn-sm"
						on:click={() =>
							(purchaseQuantity = Math.min(
								selectedItem?.quantity_available || 1,
								purchaseQuantity + 1
							))}>+</button
					>
				</div>
			</div>

			{#if characterGold < selectedItem.price * purchaseQuantity}
				<p class="animate-pulse text-sm font-bold text-warning">Not enough gold.</p>
			{/if}
		</div>
	{/if}

	<div slot="action">
		<button class="btn btn-ghost" on:click={() => (showPurchaseConfirm = false)}>Cancel</button>
		<button
			class="btn btn-primary"
			disabled={!selectedItem || !activeCharacterId || characterGold < (selectedItem?.price ?? 0) * purchaseQuantity}
			on:click={handlePurchase}
		>
			Confirm
		</button>
	</div>
</Modal>
