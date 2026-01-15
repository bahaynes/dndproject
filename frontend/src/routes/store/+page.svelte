<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
	import type { StoreItem, Character } from '$lib/types';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Modal from '$lib/components/Modal.svelte';

	let storeItems: StoreItem[] = [];
	let character: Character | null = null;
	let loading = true;
	let error = '';
	let successMessage = '';

	let selectedItem: StoreItem | null = null;
	let purchaseQuantity = 1;
	let showPurchaseConfirm = false;

	onMount(async () => {
		await Promise.all([fetchStoreItems(), fetchCharacter()]);
	});

	async function fetchStoreItems() {
		try {
			const authState = get(auth);
			const res = await fetch(`${API_BASE_URL}/store/items/`, {
				headers: {
					Authorization: `Bearer ${authState.token}`
				}
			});
			if (res.ok) {
				storeItems = await res.json();
			}
		} catch (e) {
			console.error('Failed to fetch store items', e);
		}
	}

	async function fetchCharacter() {
		loading = true;
		try {
			const authState = get(auth);
			const charId = authState.user?.active_character?.id;
			if (!charId) return;

			const res = await fetch(`${API_BASE_URL}/characters/${charId}`, {
				headers: {
					Authorization: `Bearer ${authState.token}`
				}
			});
			if (res.ok) {
				character = await res.json();
			}
		} catch (e) {
			console.error('Failed to fetch character', e);
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
		if (!selectedItem || !character) return;

		error = '';
		successMessage = '';

		try {
			const authState = get(auth);
			const res = await fetch(
				`${API_BASE_URL}/store/items/${selectedItem.id}/purchase?quantity=${purchaseQuantity}`,
				{
					method: 'POST',
					headers: {
						Authorization: `Bearer ${authState.token}`
					}
				}
			);

			if (res.ok) {
				successMessage = `Successfully purchased ${purchaseQuantity}x ${selectedItem.item.name}!`;
				showPurchaseConfirm = false;
				await Promise.all([fetchStoreItems(), fetchCharacter()]);

				// Clear success message after 5s
				setTimeout(() => (successMessage = ''), 5000);
			} else {
				const errData = await res.json();
				error = errData.detail || 'Purchase failed.';
			}
		} catch (e) {
			error = 'An error occurred during purchase.';
		}
	}
</script>

<div class="container mx-auto max-w-5xl p-4">
	<div
		class="border-base-content/10 mb-8 flex flex-col items-start justify-between gap-4 border-b pb-4 md:flex-row md:items-center"
	>
		<div>
			<h1 class="text-primary text-4xl font-[var(--font-cinzel)] font-bold">Company Store</h1>
			<p class="text-sm opacity-60">Trade your hard-earned Scrip for valuable equipment.</p>
		</div>

		{#if character}
			<div class="stats border-primary/20 bg-base-200 border shadow">
				<div class="stat px-4 py-2">
					<div class="stat-title text-primary text-[10px] font-bold uppercase">Your Balance</div>
					<div class="stat-value text-primary text-2xl">
						{character.stats.scrip} <span class="text-xs">Scrip</span>
					</div>
				</div>
			</div>
		{/if}
	</div>

	{#if error}
		<div class="alert alert-error mb-6 shadow-lg">
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
		<div class="alert alert-success mb-6 shadow-lg">
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
					class="card bg-base-100 border-base-content/10 hover:border-primary/50 group border shadow-xl transition-all"
				>
					<div class="card-body">
						<div class="mb-2 flex items-start justify-between">
							<h2 class="card-title text-xl font-bold">{item.item.name}</h2>
							<div class="badge badge-primary font-bold">{item.price} Scrip</div>
						</div>

						<p class="mb-4 line-clamp-2 h-12 text-sm opacity-70">
							{item.item.description || 'No description provided.'}
						</p>

						<div class="mt-auto flex items-center justify-between">
							<div class="text-xs">
								{#if item.quantity_available > 0}
									<span class="text-success font-bold">In Stock: {item.quantity_available}</span>
								{:else}
									<span class="text-error font-bold">Out of Stock</span>
								{/if}
							</div>

							<div class="card-actions">
								<button
									class="btn btn-sm btn-primary"
									disabled={item.quantity_available <= 0 ||
										(character && character.stats.scrip < item.price)}
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
					<span class="label-text-alt opacity-50"
						>Total Price: {selectedItem.price * purchaseQuantity} Scrip</span
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
						class="input input-sm input-bordered w-full text-center"
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

			{#if character && character.stats.scrip < selectedItem.price * purchaseQuantity}
				<p class="text-error animate-pulse text-sm font-bold">Insufficient Scrip!</p>
			{/if}
		</div>
	{/if}

	<div slot="action">
		<button class="btn btn-ghost" on:click={() => (showPurchaseConfirm = false)}>Cancel</button>
		<button
			class="btn btn-primary"
			disabled={!selectedItem ||
				!character ||
				character.stats.scrip < selectedItem.price * purchaseQuantity}
			on:click={handlePurchase}
		>
			Confirm
		</button>
	</div>
</Modal>
