<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';
	import HexGrid from '$lib/components/HexGrid.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import type { Mission } from '$lib/types';
	import { getTerrainColor } from '$lib/utils/terrainColors';
	import {
		EARTH_REGION_PRESETS,
		TRAVEL_SCALES,
		fetchAuthedLayerUrl,
		parseLatLonInput,
		type LayerBounds,
		type MapLayerMode,
		type MapRoute,
		type RouteType,
		type TravelScale
	} from '$lib/utils/mapLayers';

	interface HexData {
		q: number;
		r: number;
		terrain: string;
		is_discovered: boolean;
		linked_location_name?: string;
		linked_mission_id?: number;
		hex_state?: string;
		controlling_faction?: string | null;
		player_notes?: any[];
	}

	interface MapData {
		id: number;
		name: string;
		hex_size: number;
		topo_image_url?: string | null;
		satellite_image_url?: string | null;
		layer_bounds?: LayerBounds | null;
		source_region?: {
			center_lat?: number;
			center_lon?: number;
			travel_scale?: TravelScale;
			min_lat?: number;
			min_lon?: number;
			max_lat?: number;
			max_lon?: number;
		} | null;
		routes?: MapRoute[];
		hexes: HexData[];
	}

	let maps: MapData[] = [];
	let missions: Mission[] = [];
	let activeMap: MapData | null = null;
	let loading = true;
	let layerMode: MapLayerMode = 'tactical';
	let showDangerTiers = false;
	let layerUrls: Record<string, string> = {};

	// Real-Earth Baker State
	let bakeOpen = false;
	let baking = false;
	let bakeError = '';
	let autoSeedTerrain = true;
	let pinInput = `${EARTH_REGION_PRESETS[0].center_lat}, ${EARTH_REGION_PRESETS[0].center_lon}`;
	let travelScale: TravelScale = 'frontier';

	// Editor State
	let selectedHex: HexData | null = null;
	let selectedTool: 'select' | 'paint' | 'fog' | 'route' = 'select';
	let activeTerrain = 'plains';
	let isDirty = false;
	let dirtyHexes: Set<string> = new Set();

	// Route Drawing State
	let draftRouteName = '';
	let draftRouteType: RouteType = 'road';
	let draftRouteHexes: Array<{ q: number; r: number }> = [];
	let savingRoutes = false;

	$: activeDraftRoute =
		selectedTool === 'route' && draftRouteHexes.length >= 2
			? {
					id: 'draft',
					name: draftRouteName || 'Draft',
					type: draftRouteType,
					hexes: draftRouteHexes
				}
			: null;

	const TERRAIN_TYPES = ['Plains', 'Forest', 'Mountain', 'Water', 'Desert', 'Swamp'];
	const HEX_STATES = [
		{ value: 'wilderness', label: 'Wilderness (2h)' },
		{ value: 'claimed_developed', label: 'Claimed & Developed (0.5h)' },
		{ value: 'friendly', label: 'Friendly Controlled (1h)' },
		{ value: 'contested', label: 'Contested (3h)' },
		{ value: 'awakened', label: 'Awakened (variable)' }
	];
	let factionNames: string[] = ['None'];

	async function ensureLayerLoaded(map: MapData | null, mode: MapLayerMode, forceReload = false) {
		if (!map || mode === 'tactical') return;
		const apiPath = mode === 'topo' ? map.topo_image_url : map.satellite_image_url;
		if (!apiPath) return;
		const cacheKey = `${map.id}:${mode}`;
		if (layerUrls[cacheKey] && !forceReload) return;
		if (layerUrls[cacheKey]) URL.revokeObjectURL(layerUrls[cacheKey]);
		try {
			const objUrl = await fetchAuthedLayerUrl(apiPath);
			layerUrls = { ...layerUrls, [cacheKey]: objUrl };
		} catch (e) {
			console.error('Failed to load map layer', e);
		}
	}

	function setLayerMode(mode: MapLayerMode) {
		layerMode = mode;
		ensureLayerLoaded(activeMap, mode);
	}

	function applyPreset(e: Event) {
		const idx = Number((e.target as HTMLSelectElement).value);
		const preset = EARTH_REGION_PRESETS[idx];
		if (!preset) return;
		pinInput = `${preset.center_lat}, ${preset.center_lon}`;
	}

	async function bakeEarthLayers() {
		if (!activeMap) return;
		const parsed = parseLatLonInput(pinInput);
		if (!parsed) {
			bakeError = 'Paste a valid Google Maps lat, lon (e.g. 64.1466, -21.9426)';
			return;
		}
		baking = true;
		bakeError = '';
		try {
			const updated: MapData = await api('POST', `/maps/${activeMap.id}/bake-earth`, {
				center_lat: parsed.lat,
				center_lon: parsed.lon,
				travel_scale: travelScale,
				auto_seed_terrain: autoSeedTerrain
			});
			activeMap = updated;
			maps = maps.map((m) => (m.id === updated.id ? updated : m));
			layerMode = 'topo';
			await ensureLayerLoaded(updated, 'topo', true);
			await ensureLayerLoaded(updated, 'satellite', true);
		} catch (e: any) {
			bakeError = e?.message || 'Failed to bake Earth region';
		} finally {
			baking = false;
		}
	}

	$: activeBaseLayerUrl =
		activeMap && layerMode !== 'tactical' ? layerUrls[`${activeMap.id}:${layerMode}`] || null : null;

	onDestroy(() => {
		Object.values(layerUrls).forEach((u) => URL.revokeObjectURL(u));
	});

	onMount(async () => {
		await Promise.all([fetchMaps(), fetchMissions(), fetchFactions()]);
		if (maps.length > 0) {
			activeMap = maps[0];
			if (activeMap.source_region?.center_lat != null && activeMap.source_region?.center_lon != null) {
				pinInput = `${activeMap.source_region.center_lat}, ${activeMap.source_region.center_lon}`;
			}
			if (activeMap.source_region?.travel_scale) {
				travelScale = activeMap.source_region.travel_scale;
			}
			if (activeMap.topo_image_url) {
				layerMode = 'topo';
				ensureLayerLoaded(activeMap, 'topo');
			}
		}
		loading = false;
	});

	async function fetchFactions() {
		try {
			const res: Array<{ faction_name: string }> = await api('GET', '/factions/');
			factionNames = ['None', ...res.map((f) => f.faction_name)];
		} catch (e) {}
	}

	async function fetchMissions() {
		try {
			missions = await api('GET', '/missions/');
		} catch (e) {}
	}

	async function fetchMaps() {
		try {
			maps = await api('GET', '/maps/');
		} catch (e) {}
	}

	function handleHexClick(e: CustomEvent) {
		if (!activeMap) return;
		const { q, r } = e.detail;
		const hexIndex = activeMap.hexes.findIndex((h) => h.q === q && h.r === r);

		if (hexIndex === -1) return;

		if (selectedTool === 'paint') {
			const newHexes = [...activeMap.hexes];
			newHexes[hexIndex] = { ...newHexes[hexIndex], terrain: activeTerrain };
			activeMap.hexes = newHexes;
			isDirty = true;
			dirtyHexes.add(`${q},${r}`);
		} else if (selectedTool === 'fog') {
			const newHexes = [...activeMap.hexes];
			newHexes[hexIndex] = {
				...newHexes[hexIndex],
				is_discovered: !newHexes[hexIndex].is_discovered
			};
			activeMap.hexes = newHexes;
			isDirty = true;
			dirtyHexes.add(`${q},${r}`);
		} else if (selectedTool === 'select') {
			selectedHex = activeMap.hexes[hexIndex];
		} else if (selectedTool === 'route') {
			const last = draftRouteHexes[draftRouteHexes.length - 1];
			if (!last || last.q !== q || last.r !== r) {
				draftRouteHexes = [...draftRouteHexes, { q, r }];
			}
		}
	}

	async function persistRoutes(nextRoutes: MapRoute[]) {
		if (!activeMap) return;
		savingRoutes = true;
		try {
			const updated: MapData = await api('PUT', `/maps/${activeMap.id}/routes`, {
				routes: nextRoutes
			});
			activeMap = updated;
			maps = maps.map((m) => (m.id === updated.id ? updated : m));
		} catch (e) {
			console.error('Failed to save routes', e);
		} finally {
			savingRoutes = false;
		}
	}

	async function commitDraftRoute() {
		if (!activeMap || draftRouteHexes.length < 2) return;
		const newRoute: MapRoute = {
			id: `route-${Date.now()}`,
			name: draftRouteName.trim() || `${draftRouteType.replace('_', ' ')}`,
			type: draftRouteType,
			hexes: draftRouteHexes
		};
		await persistRoutes([...(activeMap.routes || []), newRoute]);
		draftRouteName = '';
		draftRouteHexes = [];
	}

	async function deleteRoute(id: string) {
		if (!activeMap) return;
		await persistRoutes((activeMap.routes || []).filter((r) => r.id !== id));
	}

	function updateSelectedHex() {
		if (!activeMap || !selectedHex) return;
		const { q, r } = selectedHex;
		const hexIndex = activeMap.hexes.findIndex((h) => h.q === q && h.r === r);
		if (hexIndex === -1) return;

		activeMap.hexes[hexIndex] = { ...selectedHex };
		activeMap.hexes = [...activeMap.hexes];
		isDirty = true;
		dirtyHexes.add(`${selectedHex.q},${selectedHex.r}`);
	}

	function setAllDiscovery(discovered: boolean) {
		if (!activeMap) return;
		const newHexes = activeMap.hexes.map((h) => {
			if (h.is_discovered !== discovered) {
				dirtyHexes.add(`${h.q},${h.r}`);
			}
			return { ...h, is_discovered: discovered };
		});
		activeMap.hexes = newHexes;
		isDirty = true;
	}

	async function saveChanges() {
		if (!activeMap || !isDirty) return;

		let successCount = 0;
		let failCount = 0;

		for (const coordStr of dirtyHexes) {
			const [q, r] = coordStr.split(',').map(Number);
			const hex = activeMap.hexes.find((h) => h.q === q && h.r === r);
			if (!hex) continue;

			try {
				await api('PUT', `/maps/${activeMap.id}/hexes/${q}/${r}`, {
					terrain: hex.terrain,
					is_discovered: hex.is_discovered,
					linked_location_name: hex.linked_location_name,
					linked_mission_id: hex.linked_mission_id,
					notes: (hex as any).notes,
					hex_state: hex.hex_state,
					controlling_faction: hex.controlling_faction ?? null
				});
				successCount++;
			} catch (e) {
				failCount++;
			}
		}

		if (failCount === 0) {
			alert('Map saved successfully!');
			isDirty = false;
			dirtyHexes.clear();
			goto('/maps');
		} else {
			alert(`Map saved with ${failCount} errors.`);
		}
	}
