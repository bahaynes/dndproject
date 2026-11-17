<script lang="ts">
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import type { Ship } from '$lib/types';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let settings: Ship | null = null;
	let loading = true;
	let saving = false;
	let seeding = false;
	let saveMsg = '';
	let saveError = '';
	let seedMsg = '';

	// World Import / Export
	let exporting = false;
	let importing = false;
	let importMode: 'merge' | 'replace' = 'merge';
	let importPreview: {
		world_name: string;
		factions: number;
		items: number;
		missions: number;
		maps: number;
		hexes: number;
		raw: unknown;
	} | null = null;
	let worldMsg = '';
	let worldError = '';

	interface WorldPreset {
		slug: string;
		world_name: string;
		hub_name?: string | null;
		summary?: string | null;
		factions: number;
		items: number;
		missions: number;
		maps: number;
		hexes: number;
	}

	let presets: WorldPreset[] = [];
	let selectedPreset = 'baseline_world';

	// Form
	let editName = '';
	let editMotd = '';

	$: activePreset = presets.find((p) => p.slug === selectedPreset) ?? presets[0] ?? null;

	onMount(loadSettings);

	async function loadSettings() {
		loading = true;
		try {
			const [shipRes, presetsRes] = await Promise.all([
				api('GET', '/ship/'),
				api('GET', '/admin/presets').catch(() => [])
			]);
			settings = shipRes;
			editName = settings!.name;
			editMotd = settings!.motd ?? '';
			presets = Array.isArray(presetsRes) ? presetsRes : [];
			if (presets.length > 0 && !presets.some((p) => p.slug === selectedPreset)) {
				selectedPreset = presets[0].slug;
			}
		} catch (e) {}
		loading = false;
	}

	async function saveSettings() {
		saving = true;
		saveMsg = '';
		saveError = '';
		try {
			settings = await api('PUT', '/ship/', {
				name: editName,
				level: settings?.level ?? 1,
				essence: settings?.essence ?? 0,
				motd: editMotd || null
			});
			saveMsg = 'Campaign settings saved.';
		} catch (e) {
			saveError = e instanceof Error ? e.message : 'Failed to save.';
		}
		saving = false;
	}

	async function seedStarterData() {
		seeding = true;
		seedMsg = '';
		saveError = '';
		try {
			const res = await api('POST', `/admin/seed?preset=${encodeURIComponent(selectedPreset)}`);
			seedMsg = `Loaded "${res.world_name}": ${res.factions_created} factions, ${res.items_created} items, ${res.missions_created} quests, ${res.hexes_upserted} hexes.`;
			await loadSettings();
		} catch (e) {
			saveError = e instanceof Error ? e.message : 'Failed to load starter world.';
		}
		seeding = false;
	}

	async function exportWorld() {
		exporting = true;
		worldMsg = '';
		worldError = '';
		try {
			const bundle = await api('GET', '/admin/world/export');
			const slug = (bundle.world_name || 'world')
				.toLowerCase()
				.replace(/[^a-z0-9]+/g, '-')
				.replace(/^-|-$/g, '');
			const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `${slug || 'world'}.world.json`;
			document.body.appendChild(a);
			a.click();
			a.remove();
			URL.revokeObjectURL(url);
			worldMsg = `Exported "${bundle.world_name}".`;
		} catch (e) {
			worldError = e instanceof Error ? e.message : 'Failed to export world.';
		}
		exporting = false;
	}

	async function handleFileSelect(event: Event) {
		worldMsg = '';
		worldError = '';
		importPreview = null;
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		try {
			const text = await file.text();
			const parsed = JSON.parse(text);
			if (!parsed || typeof parsed.world_name !== 'string') {
				throw new Error('Invalid world bundle: missing "world_name".');
			}
			const maps = Array.isArray(parsed.maps) ? parsed.maps : [];
			const hexCount = maps.reduce(
				(sum: number, m: { hexes?: unknown[] }) => sum + (Array.isArray(m.hexes) ? m.hexes.length : 0),
				0
			);
			importPreview = {
				world_name: parsed.world_name,
				factions: Array.isArray(parsed.factions) ? parsed.factions.length : 0,
				items: Array.isArray(parsed.items) ? parsed.items.length : 0,
				missions: Array.isArray(parsed.missions) ? parsed.missions.length : 0,
				maps: maps.length,
				hexes: hexCount,
				raw: parsed
			};
		} catch (e) {
			worldError = e instanceof Error ? e.message : 'Could not parse JSON file.';
		}
	}

	async function importWorld() {
		if (!importPreview) return;
		importing = true;
		worldMsg = '';
		worldError = '';
		try {
			const res = await api('POST', '/admin/world/import', {
				bundle: importPreview.raw,
				mode: importMode
			});
			worldMsg = `Imported "${res.world_name}" (${res.mode}): ${res.factions_created + res.factions_updated} factions, ${res.items_created + res.items_updated} items, ${res.missions_created + res.missions_updated} quests, ${res.hexes_upserted} hexes.`;
			importPreview = null;
			await loadSettings();
		} catch (e) {
			worldError = e instanceof Error ? e.message : 'Failed to import world.';
		}
		importing = false;
	}
</script>

<PageHeader
	title="Campaign Settings"
	subtitle="Configure the DM bulletin (MOTD) shown on the Dashboard or seed starter quests and factions."
/>

