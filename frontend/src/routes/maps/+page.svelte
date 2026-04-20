<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import HexGrid from '$lib/components/HexGrid.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import { getFactionBadgeStyle } from '$lib/utils/terrainColors';

	// Minimal types for map view
	interface HexData {
		q: number;
		r: number;
		terrain: string;
		is_discovered: boolean;
		linked_location_name?: string;
		linked_mission_id?: number;
		linked_mission?: any;
		hex_state?: string;
		controlling_faction?: string | null;
		player_notes?: Array<{ author_character_id: number; text: string; created_at: string }>;
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
	let noteDraft = '';
	let submittingNote = false;

	onMount(async () => {
		isAdmin = $auth.user?.role === 'admin';
		try {
			maps = await api('GET', '/maps/');
		} catch (e) {}
		if (maps.length > 0) activeMap = maps[0];
		loading = false;
	});

	function handleHexClick(e: CustomEvent) {
		const { q, r } = e.detail;
		if (activeMap) {
			const hex = activeMap.hexes.find((h) => h.q === q && h.r === r);
			if (hex && hex.is_discovered) {
				selectedHex = hex;
				noteDraft = '';
			} else {
				selectedHex = null;
			}
		}
	}

	async function submitNote() {
		if (!selectedHex || !activeMap || !noteDraft.trim()) return;
		submittingNote = true;
		try {
			const updated = await api(
				'POST',
				`/maps/${activeMap.id}/hexes/${selectedHex.q}/${selectedHex.r}/notes`,
				{ text: noteDraft }
			);
			const idx = activeMap.hexes.findIndex(
				(h) => h.q === selectedHex!.q && h.r === selectedHex!.r
			);
			if (idx !== -1) {
				activeMap.hexes[idx] = { ...activeMap.hexes[idx], player_notes: updated.player_notes };
				selectedHex = { ...selectedHex, player_notes: updated.player_notes };
				activeMap.hexes = [...activeMap.hexes];
			}
			noteDraft = '';
		} catch (e) {
			console.error('Failed to submit note', e);
		} finally {
			submittingNote = false;
		}
	}
</script>

<div class="flex h-[calc(100vh-64px)] flex-col">
	{#if maps.length > 1}
		<div class="flex gap-2 overflow-x-auto border-b border-base-300 bg-base-200 p-2">
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
				class="absolute top-4 left-4 z-10 max-w-xs rounded-xl border border-base-content/10 bg-base-100/90 p-4 shadow-lg backdrop-blur"
			>
				<h2 class="text-2xl font-[var(--font-cinzel)] font-bold">{activeMap.name}</h2>
				<p class="mt-1 text-xs text-base-content/70">
					Explore the world. Discovered areas are shown in color.
				</p>

				<div class="mt-4 rounded bg-base-200 p-2 font-mono text-xs">
					Left Click: Select<br />
					Drag: Pan Map<br />
					Scroll: Zoom
				</div>

				{#if isAdmin}
					<div class="mt-4 border-t border-base-content/10 pt-4">
						<a href="/admin/maps" class="btn w-full btn-outline btn-sm">Open Map Editor</a>
					</div>
				{/if}
			</div>

			{#if selectedHex}
				<div
					class="absolute bottom-4 left-4 z-10 w-80 rounded-xl border border-base-content/10 bg-base-100/90 p-4 shadow-lg backdrop-blur"
				>
					<div class="flex items-center justify-between">
						<h3 class="text-xl font-[var(--font-cinzel)] font-bold">
							{selectedHex.linked_location_name || 'Wilderness'}
						</h3>
						<button class="btn btn-ghost btn-xs" on:click={() => (selectedHex = null)}>✕</button>
					</div>

					<div class="mt-4 flex flex-col gap-2">
						<div class="flex flex-wrap items-center gap-2">
							<span class="text-xs font-bold text-base-content/60 uppercase">Terrain:</span>
							<span class="badge badge-outline border-primary/30 text-sm capitalize"
								>{selectedHex.terrain}</span
							>
							{#if selectedHex.hex_state && selectedHex.hex_state !== 'wilderness'}
								<span class="badge badge-outline text-xs capitalize"
									>{selectedHex.hex_state.replace('_', ' ')}</span
								>
							{/if}
							{#if selectedHex.controlling_faction}
								<span
									class="badge text-xs"
									style={getFactionBadgeStyle(selectedHex.controlling_faction)}
									>{selectedHex.controlling_faction}</span
								>
							{/if}
						</div>

						{#if selectedHex.linked_mission_id}
							<div class="mt-2 rounded-lg border border-primary/20 bg-primary/5 p-3">
								<span class="mb-1 block text-[10px] font-bold text-primary uppercase"
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

						{#if selectedHex.player_notes && selectedHex.player_notes.length > 0}
							<div class="mt-2 border-t border-base-content/10 pt-2">
								<span class="text-xs font-bold text-base-content/60 uppercase">Notes left here</span
								>
								<div class="mt-1 flex flex-col gap-1">
									{#each selectedHex.player_notes as note}
										<div class="rounded bg-base-200/60 p-2 text-xs">
											{note.text}
											<span class="ml-1 text-base-content/55"
												>— {new Date(note.created_at).toLocaleDateString()}</span
											>
										</div>
									{/each}
								</div>
							</div>
						{/if}

						<div class="mt-2 border-t border-base-content/10 pt-2">
							<span class="text-xs font-bold text-base-content/60 uppercase">Leave a Note</span>
							<textarea
								class="textarea-bordered textarea mt-1 w-full text-xs"
								rows="2"
								placeholder="Mark what you found here..."
								bind:value={noteDraft}
							></textarea>
							<button
								class="btn mt-1 w-full btn-outline btn-xs"
								disabled={!noteDraft.trim() || submittingNote}
								on:click={submitNote}
							>
								{submittingNote ? 'Posting...' : 'Post Note'}
							</button>
						</div>
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
			<div class="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-base-100">
				<p class="text-base-content/60 italic">
					Designating coordinates... No maps found for this campaign.
				</p>
				{#if isAdmin}
					<a href="/admin/maps" class="btn btn-sm btn-primary">Create a Map</a>
				{/if}
			</div>
		{/if}
	</div>
</div>
