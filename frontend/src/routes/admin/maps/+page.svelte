<script context="module">
	function getTerrainColor(terrain: string): string {
		switch (terrain) {
			case 'plains':
				return '#90EE90';
			case 'forest':
				return '#228B22';
			case 'mountain':
				return '#808080';
			case 'water':
				return '#4682B4';
			case 'desert':
				return '#F4A460';
			case 'swamp':
				return '#556B2F';
			default:
				return '#D3D3D3';
		}
	}
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/auth';
	import { get } from 'svelte/store';
	import { API_BASE_URL } from '$lib/config';
	import { goto } from '$app/navigation';
	import HexGrid from '$lib/components/HexGrid.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import type { Mission } from '$lib/types';

	interface HexData {
		q: number;
		r: number;
		terrain: string;
		is_discovered: boolean;
		linked_location_name?: string;
		linked_mission_id?: number;
	}

	interface MapData {
		id: number;
		name: string;
		hex_size: number;
		hexes: HexData[];
	}

	let maps: MapData[] = [];
	let missions: Mission[] = [];
	let activeMap: MapData | null = null;
	let loading = true;

	// Editor State
	let selectedHex: HexData | null = null;
	let selectedTool: 'select' | 'paint' | 'fog' = 'select';
	let activeTerrain = 'plains';
	let isDirty = false;
	let dirtyHexes: Set<string> = new Set();

	const TERRAIN_TYPES = ['Plains', 'Forest', 'Mountain', 'Water', 'Desert', 'Swamp'];

	onMount(async () => {
		// Check admin
		const authState = get(auth);
		if (!authState.isAuthenticated || authState.user?.role !== 'admin') {
			// Redirect or show error (omitted for brevity)
		}

		await Promise.all([fetchMaps(), fetchMissions()]);
		if (maps.length > 0) {
			activeMap = maps[0];
		}
		loading = false;
	});

	async function fetchMissions() {
		try {
			const res = await fetch(`${API_BASE_URL}/missions/`, {
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) missions = await res.json();
		} catch (e) {}
	}

	async function fetchMaps() {
		try {
			const res = await fetch(`${API_BASE_URL}/maps/`, {
				headers: { Authorization: `Bearer ${get(auth).token}` }
			});
			if (res.ok) maps = await res.json();
		} catch (e) {}
	}

	function handleHexClick(e: CustomEvent) {
		if (!activeMap) return;
		const { q, r } = e.detail;
		const hexIndex = activeMap.hexes.findIndex((h) => h.q === q && h.r === r);

		if (hexIndex === -1) return;

		if (selectedTool === 'paint') {
			// Update local state
			const newHexes = [...activeMap.hexes];
			newHexes[hexIndex] = { ...newHexes[hexIndex], terrain: activeTerrain };
			activeMap.hexes = newHexes;
			isDirty = true;

			// In a real app we might debut this or save immediately
			// For now, we just update local state and have a "Save" button
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
		}
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

		const token = get(auth).token;
		let successCount = 0;
		let failCount = 0;

		for (const coordStr of dirtyHexes) {
			const [q, r] = coordStr.split(',').map(Number);
			const hex = activeMap.hexes.find((h) => h.q === q && h.r === r);
			if (!hex) continue;

			try {
				const res = await fetch(`${API_BASE_URL}/maps/${activeMap.id}/hexes/${q}/${r}`, {
					method: 'PUT',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${token}`
					},
					body: JSON.stringify({
						terrain: hex.terrain,
						is_discovered: hex.is_discovered,
						linked_location_name: hex.linked_location_name,
						linked_mission_id: hex.linked_mission_id,
						notes: (hex as any).notes
					})
				});

				if (res.ok) successCount++;
				else failCount++;
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
	<div class="bg-base-200 border-base-content/10 flex w-64 flex-col border-r p-4">
		<h2 class="mb-4 text-xl font-[var(--font-cinzel)] font-bold">Map Editor</h2>

		<div class="mb-6 flex flex-col gap-2">
			<span class="text-xs font-bold uppercase opacity-50">Tools</span>
			<div class="join w-full">
				<button
					class="join-item btn flex-1 {selectedTool === 'select' ? 'btn-primary' : 'btn-outline'}"
					on:click={() => (selectedTool = 'select')}>Select</button
				>
				<button
					class="join-item btn flex-1 {selectedTool === 'paint' ? 'btn-primary' : 'btn-outline'}"
					on:click={() => (selectedTool = 'paint')}>Paint</button
				>
				<button
					class="join-item btn flex-1 {selectedTool === 'fog' ? 'btn-primary' : 'btn-outline'}"
					on:click={() => (selectedTool = 'fog')}>Fog</button
				>
			</div>
		</div>

		{#if selectedTool === 'paint'}
			<div class="mb-6 flex flex-col gap-2">
				<span class="text-xs font-bold uppercase opacity-50">Palette</span>
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
			<div class="border-base-content/10 mt-4 flex flex-col gap-4 border-t pt-4">
				<div class="flex items-center justify-between">
					<span class="text-sm font-bold">Hex {selectedHex.q}, {selectedHex.r}</span>
					<button class="btn btn-xs btn-ghost" on:click={() => (selectedHex = null)}>Close</button>
				</div>

				<div class="form-control">
					<label class="label" for="terrain-select"><span class="label-text">Terrain</span></label>
					<select
						id="terrain-select"
						bind:value={selectedHex.terrain}
						on:change={updateSelectedHex}
						class="select select-bordered select-sm"
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
						class="input input-bordered input-sm"
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
						class="select select-bordered select-sm"
					>
						<option value={null}>None</option>
						{#each missions as mission}
							<option value={mission.id}>{mission.name}</option>
						{/each}
					</select>
				</div>
			</div>
		{/if}

		{#if selectedTool === 'fog'}
			<div class="border-base-content/10 mb-6 mt-4 flex flex-col gap-2 border-t pt-4">
				<span class="text-xs font-bold uppercase opacity-50">Bulk Actions</span>
				<button class="btn btn-sm btn-outline" on:click={() => setAllDiscovery(true)}>
					Reveal All
				</button>
				<button class="btn btn-sm btn-outline" on:click={() => setAllDiscovery(false)}>
					Hide All
				</button>
				<div class="mt-2 text-[10px] leading-tight opacity-60">
					Click individual hexes while Fog tool is active to toggle discovery.
				</div>
			</div>
		{/if}

		<div class="mt-auto">
			{#if isDirty}
				<button class="btn btn-success w-full" on:click={saveChanges}>Save Changes</button>
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
				on:click={handleHexClick}
			/>

			<div class="bg-base-100/90 absolute right-4 top-4 rounded p-2 text-xs shadow">
				Active Map: <strong>{activeMap.name}</strong> ({activeMap.hexes.length} Hexes)
			</div>
		{/if}
	</div>
</div>