</script>

<div class="flex h-[calc(100vh-64px)]">
	<!-- Sidebar Tools -->
	<div class="flex w-64 flex-col border-r border-base-content/10 bg-base-200 p-4">
		<h2 class="mb-4 text-xl font-[var(--font-cinzel)] font-bold">Map Editor</h2>

		<div class="mb-6 flex flex-col gap-2">
			<span class="text-xs font-bold text-base-content/60 uppercase">Tools</span>
			<div class="join w-full">
				<button
					class="btn join-item btn-xs flex-1 {selectedTool === 'select' ? 'btn-primary' : 'btn-outline'}"
					on:click={() => (selectedTool = 'select')}>Select</button
				>
				<button
					class="btn join-item btn-xs flex-1 {selectedTool === 'paint' ? 'btn-primary' : 'btn-outline'}"
					on:click={() => (selectedTool = 'paint')}>Paint</button
				>
				<button
					class="btn join-item btn-xs flex-1 {selectedTool === 'fog' ? 'btn-primary' : 'btn-outline'}"
					on:click={() => (selectedTool = 'fog')}>Fog</button
				>
				<button
					class="btn join-item btn-xs flex-1 {selectedTool === 'route' ? 'btn-primary' : 'btn-outline'}"
					on:click={() => (selectedTool = 'route')}>Route</button
				>
			</div>
		</div>

		{#if selectedTool === 'paint'}
			<div class="mb-6 flex flex-col gap-2">
				<span class="text-xs font-bold text-base-content/60 uppercase">Palette</span>
				<div class="grid grid-cols-2 gap-2">
					{#each TERRAIN_TYPES as t}
						<button
							class="btn btn-sm {activeTerrain === t.toLowerCase()
								? 'btn-active'
								: 'btn-ghost'} justify-start"
							on:click={() => (activeTerrain = t.toLowerCase())}
						>
							<div
								class="mr-2 h-3 w-3 rounded-full"
								style="background-color: {getTerrainColor(t.toLowerCase())}"
							></div>
							{t}
						</button>
					{/each}
				</div>
			</div>
		{/if}

		{#if selectedTool === 'select' && selectedHex}
			<div class="mt-4 flex flex-col gap-4 border-t border-base-content/10 pt-4">
				<div class="flex items-center justify-between">
					<span class="text-sm font-bold">Hex {selectedHex.q}, {selectedHex.r}</span>
					<button class="btn btn-ghost btn-xs" on:click={() => (selectedHex = null)}>Close</button>
				</div>

				<div class="form-control">
					<label class="label" for="terrain-select"><span class="label-text">Terrain</span></label>
					<select
						id="terrain-select"
						bind:value={selectedHex.terrain}
						on:change={updateSelectedHex}
						class="select-bordered select select-sm"
					>
						{#each TERRAIN_TYPES as t}
							<option value={t.toLowerCase()}>{t}</option>
						{/each}
					</select>
				</div>

				<div class="form-control">
					<label class="label cursor-pointer">
						<span class="label-text">Discovered</span>
						<input
							type="checkbox"
							bind:checked={selectedHex.is_discovered}
							on:change={updateSelectedHex}
							class="checkbox checkbox-sm"
						/>
					</label>
				</div>

				<div class="form-control">
					<label class="label" for="poi-input"><span class="label-text">POI Name</span></label>
					<input
						id="poi-input"
						type="text"
						bind:value={selectedHex.linked_location_name}
						on:input={updateSelectedHex}
						class="input-bordered input input-sm"
						placeholder="Optional"
					/>
				</div>

				<div class="form-control">
					<label class="label" for="mission-link"
						><span class="label-text">Linked Mission</span></label
					>
					<select
						id="mission-link"
						bind:value={selectedHex.linked_mission_id}
						on:change={updateSelectedHex}
						class="select-bordered select select-sm"
					>
						<option value={null}>None</option>
						{#each missions as mission}
							<option value={mission.id}>{mission.name}</option>
						{/each}
					</select>
				</div>

				<div class="form-control">
					<label class="label" for="hex-state-select"
						><span class="label-text">Hex State</span></label
					>
					<select
						id="hex-state-select"
						bind:value={selectedHex.hex_state}
						on:change={updateSelectedHex}
						class="select-bordered select select-sm"
					>
						{#each HEX_STATES as s}
							<option value={s.value}>{s.label}</option>
						{/each}
					</select>
				</div>

				<div class="form-control">
					<label class="label" for="faction-select"
						><span class="label-text">Controlling Faction</span></label
					>
					<select
						id="faction-select"
						bind:value={selectedHex.controlling_faction}
						on:change={updateSelectedHex}
						class="select-bordered select select-sm"
					>
						{#each factionNames as f}
							<option value={f === 'None' ? null : f}>{f}</option>
						{/each}
					</select>
				</div>
			</div>
		{/if}

		{#if selectedTool === 'fog'}
			<div class="mt-4 mb-6 flex flex-col gap-2 border-t border-base-content/10 pt-4">
				<span class="text-xs font-bold text-base-content/60 uppercase">Bulk Actions</span>
				<button class="btn btn-outline btn-sm" on:click={() => setAllDiscovery(true)}>
					Reveal All
				</button>
				<button class="btn btn-outline btn-sm" on:click={() => setAllDiscovery(false)}>
					Hide All
				</button>
				<div class="mt-2 text-[10px] leading-tight text-base-content/65">
					Click individual hexes while Fog tool is active to toggle discovery.
				</div>
			</div>
		{/if}

		{#if selectedTool === 'route'}
			<div class="mb-4 flex flex-col gap-2 border-t border-base-content/10 pt-3 text-xs">
				<span class="font-bold text-base-content/60 uppercase">Draw Route</span>
				<input
					type="text"
					bind:value={draftRouteName}
					class="input-bordered input input-xs"
					placeholder="Route name (e.g. King's Road)"
				/>
				<select bind:value={draftRouteType} class="select-bordered select select-xs">
					<option value="road">Road (Cobbled/Paved)</option>
					<option value="trail">Trail (Frontier Path)</option>
					<option value="sea_lane">Sea Lane (Nautical)</option>
					<option value="river">River / Waterway</option>
				</select>
				<div class="text-[11px] opacity-70">
					Click hexes in order ({draftRouteHexes.length} selected).
				</div>
				<div class="flex gap-1">
					<button
						class="btn btn-outline btn-xs flex-1"
						disabled={draftRouteHexes.length === 0}
						on:click={() => (draftRouteHexes = draftRouteHexes.slice(0, -1))}
					>
						Undo
					</button>
					<button
						class="btn btn-ghost btn-xs"
						disabled={draftRouteHexes.length === 0}
						on:click={() => (draftRouteHexes = [])}
					>
						Clear
					</button>
				</div>
				<button
					class="btn btn-primary btn-xs"
					disabled={draftRouteHexes.length < 2 || savingRoutes}
					on:click={commitDraftRoute}
				>
					{savingRoutes ? 'Saving...' : 'Save Route'}
				</button>

				{#if activeMap?.routes && activeMap.routes.length > 0}
					<div class="mt-2 flex flex-col gap-1 border-t border-base-content/10 pt-2">
						<span class="text-[10px] font-bold uppercase opacity-60">Existing Routes</span>
						{#each activeMap.routes as r}
							<div class="flex items-center justify-between rounded bg-base-300/60 px-2 py-1">
								<span class="truncate">{r.name || r.type}</span>
								<button
									class="btn btn-ghost btn-xs text-error"
									disabled={savingRoutes}
									on:click={() => deleteRoute(r.id)}
								>
									✕
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}

		<div class="mt-4 border-t border-base-content/10 pt-3">
			<button
				class="btn w-full btn-outline btn-xs"
				on:click={() => (bakeOpen = !bakeOpen)}
			>
				{bakeOpen ? 'Hide Earth Baker' : 'Bake Real-Earth Region'}
			</button>
			{#if bakeOpen}
				<div class="mt-2 flex flex-col gap-2 rounded bg-base-300/60 p-2 text-xs">
					<select class="select-bordered select select-xs" on:change={applyPreset}>
						{#each EARTH_REGION_PRESETS as preset, idx}
							<option value={idx}>{preset.label}</option>
						{/each}
					</select>
					<label class="flex flex-col gap-1">
						<span class="text-[11px] opacity-75">Camp Pin (Google Maps lat, lon)</span>
						<input
							type="text"
							bind:value={pinInput}
							class="input-bordered input input-xs font-mono"
							placeholder="64.1466, -21.9426"
						/>
					</label>
					<label class="flex flex-col gap-1">
						<span class="text-[11px] opacity-75">D&amp;D Travel Scale</span>
						<select bind:value={travelScale} class="select-bordered select select-xs">
							{#each TRAVEL_SCALES as scale}
								<option value={scale.value}>{scale.label}</option>
							{/each}
						</select>
					</label>
					<label class="flex cursor-pointer items-center gap-2">
						<input type="checkbox" bind:checked={autoSeedTerrain} class="checkbox checkbox-xs" />
						<span>Auto-seed hex terrain</span>
					</label>
					{#if bakeError}
						<p class="text-error text-[11px]">{bakeError}</p>
					{/if}
					<button class="btn btn-primary btn-xs" disabled={baking} on:click={bakeEarthLayers}>
						{baking ? 'Baking DEM + OSM...' : 'Bake Topo & Satellite'}
					</button>
				</div>
			{/if}
		</div>

		<div class="mt-auto pt-3">
			{#if isDirty}
				<button class="btn w-full btn-success" on:click={saveChanges}>Save Changes</button>
			{:else}
				<button class="btn btn-disabled w-full">Synced</button>
			{/if}
		</div>
	</div>

	<!-- Map Canvas -->
	<div class="relative flex-grow bg-neutral-900">
		{#if loading}
			<LoadingSpinner />
		{:else if activeMap}
			<HexGrid
				hexes={activeMap.hexes}
				hexSize={activeMap.hex_size}
				{selectedHex}
				showCoords={true}
				adminMode={true}
				baseLayerUrl={activeBaseLayerUrl}
				layerBounds={activeMap.layer_bounds || null}
				routes={activeMap.routes || []}
				{activeDraftRoute}
				{showDangerTiers}
				on:click={handleHexClick}
			/>

			<div class="absolute top-4 right-4 flex flex-col items-end gap-2">
				<div class="rounded bg-base-100/90 p-2 text-xs shadow">
					Active Map: <strong>{activeMap.name}</strong> ({activeMap.hexes.length} Hexes)
				</div>
				<div class="flex gap-1 rounded bg-base-100/90 p-1 shadow">
					{#if activeMap.topo_image_url}
						<button
							class="btn btn-xs {layerMode === 'topo' ? 'btn-primary' : 'btn-ghost'}"
							on:click={() => setLayerMode('topo')}
						>
							Topo
						</button>
					{/if}
					{#if activeMap.satellite_image_url}
						<button
							class="btn btn-xs {layerMode === 'satellite' ? 'btn-primary' : 'btn-ghost'}"
							on:click={() => setLayerMode('satellite')}
						>
							Satellite
						</button>
					{/if}
					<button
						class="btn btn-xs {layerMode === 'tactical' ? 'btn-primary' : 'btn-ghost'}"
						on:click={() => setLayerMode('tactical')}
					>
						Tactical
					</button>
					<button
						class="btn btn-xs {showDangerTiers ? 'btn-warning' : 'btn-ghost'}"
						on:click={() => (showDangerTiers = !showDangerTiers)}
					>
						T1–T3
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>
