<script lang="ts">
    import { auth } from '$lib/auth';
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { API_BASE_URL } from '$lib/config';
    import FactionReputationTracker from '$lib/components/FactionReputationTracker.svelte';
    import type { Ship, LedgerEntry, CharacterRosterEntry, GameSessionWithPlayers } from '$lib/types';

    let user: any = null;
    let campaign: any = null;
    let authToken: string | null = null;

    let ship: Ship | null = null;
    let ledgerEntries: LedgerEntry[] = [];
    let roster: CharacterRosterEntry[] = [];
    let upcomingSessions: GameSessionWithPlayers[] = [];
    let loading = true;

    auth.subscribe(value => {
        user = value.user;
        campaign = value.campaign;
        authToken = value.token;
    });

    onMount(async () => {
        if (!user && !localStorage.getItem('accessToken')) {
            goto('/login');
            return;
        } else if (user && !campaign) {
            goto('/campaigns');
            return;
        }
        if (authToken) await loadData();
    });

    async function loadData() {
        const headers = { Authorization: `Bearer ${authToken}` };
        const [shipRes, ledgerRes, rosterRes, sessionsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/ship/`, { headers }),
            fetch(`${API_BASE_URL}/ledger/?limit=5`, { headers }),
            fetch(`${API_BASE_URL}/characters/roster`, { headers }),
            fetch(`${API_BASE_URL}/sessions/?limit=100`, { headers }),
        ]);
        if (shipRes.ok) ship = await shipRes.json();
        if (ledgerRes.ok) ledgerEntries = await ledgerRes.json();
        if (rosterRes.ok) roster = await rosterRes.json();
        if (sessionsRes.ok) {
            const all: GameSessionWithPlayers[] = await sessionsRes.json();
            upcomingSessions = all
                .filter(s => s.status !== 'Completed' && s.status !== 'Cancelled')
                .sort((a, b) => new Date(a.session_date).getTime() - new Date(b.session_date).getTime())
                .slice(0, 3);
        }
        loading = false;
    }

    $: fuelPct = ship ? Math.round((ship.fuel / ship.max_fuel) * 100) : 0;
    $: statusColor = ship?.status === 'critical' ? 'error' : ship?.status === 'low_fuel' ? 'warning' : 'success';

    function formatDate(iso: string) {
        return new Date(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
    }

    function formatDelta(n: number) {
        if (n === 0) return null;
        return n > 0 ? `+${n}` : `${n}`;
    }

    function eventTypeLabel(type: string) {
        const labels: Record<string, string> = {
            MissionCompleted: '✅ Mission Complete',
            MissionFailed: '❌ Mission Failed',
            Purchase: '🛒 Purchase',
            RewardDistribution: '🎁 Rewards',
            AdminAdjustment: '⚙️ Adjustment',
            ShipAdjustment: '🚀 Ship Adjust',
            CharacterDeath: '💀 Death',
            LevelUp: '⬆️ Level Up',
        };
        return labels[type] ?? type;
    }
</script>

<div class="container mx-auto p-4 max-w-6xl">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6 border-b border-base-content/10 pb-4">
        <h1 class="text-3xl font-bold font-[var(--font-cinzel)] tracking-tight text-primary">
            {campaign ? campaign.name : 'Dashboard'}
        </h1>
        {#if campaign}
            <div class="hidden md:block text-xs opacity-50 uppercase font-bold text-right">Active Campaign</div>
        {/if}
    </div>

    {#if loading}
        <div class="flex justify-center py-16"><span class="loading loading-spinner loading-lg text-primary"></span></div>
    {:else if user}

        <!-- Ship Status Panel -->
        {#if ship}
        <div class="card bg-base-100 shadow-md border border-base-content/10 mb-6">
            <div class="card-body">
                <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div class="flex items-center gap-3">
                        <span class="text-2xl font-bold font-[var(--font-cinzel)]">🚀 {ship.name}</span>
                        <span class="badge badge-outline">Level {ship.level}</span>
                        <span class="badge badge-{statusColor} capitalize">{ship.status.replace('_', ' ')}</span>
                    </div>
                    <div class="flex gap-6 text-sm font-semibold">
                        <span>💎 {ship.crystals} Crystals</span>
                        <span>💰 {ship.credits.toLocaleString()} Credits</span>
                    </div>
                </div>

                <!-- Fuel gauge -->
                <div class="mb-2">
                    <div class="flex justify-between text-xs opacity-70 mb-1">
                        <span>Fuel</span>
                        <span>{ship.fuel} / {ship.max_fuel}</span>
                    </div>
                    <progress
                        class="progress progress-{statusColor} w-full h-4"
                        value={fuelPct}
                        max="100"
                    ></progress>
                </div>

                {#if ship.motd}
                    <div class="alert alert-info mt-3 text-sm">
                        <span>📢 {ship.motd}</span>
                    </div>
                {/if}
            </div>
        </div>
        {/if}

        <!-- Middle row: Upcoming Sessions + Latest Ledger -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">

            <!-- Upcoming Sessions -->
            <div class="card bg-base-100 shadow-md border border-base-content/10">
                <div class="card-body">
                    <div class="flex justify-between items-center mb-3">
                        <h2 class="card-title text-base">📅 Upcoming Sessions</h2>
                        <a href="/sessions" class="text-xs text-primary hover:underline">View all →</a>
                    </div>
                    {#if upcomingSessions.length === 0}
                        <p class="text-sm opacity-60">No upcoming sessions scheduled.</p>
                    {:else}
                        <div class="space-y-3">
                            {#each upcomingSessions as session}
                            <div class="border border-base-content/10 rounded-lg p-3">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <p class="font-semibold text-sm">{session.name}</p>
                                        {#if session.confirmed_mission}
                                            <p class="text-xs opacity-70">📜 {session.confirmed_mission.name}</p>
                                        {/if}
                                    </div>
                                    <span class="badge badge-sm badge-outline">{formatDate(session.session_date)}</span>
                                </div>
                                <div class="flex items-center justify-between mt-2">
                                    <span class="text-xs opacity-60">
                                        {session.players.length}/{session.min_players}+ crew
                                    </span>
                                    <span class="badge badge-sm capitalize">{session.status}</span>
                                </div>
                            </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>

            <!-- Latest Ledger -->
            <div class="card bg-base-100 shadow-md border border-base-content/10">
                <div class="card-body">
                    <div class="flex justify-between items-center mb-3">
                        <h2 class="card-title text-base">📖 Latest Ledger</h2>
                        <a href="/ledger" class="text-xs text-primary hover:underline">View all →</a>
                    </div>
                    {#if ledgerEntries.length === 0}
                        <p class="text-sm opacity-60">No ledger entries yet.</p>
                    {:else}
                        <div class="space-y-2">
                            {#each ledgerEntries as entry}
                            <div class="flex justify-between items-start text-sm border-b border-base-content/5 pb-2">
                                <div class="flex-1 min-w-0">
                                    <p class="font-medium truncate">{eventTypeLabel(entry.event_type)}</p>
                                    <p class="text-xs opacity-60 truncate">{entry.description}</p>
                                </div>
                                <div class="text-right text-xs ml-2 flex-shrink-0 space-y-0.5">
                                    {#if formatDelta(entry.fuel_delta)}<span class="opacity-70">⛽ {formatDelta(entry.fuel_delta)}</span><br>{/if}
                                    {#if formatDelta(entry.credit_delta)}<span class="opacity-70">💰 {formatDelta(entry.credit_delta)}</span><br>{/if}
                                    {#if formatDelta(entry.crystal_delta)}<span class="opacity-70">💎 {formatDelta(entry.crystal_delta)}</span>{/if}
                                </div>
                            </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>

        </div>

        <!-- Bottom: Active Crew + Nav Links -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">

            <!-- Active Crew -->
            <div class="md:col-span-2 card bg-base-100 shadow-md border border-base-content/10">
                <div class="card-body">
                    <div class="flex justify-between items-center mb-3">
                        <h2 class="card-title text-base">👥 Active Crew</h2>
                        <a href="/roster" class="text-xs text-primary hover:underline">Full roster →</a>
                    </div>
                    {#if roster.filter(c => c.status === 'Active').length === 0}
                        <p class="text-sm opacity-60">No active crew members.</p>
                    {:else}
                        <div class="overflow-x-auto">
                            <table class="table table-xs">
                                <thead>
                                    <tr><th>Name</th><th>Class</th><th>Lvl</th><th>Player</th><th>Missions</th></tr>
                                </thead>
                                <tbody>
                                    {#each roster.filter(c => c.status === 'Active').slice(0, 8) as char}
                                    <tr>
                                        <td class="font-medium">{char.name}</td>
                                        <td class="opacity-70">{char.class_name ?? '—'}</td>
                                        <td>{char.level}</td>
                                        <td class="opacity-70">{char.owner_username ?? '—'}</td>
                                        <td>{char.missions_completed}</td>
                                    </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    {/if}
                </div>
            </div>

            <!-- Quick Nav -->
            <div class="space-y-4">
                <div class="card bg-base-100 shadow-md border border-base-content/10">
                    <div class="card-body p-4">
                        <h2 class="font-semibold mb-2 text-sm">Quick Links</h2>
                        <ul class="space-y-1">
                            <li><a href="/characters" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">⚔️ My Character</a></li>
                            <li><a href="/missions" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">📋 Mission Board</a></li>
                            <li><a href="/sessions" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">📅 Sessions</a></li>
                            <li><a href="/store" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">🛒 Store</a></li>
                            <li><a href="/maps" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">🗺️ Maps</a></li>
                            <li><a href="/factions" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">⚖️ Factions</a></li>
                            <li><a href="/ledger" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">📖 Ledger</a></li>
                            <li><a href="/roster" class="block p-2 hover:bg-base-200 rounded text-sm text-primary font-medium">👥 Crew Roster</a></li>
                        </ul>
                    </div>
                </div>

                <div class="card bg-base-100 shadow-md border border-base-content/10">
                    <div class="card-body p-4">
                        <FactionReputationTracker />
                    </div>
                </div>
            </div>

        </div>

        <!-- Admin Tools -->
        {#if user.role === 'admin'}
        <div class="card bg-error/10 border border-error/20 shadow-md">
            <div class="card-body">
                <h2 class="card-title text-error/80 text-base">⚙️ Dungeon Master Tools</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <a href="/admin/sessions" class="btn btn-sm btn-outline btn-error">Sessions</a>
                    <a href="/admin/missions" class="btn btn-sm btn-outline btn-error">Missions</a>
                    <a href="/admin/items" class="btn btn-sm btn-outline btn-error">Items</a>
                    <a href="/admin/ship" class="btn btn-sm btn-outline btn-error">Ship Config</a>
                    <a href="/admin/maps" class="btn btn-sm btn-outline btn-error">Maps</a>
                </div>
            </div>
        </div>
        {/if}

    {:else}
        <p class="mt-4">Loading user information...</p>
    {/if}
</div>
