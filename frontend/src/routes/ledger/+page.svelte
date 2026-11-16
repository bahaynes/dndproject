<script lang="ts">
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import type { LedgerEntry } from '$lib/types';
	import { WORLD_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let entries: LedgerEntry[] = [];
	let loading = true;
	let filterType = '';
	let offset = 0;
	const PAGE_SIZE = 25;

	const EVENT_TYPES = [
		'MissionCompleted',
		'MissionFailed',
		'Purchase',
		'RewardDistribution',
		'AdminAdjustment',
		'ShipAdjustment',
		'CharacterDeath',
		'LevelUp'
	];

	const EVENT_LABELS: Record<string, string> = {
		MissionCompleted: 'Quest Completed',
		MissionFailed: 'Quest Failed',
		Purchase: 'Store Purchase',
		RewardDistribution: 'Rewards',
		AdminAdjustment: 'DM Adjustment',
		ShipAdjustment: 'Treasury',
		CharacterDeath: 'Character Death',
		LevelUp: 'Level Up'
	};

	onMount(loadEntries);

	async function loadEntries() {
		loading = true;
		const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
		if (filterType) params.set('event_type', filterType);
		entries = await api('GET', `/ledger/?${params}`).catch(() => []);
		loading = false;
	}

	function applyFilter() {
		offset = 0;
		loadEntries();
	}

	function nextPage() {
		offset += PAGE_SIZE;
		loadEntries();
	}

	function prevPage() {
		offset = Math.max(0, offset - PAGE_SIZE);
		loadEntries();
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
	}
</script>

<div class="page-container">
	<SubNav items={WORLD_NAV} />

	<PageHeader
		title="Campaign Ledger"
		subtitle="Chronological record of completed quests, level-ups, store purchases, and casualties."
	>
		<div slot="actions" class="flex items-center gap-2">
			<select
				class="select select-bordered select-sm"
				bind:value={filterType}
				on:change={applyFilter}
				aria-label="Filter ledger by event type"
			>
				<option value="">All Event Types</option>
				{#each EVENT_TYPES as t}
					<option value={t}>{EVENT_LABELS[t] ?? t}</option>
				{/each}
			</select>
			<button class="btn btn-ghost btn-sm" on:click={applyFilter}>Refresh</button>
		</div>
	</PageHeader>

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else if entries.length === 0}
		<div class="panel p-10 text-center text-sm text-base-content/60">
			No ledger entries found.
		</div>
	{:else}
		<div class="panel overflow-x-auto">
			<table class="table table-sm">
				<thead class="bg-base-300/70 text-xs text-base-content/65">
					<tr>
						<th>Date</th>
						<th>Event</th>
						<th>Description</th>
					</tr>
				</thead>
				<tbody>
					{#each entries as entry}
						<tr class="border-b border-base-content/5 hover:bg-base-300/30">
							<td class="whitespace-nowrap text-xs text-base-content/60 stat-num">
								{formatDate(entry.created_at)}
							</td>
							<td>
								<span class="badge badge-outline badge-xs">
									{EVENT_LABELS[entry.event_type] ?? entry.event_type}
								</span>
							</td>
							<td class="text-sm text-base-content/85">{entry.description}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<div class="mt-4 flex items-center justify-between text-xs text-base-content/65">
			<button class="btn btn-ghost btn-xs" on:click={prevPage} disabled={offset === 0}>
				← Prev
			</button>
			<span class="stat-num">Showing {offset + 1}–{offset + entries.length}</span>
			<button class="btn btn-ghost btn-xs" on:click={nextPage} disabled={entries.length < PAGE_SIZE}>
				Next →
			</button>
		</div>
	{/if}
</div>
