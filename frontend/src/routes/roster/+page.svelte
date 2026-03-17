<script lang="ts">
    import { auth } from '$lib/auth';
    import { onMount } from 'svelte';
    import { API_BASE_URL } from '$lib/config';
    import type { CharacterRosterEntry } from '$lib/types';

    let authToken: string | null = null;
    let roster: CharacterRosterEntry[] = [];
    let loading = true;
    let statusFilter = '';
    let sortKey: keyof CharacterRosterEntry = 'name';
    let sortAsc = true;

    auth.subscribe(v => { authToken = v.token; });
    onMount(loadRoster);

    async function loadRoster() {
        loading = true;
        const params = new URLSearchParams();
        if (statusFilter) params.set('status', statusFilter);
        const res = await fetch(`${API_BASE_URL}/characters/roster?${params}`, {
            headers: { Authorization: `Bearer ${authToken}` },
        });
        if (res.ok) roster = await res.json();
        loading = false;
    }

    function toggleSort(key: keyof CharacterRosterEntry) {
        if (sortKey === key) sortAsc = !sortAsc;
        else { sortKey = key; sortAsc = true; }
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

<div class="container mx-auto p-4 max-w-5xl">
    <div class="flex justify-between items-center mb-6 border-b border-base-content/10 pb-4">
        <h1 class="text-3xl font-bold font-[var(--font-cinzel)] tracking-tight text-primary">👥 Crew Roster</h1>
        <a href="/dashboard" class="btn btn-sm btn-ghost">← Dashboard</a>
    </div>

    <!-- Filter -->
    <div class="flex gap-3 mb-4 flex-wrap">
        <select class="select select-sm select-bordered" bind:value={statusFilter} on:change={loadRoster}>
            {#each STATUSES as s}
                <option value={s}>{s || 'All statuses'}</option>
            {/each}
        </select>
        <span class="text-sm opacity-60 self-center">{roster.length} crew member{roster.length !== 1 ? 's' : ''}</span>
    </div>

    {#if loading}
        <div class="flex justify-center py-16"><span class="loading loading-spinner loading-lg text-primary"></span></div>
    {:else if sorted.length === 0}
        <div class="alert">No crew members found.</div>
    {:else}
        <div class="overflow-x-auto rounded-lg border border-base-content/10">
            <table class="table table-sm">
                <thead class="bg-base-200">
                    <tr>
                        <th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('name')}>Name {sortKey === 'name' ? (sortAsc ? '↑' : '↓') : ''}</th>
                        <th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('class_name')}>Class {sortKey === 'class_name' ? (sortAsc ? '↑' : '↓') : ''}</th>
                        <th class="cursor-pointer hover:text-primary text-center" on:click={() => toggleSort('level')}>Lvl {sortKey === 'level' ? (sortAsc ? '↑' : '↓') : ''}</th>
                        <th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('owner_username')}>Player {sortKey === 'owner_username' ? (sortAsc ? '↑' : '↓') : ''}</th>
                        <th class="cursor-pointer hover:text-primary" on:click={() => toggleSort('status')}>Status {sortKey === 'status' ? (sortAsc ? '↑' : '↓') : ''}</th>
                        <th class="cursor-pointer hover:text-primary text-center" on:click={() => toggleSort('missions_completed')}>Missions {sortKey === 'missions_completed' ? (sortAsc ? '↑' : '↓') : ''}</th>
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
                        <td class="opacity-70">{char.class_name ?? '—'}</td>
                        <td class="text-center">{char.level}</td>
                        <td class="opacity-70">{char.owner_username ?? '—'}</td>
                        <td><span class="badge badge-sm {statusBadge(char.status)}">{char.status}</span></td>
                        <td class="text-center">{char.missions_completed}</td>
                        <td class="text-xs opacity-60">{char.status === 'Dead' ? formatDate(char.date_of_death) : '—'}</td>
                    </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>
