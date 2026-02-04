<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
	import HexGrid from '$lib/components/HexGrid.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	// Minimal types for map view
	interface HexData {
		q: number;
		r: number;
		terrain: string;
		is_discovered: boolean;
		linked_location_name?: string;
		linked_mission_id?: number;
		linked_mission?: any;
	}

	interface MapData {
		id: number;
		name: string;
		hex_size: number;
		hexes: HexData[];
	}

	let maps: MapData[] = [];
	let activeMap: MapData | null = null;
	let loading = true;
	let error = '';
	let isAdmin = false;
	let selectedHex: HexData | null = null;

	onMount(async () => {
		// Check admin
		const authState = get(auth);
		isAdmin = authState.user?.role === 'admin';

		await fetchMaps();

		if (maps.length > 0) {
			activeMap = maps[0];
		}

		loading = false;
	});

	async function fetchMaps() {
		try {
			const res = await fetch(`${API_BASE_URL}/maps/`, {
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) {
				maps = await res.json();
			}
		} catch (e) {
			console.error('Failed to fetch maps', e);
			// Do not block dummy generation for dev testing
		}
	}

	function handleHexClick(e: CustomEvent) {
		const { q, r } = e.detail;
		if (activeMap) {
			const hex = activeMap.hexes.find((h) => h.q === q && h.r === r);
			if (hex && hex.is_discovered) {
				selectedHex = hex;
			} else {
				selectedHex = null;
			}
		}
	}
</script>

<div class="flex h-[calc(100vh-64px)] flex-col">
	{#if maps.length > 1}
		<div class="border-base-300 bg-base-200 flex gap-2 overflow-x-auto border-b p-2">
			{#each maps as map}
				<button
					class="btn btn-sm {activeMap?.id === map.id ? 'btn-primary' : 'btn-ghost'}"
					on:click={() => (activeMap = map)}
				>
					{map.name}
				</button>
			{/each}
		</div>
	{/if}

	<div class="relative flex-grow overflow-hidden bg-neutral-900">
		{#if loading}
			<div class="absolute inset-0 flex items-center justify-center">
				<LoadingSpinner />
			</div>
		{:else if activeMap}
			<div
				class="bg-base-100/90 border-base-content/10 absolute left-4 top-4 z-10 max-w-xs rounded-xl border p-4 shadow-lg backdrop-blur"
			>
				<h2 class="text-2xl font-[var(--font-cinzel)] font-bold">{activeMap.name}</h2>
				<p class="mt-1 text-xs opacity-70">
					Explore the world. Discovered areas are shown in color.
				</p>

				<div class="bg-base-200 mt-4 rounded p-2 font-mono text-xs">
					Left Click: Select<br />
					Drag: Pan Map<br />
					Scroll: Zoom
				</div>

				{#if isAdmin}
					<div class="border-base-content/10 mt-4 border-t pt-4">
						<a href="/admin/maps" class="btn btn-sm btn-outline w-full">Open Map Editor</a>
					</div>
				{/if}
			</div>

			{#if selectedHex}
				<div
					class="bg-base-100/90 border-base-content/10 absolute bottom-4 left-4 z-10 w-80 rounded-xl border p-4 shadow-lg backdrop-blur"
				>
					<div class="flex items-center justify-between">
						<h3 class="text-xl font-[var(--font-cinzel)] font-bold">
							{selectedHex.linked_location_name || 'Wilderness'}
						</h3>
						<button class="btn btn-xs btn-ghost" on:click={() => (selectedHex = null)}>✕</button>
					</div>

					<div class="mt-4 flex flex-col gap-2">
						<div class="flex items-center gap-2">
							<span class="text-neutral-content text-xs font-bold uppercase opacity-50"
								>Terrain:</span
							>
							<span class="badge badge-outline border-primary/30 text-sm capitalize"
								>{selectedHex.terrain}</span
							>
						</div>

						{#if selectedHex.linked_mission_id}
							<div class="border-primary/20 bg-primary/5 mt-2 rounded-lg border p-3">
								<span class="text-primary mb-1 block text-[10px] font-bold uppercase"
									>Linked Mission</span
								>
								<div class="flex items-center justify-between gap-2">
									<p class="truncate text-sm font-semibold">
										{selectedHex.linked_mission?.name || 'Unknown Mission'}
									</p>
									<a href="/missions" class="btn btn-xs btn-primary">Details</a>
								</div>
							</div>
						{/if}
					</div>
				</div>
			{/if}

			<HexGrid
				hexes={activeMap.hexes}
				hexSize={activeMap.hex_size}
				{selectedHex}
				on:click={handleHexClick}
			/>
		{:else}
			<div class="text-error bg-base-100 absolute inset-0 flex items-center justify-center italic">
				Designating coordinates... No maps found for this campaign.
			</div>
		{/if}
	</div>
</div>
