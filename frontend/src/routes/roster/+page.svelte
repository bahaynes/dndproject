<script lang="ts">
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import type { CharacterRosterEntry } from '$lib/types';
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

<div class="container mx-auto max-w-5xl p-4">
	<div class="mb-6 flex items-center justify-between border-b border-base-content/10 pb-4">
		<h1 class="text-3xl font-[var(--font-cinzel)] font-bold tracking-tight text-primary">
			👥 Crew Roster
		</h1>
		<a href="/dashboard" class="btn btn-ghost btn-sm">← Dashboard</a>
	</div>

	<!-- Filter -->
	<div class="mb-4 flex flex-wrap gap-3">
		<select
			class="select-bordered select select-sm"
			bind:value={statusFilter}
			on:change={loadRoster}
		>
			{#each STATUSES as s}
				<option value={s}>{s || 'All statuses'}</option>
			{/each}
		</select>
		<span class="self-center text-sm text-base-content/65"
			>{roster.length} crew member{roster.length !== 1 ? 's' : ''}</span
		>
	</div>

	{#if loading}
		<div class="flex justify-center py-16">
			<span class="loading loading-lg loading-spinner text-primary"></span>
		</div>
	{:else if sorted.length === 0}
		<div class="alert">No crew members found.</div>
	{:else}
		<div class="overflow-x-auto rounded-lg border border-base-content/10">
			<table class="table table-sm">
				<thead class="bg-base-200">
					<tr>
						<th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('name')}
							>Name {sortKey === 'name' ? (sortAsc ? '↑' : '↓') : ''}</th
						>
						<th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('class_name')}
							>Class {sortKey === 'class_name' ? (sortAsc ? '↑' : '↓') : ''}</th
						>
						<th
							class="cursor-pointer text-center hover:text-primary"
							on:click={() => toggleSort('level')}
							>Lvl {sortKey === 'level' ? (sortAsc ? '↑' : '↓') : ''}</th
						>
						<th
							class="cursor-pointer hover:text-primary"
							on:click={() => toggleSort('owner_username')}
							>Player {sortKey === 'owner_username' ? (sortAsc ? '↑' : '↓') : ''}</th
						>
						<th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('status')}
							>Status {sortKey === 'status' ? (sortAsc ? '↑' : '↓') : ''}</th
						>
						<th
							class="cursor-pointer text-center hover:text-primary"
							on:click={() => toggleSort('missions_completed')}
							>Missions {sortKey === 'missions_completed' ? (sortAsc ? '↑' : '↓') : ''}</th
						>
						<th>Date of Death</th>
					</tr>
				</thead>
				<tbody>
					{#each sorted as char}
						<tr class="hover {char.status === 'Dead' ? 'opacity-60' : ''}">
							<td class="font-semibold">
								{#if char.status === 'Dead'}💀{/if}
								{char.name}
							</td>
							<td class="text-base-content/70">{char.class_name ?? '—'}</td>
							<td class="text-center">{char.level}</td>
							<td class="text-base-content/70">{char.owner_username ?? '—'}</td>
							<td><span class="badge badge-sm {statusBadge(char.status)}">{char.status}</span></td>
							<td class="text-center">{char.missions_completed}</td>
							<td class="text-xs text-base-content/65"
								>{char.status === 'Dead' ? formatDate(char.date_of_death) : '—'}</td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>
