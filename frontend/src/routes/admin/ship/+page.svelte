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

	// Form
	let editName = '';
	let editMotd = '';

	onMount(loadSettings);

	async function loadSettings() {
		loading = true;
		try {
			settings = await api('GET', '/ship/');
			editName = settings!.name;
			editMotd = settings!.motd ?? '';
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
			const res = await api('POST', '/admin/seed');
			seedMsg = `Seeded ${res.factions_created} factions and ${res.missions_created} starter quests.`;
		} catch (e) {
			saveError = e instanceof Error ? e.message : 'Failed to seed starter data.';
		}
		seeding = false;
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
			<h2 class="text-base font-semibold text-base-content">Quick Start Seed</h2>
			<p class="text-xs leading-relaxed text-base-content/70">
				Populate a new campaign with starter D&amp;D 5e Tier 1 quests and baseline factions. Safe to
				run multiple times—existing records are skipped.
			</p>
			{#if seedMsg}
				<div class="alert alert-success text-xs">{seedMsg}</div>
			{/if}
			<div>
				<button class="btn btn-outline btn-primary btn-sm" on:click={seedStarterData} disabled={seeding}>
					{seeding ? 'Seeding...' : 'Seed Starter Campaign Data'}
				</button>
			</div>
		</section>
	</div>
{/if}
