<script lang="ts">
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import type { LedgerEntry } from '$lib/types';
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

	function deltaCell(n: number) {
		if (n === 0) return '—';
		return n > 0 ? `+${n}` : `${n}`;
	}

	function deltaClass(n: number) {
		if (n > 0) return 'text-success font-semibold';
		if (n < 0) return 'text-error font-semibold';
		return 'text-base-content/50';
	}

	const EVENT_LABELS: Record<string, string> = {
		MissionCompleted: '✅ Completed',
		MissionFailed: '❌ Failed',
		Purchase: '🛒 Purchase',
		RewardDistribution: '🎁 Rewards',
		AdminAdjustment: '⚙️ Adjustment',
		ShipAdjustment: '🚀 Ship',
		CharacterDeath: '💀 Death',
		LevelUp: '⬆️ Level Up'
	};
</script>

<div class="container mx-auto max-w-5xl p-4">
	<div class="mb-6 flex items-center justify-between border-b border-base-content/10 pb-4">
		<h1 class="text-3xl font-[var(--font-cinzel)] font-bold tracking-tight text-primary">
			📖 Campaign Ledger
		</h1>
		<a href="/dashboard" class="btn btn-ghost btn-sm">← Dashboard</a>
	</div>

	<!-- Filters -->
	<div class="mb-4 flex flex-wrap gap-3">
		<select
			class="select-bordered select select-sm"
			bind:value={filterType}
			on:change={applyFilter}
		>
			<option value="">All event types</option>
			{#each EVENT_TYPES as t}
				<option value={t}>{EVENT_LABELS[t] ?? t}</option>
			{/each}
		</select>
		<button class="btn btn-ghost btn-sm" on:click={applyFilter}>Refresh</button>
	</div>

	{#if loading}
		<div class="flex justify-center py-16">
			<span class="loading loading-lg loading-spinner text-primary"></span>
		</div>
	{:else if entries.length === 0}
		<div class="alert">No ledger entries found.</div>
	{:else}
		<div class="overflow-x-auto rounded-lg border border-base-content/10">
			<table class="table table-sm">
				<thead class="bg-base-200">
					<tr>
						<th>Date</th>
						<th>Event</th>
						<th>Description</th>
						<th class="text-right">⚡ Essence</th>
						<th class="text-right">🪙 Gold</th>
						<th class="text-right">❤️ HP</th>
					</tr>
				</thead>
				<tbody>
					{#each entries as entry}
						<tr class="hover">
							<td class="text-xs whitespace-nowrap text-base-content/65"
								>{formatDate(entry.created_at)}</td
							>
							<td
								><span class="badge badge-outline badge-sm"
									>{EVENT_LABELS[entry.event_type] ?? entry.event_type}</span
								></td
							>
							<td class="max-w-xs truncate text-sm">{entry.description}</td>
							<td class="text-right text-sm {deltaClass(entry.essence_delta)}"
								>{deltaCell(entry.essence_delta)}</td
							>
							<td class="text-right text-sm {deltaClass(entry.gold_delta)}"
								>{deltaCell(entry.gold_delta)}</td
							>
							<td class="text-right text-sm {deltaClass(entry.hp_delta)}"
								>{deltaCell(entry.hp_delta)}</td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		<div class="mt-4 flex items-center justify-between">
			<button class="btn btn-ghost btn-sm" on:click={prevPage} disabled={offset === 0}
				>← Prev</button
			>
			<span class="text-sm text-base-content/65"
				>Showing {offset + 1}–{offset + entries.length}</span
			>
			<button class="btn btn-ghost btn-sm" on:click={nextPage} disabled={entries.length < PAGE_SIZE}
				>Next →</button
			>
		</div>
	{/if}
</div>
