<script lang="ts">
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import type { Character, InventoryItem } from '$lib/types';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let character: Character | null = null;
	let loading = true;
	let error = '';

	// Reactive trigger
	$: if ($auth.user?.active_character?.id) {
		fetchInventory();
	}

	async function fetchInventory() {
		loading = true;
		error = '';
		const characterId = $auth.user?.active_character?.id;
		if (!characterId) {
			error = 'No character found.';
			loading = false;
			return;
		}
		try {
			character = await api('GET', `/characters/${characterId}`);
		} catch (e) {
			error = 'Failed to load inventory.';
		} finally {
			loading = false;
		}
	}

	async function removeItem(inventoryItem: InventoryItem) {
		if (!character) return;
		try {
			await api('DELETE', `/characters/${character.id}/inventory/${inventoryItem.id}`);
			await fetchInventory();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to remove item.';
		}
	}
</script>

<div class="container mx-auto max-w-4xl p-4">
	<div class="mb-8 flex flex-col items-center justify-between gap-4 sm:flex-row">
		<div>
			<h1 class="text-primary text-4xl font-[var(--font-cinzel)] font-bold tracking-tight">
				Inventory
			</h1>
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
		<button class="btn btn-primary" on:click={fetchInventory}>Retry</button>
	{:else if character}
		{#if character.inventory.length === 0}
			<div
				class="bg-base-200 border-base-content/20 rounded-2xl border-2 border-dashed p-12 text-center"
			>
				<span class="mb-4 block text-6xl">🎒</span>
				<h2 class="mb-2 text-2xl font-bold">Backpack is Empty</h2>
				<p class="mb-6 opacity-70">
					You haven't acquired any items yet. Venture out on missions or visit the local store!
				</p>
				<a href="/store" class="btn btn-primary px-8">Browse the Store</a>
			</div>
		{:else}
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
				{#each character.inventory as invItem}
					<div
						class="card bg-base-100 border-base-content/10 hover:border-primary/30 group border shadow-md transition-all"
					>
						<div class="card-body">
							<div class="flex items-start justify-between">
								<div>
									<h3 class="card-title text-xl font-bold">{invItem.item.name}</h3>
									<div class="badge badge-primary badge-sm mt-1">Qty: {invItem.quantity}</div>
								</div>
								<button
									class="btn btn-circle btn-xs btn-ghost text-error opacity-0 transition-opacity group-hover:opacity-100"
									title="Remove Item"
									on:click={() => removeItem(invItem)}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-4 w-4"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
										><path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M6 18L18 6M6 6l12 12"
										/></svg
									>
								</button>
							</div>
							<p class="mt-2 text-sm opacity-70">
								{invItem.item.description || 'No description available.'}
							</p>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>
