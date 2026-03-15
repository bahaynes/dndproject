<script lang="ts">
    import { auth } from '$lib/auth';
    import { onMount } from 'svelte';
    import { API_BASE_URL } from '$lib/config';
    import type { LedgerEntry } from '$lib/types';

    let authToken: string | null = null;
    let entries: LedgerEntry[] = [];
    let loading = true;
    let filterType = '';
    let offset = 0;
    const PAGE_SIZE = 25;

    const EVENT_TYPES = [
        'MissionCompleted', 'MissionFailed', 'Purchase', 'RewardDistribution',
        'AdminAdjustment', 'ShipAdjustment', 'CharacterDeath', 'LevelUp',
    ];

    auth.subscribe(v => { authToken = v.token; });

    onMount(loadEntries);

    async function loadEntries() {
        loading = true;
        const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
        if (filterType) params.set('event_type', filterType);
        const res = await fetch(`${API_BASE_URL}/ledger/?${params}`, {
            headers: { Authorization: `Bearer ${authToken}` },
        });
        if (res.ok) entries = await res.json();
        loading = false;
    }

    function applyFilter() { offset = 0; loadEntries(); }
    function nextPage() { offset += PAGE_SIZE; loadEntries(); }
    function prevPage() { offset = Math.max(0, offset - PAGE_SIZE); loadEntries(); }

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
        return 'opacity-40';
    }

    const EVENT_LABELS: Record<string, string> = {
        MissionCompleted: '✅ Completed',
        MissionFailed: '❌ Failed',
        Purchase: '🛒 Purchase',
        RewardDistribution: '🎁 Rewards',
        AdminAdjustment: '⚙️ Adjustment',
        ShipAdjustment: '🚀 Ship',
        CharacterDeath: '💀 Death',
        LevelUp: '⬆️ Level Up',
    };
</script>

<div class="container mx-auto p-4 max-w-5xl">
    <div class="flex justify-between items-center mb-6 border-b border-base-content/10 pb-4">
        <h1 class="text-3xl font-bold font-[var(--font-cinzel)] tracking-tight text-primary">📖 Campaign Ledger</h1>
        <a href="/dashboard" class="btn btn-sm btn-ghost">← Dashboard</a>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4 flex-wrap">
        <select class="select select-sm select-bordered" bind:value={filterType} on:change={applyFilter}>
            <option value="">All event types</option>
            {#each EVENT_TYPES as t}
                <option value={t}>{EVENT_LABELS[t] ?? t}</option>
            {/each}
        </select>
        <button class="btn btn-sm btn-ghost" on:click={applyFilter}>Refresh</button>
    </div>

    {#if loading}
        <div class="flex justify-center py-16"><span class="loading loading-spinner loading-lg text-primary"></span></div>
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
                        <th class="text-right">⛽ Fuel</th>
                        <th class="text-right">💎 Crystal</th>
                        <th class="text-right">💰 Credits</th>
                        <th class="text-right">⭐ XP</th>
                    </tr>
                </thead>
                <tbody>
                    {#each entries as entry}
                    <tr class="hover">
                        <td class="text-xs opacity-60 whitespace-nowrap">{formatDate(entry.created_at)}</td>
                        <td><span class="badge badge-sm badge-outline">{EVENT_LABELS[entry.event_type] ?? entry.event_type}</span></td>
                        <td class="max-w-xs truncate text-sm">{entry.description}</td>
                        <td class="text-right text-sm {deltaClass(entry.fuel_delta)}">{deltaCell(entry.fuel_delta)}</td>
                        <td class="text-right text-sm {deltaClass(entry.crystal_delta)}">{deltaCell(entry.crystal_delta)}</td>
                        <td class="text-right text-sm {deltaClass(entry.credit_delta)}">{deltaCell(entry.credit_delta)}</td>
                        <td class="text-right text-sm {deltaClass(entry.xp_delta)}">{deltaCell(entry.xp_delta)}</td>
                    </tr>
                    {/each}
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <div class="flex justify-between items-center mt-4">
            <button class="btn btn-sm btn-ghost" on:click={prevPage} disabled={offset === 0}>← Prev</button>
            <span class="text-sm opacity-60">Showing {offset + 1}–{offset + entries.length}</span>
            <button class="btn btn-sm btn-ghost" on:click={nextPage} disabled={entries.length < PAGE_SIZE}>Next →</button>
        </div>
    {/if}
</div>