{#if loading}
	<LoadingSpinner size="lg" />
{:else}
	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<section class="panel p-5 space-y-4">
			<h2 class="text-base font-semibold text-base-content">Bulletin &amp; Display</h2>

			<div>
				<label for="camp-hub-name" class="mb-1 block text-xs font-medium text-base-content/75">
					Hub / Base Name
				</label>
				<input
					id="camp-hub-name"
					class="input input-bordered input-sm w-full"
					bind:value={editName}
					placeholder="e.g. Crossroads Keep"
				/>
			</div>

			<div>
				<label for="camp-motd" class="mb-1 block text-xs font-medium text-base-content/75">
					DM Bulletin (MOTD)
				</label>
				<textarea
					id="camp-motd"
					class="textarea textarea-bordered w-full text-sm"
					rows="3"
					bind:value={editMotd}
					placeholder="Announcement shown to all players on the Dashboard..."
				></textarea>
			</div>

			{#if saveMsg}
				<div class="alert alert-success text-xs">{saveMsg}</div>
			{/if}
			{#if saveError}
				<div class="alert alert-error text-xs">{saveError}</div>
			{/if}

			<div class="flex justify-end">
				<button class="btn btn-primary btn-sm" on:click={saveSettings} disabled={saving}>
					{saving ? 'Saving...' : 'Save Settings'}
				</button>
			</div>
		</section>

		<section class="panel p-5 space-y-4">
			<h2 class="text-base font-semibold text-base-content">Starter World Presets</h2>
			<p class="text-xs leading-relaxed text-base-content/70">
				Choose a starting premise for this campaign. Uses non-destructive merge—safe to run multiple times.
			</p>
			{#if presets.length > 0}
				<div>
					<label for="starter-preset" class="mb-1 block text-xs font-medium text-base-content/75">
						World Premise
					</label>
					<select
						id="starter-preset"
						class="select select-bordered select-sm w-full"
						bind:value={selectedPreset}
					>
						{#each presets as preset}
							<option value={preset.slug}>{preset.world_name}</option>
						{/each}
					</select>
				</div>
				{#if activePreset}
					<div class="rounded-lg border border-base-content/10 bg-base-200/40 p-3 text-xs space-y-2">
						{#if activePreset.summary}
							<p class="leading-relaxed text-base-content/80">{activePreset.summary}</p>
						{/if}
						<div class="flex flex-wrap gap-1.5 text-base-content/70">
							{#if activePreset.hub_name}
								<span class="badge badge-ghost badge-sm">Hub: {activePreset.hub_name}</span>
							{/if}
							<span class="badge badge-ghost badge-sm">{activePreset.factions} factions</span>
							<span class="badge badge-ghost badge-sm">{activePreset.items} items</span>
							<span class="badge badge-ghost badge-sm">{activePreset.missions} quests</span>
							<span class="badge badge-ghost badge-sm">{activePreset.hexes} hexes</span>
						</div>
					</div>
				{/if}
			{/if}
			{#if seedMsg}
				<div class="alert alert-success text-xs">{seedMsg}</div>
			{/if}
			<div>
				<button class="btn btn-outline btn-primary btn-sm" on:click={seedStarterData} disabled={seeding}>
					{seeding ? 'Loading Starter World...' : 'Load Starter World'}
				</button>
			</div>
		</section>
	</div>

	<section class="panel mt-6 p-5 space-y-4">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<div>
				<h2 class="text-base font-semibold text-base-content">World Import / Export</h2>
				<p class="text-xs text-base-content/70">
					Back up or move your hub, factions, store catalog, quests, and hex maps between campaigns as a
					portable <code>.world.json</code> bundle. Characters and session logs are never overwritten.
				</p>
			</div>
			<button class="btn btn-outline btn-sm" on:click={exportWorld} disabled={exporting}>
				{exporting ? 'Exporting...' : 'Export World (.json)'}
			</button>
		</div>

		<div class="divider my-1"></div>

		<div class="grid grid-cols-1 gap-4 md:grid-cols-2 md:items-end">
			<div>
				<label for="world-import-file" class="mb-1 block text-xs font-medium text-base-content/75">
					Import World File (.json)
				</label>
				<input
					id="world-import-file"
					type="file"
					accept=".json,application/json"
					class="file-input file-input-bordered file-input-sm w-full"
					on:change={handleFileSelect}
				/>
			</div>

			<div>
				<label for="world-import-mode" class="mb-1 block text-xs font-medium text-base-content/75">
					Import Mode
				</label>
				<select
					id="world-import-mode"
					class="select select-bordered select-sm w-full"
					bind:value={importMode}
				>
					<option value="merge">Merge (Upsert by name, keep existing records)</option>
					<option value="replace">Replace World (Clear old world, keep characters &amp; sessions)</option>
				</select>
			</div>
		</div>

		{#if importPreview}
			<div class="rounded-lg border border-primary/30 bg-base-200/60 p-3 text-xs space-y-2">
				<div class="flex flex-wrap items-center justify-between gap-2">
					<span class="font-semibold text-base-content">Ready to import: {importPreview.world_name}</span>
					<button class="btn btn-primary btn-xs" on:click={importWorld} disabled={importing}>
						{importing ? 'Importing...' : `Confirm ${importMode === 'replace' ? 'Replace' : 'Merge'} Import`}
					</button>
				</div>
				<div class="flex flex-wrap gap-2 text-base-content/75">
					<span class="badge badge-ghost badge-sm">{importPreview.factions} factions</span>
					<span class="badge badge-ghost badge-sm">{importPreview.items} items</span>
					<span class="badge badge-ghost badge-sm">{importPreview.missions} quests</span>
					<span class="badge badge-ghost badge-sm">{importPreview.maps} maps ({importPreview.hexes} hexes)</span>
				</div>
			</div>
		{/if}

		{#if worldMsg}
			<div class="alert alert-success text-xs">{worldMsg}</div>
		{/if}
		{#if worldError}
			<div class="alert alert-error text-xs">{worldError}</div>
		{/if}
	</section>
{/if}
