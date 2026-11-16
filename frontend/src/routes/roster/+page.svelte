<script lang="ts">
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import type { CharacterRosterEntry } from '$lib/types';
	import { ADVENTURERS_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let roster: CharacterRosterEntry[] = [];
	let loading = true;
	let statusFilter = '';
	let sortKey: keyof CharacterRosterEntry = 'name';
	let sortAsc = true;

	onMount(loadRoster);

	async function loadRoster() {
		loading = true;
		const params = new URLSearchParams();
		if (statusFilter) params.set('status', statusFilter);
		roster = await api('GET', `/characters/roster?${params}`).catch(() => []);
		loading = false;
	}

	function toggleSort(key: keyof CharacterRosterEntry) {
		if (sortKey === key) sortAsc = !sortAsc;
		else {
			sortKey = key;
			sortAsc = true;
		}
	}

	$: sorted = [...roster].sort((a, b) => {
		const va = a[sortKey] ?? '';
		const vb = b[sortKey] ?? '';
		return (va < vb ? -1 : va > vb ? 1 : 0) * (sortAsc ? 1 : -1);
	});

	function statusBadge(s: string) {
		if (s === 'Active') return 'badge-success';
		if (s === 'Dead') return 'badge-error';
		return 'badge-ghost';
	}

	function formatDate(iso?: string) {
		if (!iso) return '—';
		return new Date(iso).toLocaleDateString();
	}

	const STATUSES = ['', 'Active', 'Dead', 'Benched'];
</script>

<div class="page-container">
	<SubNav items={ADVENTURERS_NAV} />

	<PageHeader
		title="Party Roster"
		subtitle="All registered adventurers in this campaign, their 5e level, XP, and status."
	>
		<div slot="actions" class="flex items-center gap-3">
			<span class="text-xs text-base-content/60 stat-num">
				{roster.length} adventurer{roster.length !== 1 ? 's' : ''}
			</span>
			<select
				class="select select-bordered select-sm"
				bind:value={statusFilter}
				on:change={loadRoster}
				aria-label="Filter roster by status"
			>
				{#each STATUSES as s}
					<option value={s}>{s || 'All Statuses'}</option>
				{/each}
			</select>
		</div>
	</PageHeader>

	{#if loading}
		<LoadingSpinner size="lg" />
	{:else if sorted.length === 0}
		<div class="panel p-10 text-center text-sm text-base-content/60">
			No adventurers found.
		</div>
	{:else}
		<div class="panel overflow-x-auto">
			<table class="table table-sm">
				<thead class="bg-base-300/70 text-xs text-base-content/65">
					<tr>
						<th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('name')}>
							Name {sortKey === 'name' ? (sortAsc ? '↑' : '↓') : ''}
						</th>
						<th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('class_name')}>
							Class {sortKey === 'class_name' ? (sortAsc ? '↑' : '↓') : ''}
						</th>
						<th class="cursor-pointer text-center hover:text-primary" on:click={() => toggleSort('level')}>
							Lvl {sortKey === 'level' ? (sortAsc ? '↑' : '↓') : ''}
						</th>
						<th class="cursor-pointer text-right hover:text-primary" on:click={() => toggleSort('xp')}>
							XP {sortKey === 'xp' ? (sortAsc ? '↑' : '↓') : ''}
						</th>
						<th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('owner_username')}>
							Player {sortKey === 'owner_username' ? (sortAsc ? '↑' : '↓') : ''}
						</th>
						<th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('status')}>
							Status {sortKey === 'status' ? (sortAsc ? '↑' : '↓') : ''}
						</th>
						<th
							class="cursor-pointer text-center hover:text-primary"
							on:click={() => toggleSort('missions_completed')}
						>
							Quests {sortKey === 'missions_completed' ? (sortAsc ? '↑' : '↓') : ''}
						</th>
						<th>Fallen</th>
					</tr>
				</thead>
				<tbody>
					{#each sorted as char}
						<tr class="border-b border-base-content/5 hover:bg-base-300/30 {char.status === 'Dead' ? 'opacity-60' : ''}">
							<td class="font-medium text-base-content">{char.name}</td>
							<td class="text-base-content/70">{char.class_name ?? '—'}</td>
							<td class="text-center stat-num">{char.level}</td>
							<td class="text-right text-base-content/75 stat-num">{(char.xp ?? 0).toLocaleString()}</td>
							<td class="text-base-content/70">{char.owner_username ?? '—'}</td>
							<td><span class="badge badge-xs {statusBadge(char.status)}">{char.status}</span></td>
							<td class="text-center stat-num">{char.missions_completed}</td>
							<td class="text-xs text-base-content/55 stat-num">
								{char.status === 'Dead' ? formatDate(char.date_of_death) : '—'}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
