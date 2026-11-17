<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { api } from '$lib/api';
	import HexGrid from '$lib/components/HexGrid.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import { getFactionBadgeStyle } from '$lib/utils/terrainColors';
	import { fetchAuthedLayerUrl, type LayerBounds, type MapLayerMode } from '$lib/utils/mapLayers';

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
		topo_image_url?: string | null;
		satellite_image_url?: string | null;
		layer_bounds?: LayerBounds | null;
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
	let seatedSessions: { id: number; name: string; session_date: string }[] = [];
	let proposeSessionId: number | null = null;
	let proposing = false;
	let proposeMsg = '';
	let layerMode: MapLayerMode = 'tactical';
	let showDangerTiers = false;
	let layerUrls: Record<string, string> = {};

	async function ensureLayerLoaded(map: MapData | null, mode: MapLayerMode) {
		if (!map || mode === 'tactical') return;
		const apiPath = mode === 'topo' ? map.topo_image_url : map.satellite_image_url;
		if (!apiPath) return;
		const cacheKey = `${map.id}:${mode}`;
		if (layerUrls[cacheKey]) return;
		try {
			const objUrl = await fetchAuthedLayerUrl(apiPath);
			layerUrls = { ...layerUrls, [cacheKey]: objUrl };
		} catch (e) {
			console.error('Failed to load map layer', e);
		}
	}

	function selectMap(map: MapData) {
		activeMap = map;
		selectedHex = null;
		if (map.topo_image_url) {
			layerMode = 'topo';
			ensureLayerLoaded(map, 'topo');
		} else if (map.satellite_image_url) {
			layerMode = 'satellite';
			ensureLayerLoaded(map, 'satellite');
		} else {
			layerMode = 'tactical';
		}
	}

	function setLayerMode(mode: MapLayerMode) {
		layerMode = mode;
		ensureLayerLoaded(activeMap, mode);
	}

	$: activeBaseLayerUrl =
		activeMap && layerMode !== 'tactical' ? layerUrls[`${activeMap.id}:${layerMode}`] || null : null;

	onDestroy(() => {
		Object.values(layerUrls).forEach((u) => URL.revokeObjectURL(u));
	});

	onMount(async () => {
		isAdmin = $auth.user?.role === 'admin';
		const [mapRes, sessRes] = await Promise.all([
			api('GET', '/maps/').catch(() => []),
			api('GET', '/sessions/').catch(() => [])
		]);
		maps = mapRes ?? [];
		if (maps.length > 0) selectMap(maps[0]);
		seatedSessions = (sessRes ?? []).filter(
			(s: any) =>
				s.status !== 'Completed' &&
				s.status !== 'Cancelled' &&
				s.players?.some((p: any) => p.owner_id === $auth.user?.id)
		);
		proposeSessionId = seatedSessions[0]?.id ?? null;
		loading = false;
	});

	function handleHexClick(e: CustomEvent) {
		const { q, r } = e.detail;
		if (activeMap) {
			const hex = activeMap.hexes.find((h) => h.q === q && h.r === r);
			if (hex && hex.is_discovered) {
				selectedHex = hex;
				noteDraft = '';
				proposeMsg = '';
			} else {
				selectedHex = null;
			}
		}
	}

	async function proposeSelectedHex() {
		if (!selectedHex || !proposeSessionId) return;
		proposing = true;
		proposeMsg = '';
		try {
			const payload = selectedHex.linked_mission_id
				? { session_id: proposeSessionId, mission_id: selectedHex.linked_mission_id }
				: { session_id: proposeSessionId, hex_id: (selectedHex as any).id };
			await api('POST', '/sessions/proposals', payload);
			proposeMsg = 'Proposed for session!';
		} catch (e) {
			proposeMsg = e instanceof Error ? e.message : 'Failed to propose.';
		} finally {
			proposing = false;
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

<div class="flex h-[calc(100vh-56px)] flex-col">
	{#if maps.length > 1}
		<div class="flex gap-2 overflow-x-auto border-b border-base-300 bg-base-200 px-4 py-2">
			{#each maps as map}
				<button
					class="btn btn-sm {activeMap?.id === map.id ? 'btn-primary' : 'btn-ghost'}"
					on:click={() => selectMap(map)}
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

				<div class="mt-3 flex flex-wrap gap-1">
					{#if activeMap.topo_image_url}
						<button
							class="btn btn-xs {layerMode === 'topo' ? 'btn-primary' : 'btn-outline'}"
							on:click={() => setLayerMode('topo')}
						>
							Topo
						</button>
					{/if}
					{#if activeMap.satellite_image_url}
						<button
							class="btn btn-xs {layerMode === 'satellite' ? 'btn-primary' : 'btn-outline'}"
							on:click={() => setLayerMode('satellite')}
						>
							Satellite
						</button>
					{/if}
					<button
						class="btn btn-xs {layerMode === 'tactical' ? 'btn-primary' : 'btn-outline'}"
						on:click={() => setLayerMode('tactical')}
					>
						Tactical
					</button>
					<button
						class="btn btn-xs {showDangerTiers ? 'btn-warning' : 'btn-ghost'}"
						on:click={() => (showDangerTiers = !showDangerTiers)}
					>
						T1–T3 Rings
					</button>
				</div>

				<div class="mt-3 rounded bg-base-200 p-2 font-mono text-xs">
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
					class="absolute bottom-4 left-4 z-10 w-80 max-w-[calc(100vw-2rem)] rounded-xl border border-base-content/10 bg-base-100/90 p-4 shadow-lg backdrop-blur"
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
							<div class="mt-2 rounded-lg border border-primary/25 bg-primary/5 p-3">
								<span class="mb-1 block text-[10px] font-bold text-primary uppercase">
									★ Quest Hook at This Hex
								</span>
								<p class="text-sm font-semibold text-base-content">
									{selectedHex.linked_mission?.name || 'Posted Quest'}
								</p>
								{#if selectedHex.linked_mission?.tier}
									<span class="badge badge-outline badge-xs mt-1">{selectedHex.linked_mission.tier}</span>
								{/if}
								{#if selectedHex.linked_mission?.description}
									<p class="mt-1.5 line-clamp-3 text-xs text-base-content/75">
										{selectedHex.linked_mission.description}
									</p>
								{/if}
							</div>
						{/if}

						<div class="mt-2 border-t border-base-content/10 pt-2">
							{#if seatedSessions.length > 0}
								<div class="flex items-center gap-2">
									<select class="select select-bordered select-sm min-w-0 flex-1" bind:value={proposeSessionId}>
										{#each seatedSessions as s}
											<option value={s.id}>{s.name}</option>
										{/each}
									</select>
									<button
										class="btn btn-primary btn-sm shrink-0"
										disabled={proposing || !proposeSessionId}
										on:click={proposeSelectedHex}
									>
										{proposing ? '...' : 'Propose'}
									</button>
								</div>
								{#if proposeMsg}
									<p class="mt-1 text-xs text-primary">{proposeMsg}</p>
								{/if}
							{:else}
								<a href="/dashboard" class="btn btn-outline btn-xs w-full">
									Join a Session to Propose →
								</a>
							{/if}
						</div>

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
				baseLayerUrl={activeBaseLayerUrl}
				layerBounds={activeMap.layer_bounds || null}
				{showDangerTiers}
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
