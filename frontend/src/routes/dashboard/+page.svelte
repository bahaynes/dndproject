<script lang="ts">
    import { auth } from '$lib/auth';
    import { api } from '$lib/api';
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import Modal from '$lib/components/Modal.svelte';
    import type { Ship, GameSessionWithPlayers, Mission } from '$lib/types';

    let ship: Ship | null = null;
    let upcomingSessions: GameSessionWithPlayers[] = [];
    let availableMissions: Mission[] = [];
    let loading = true;
    let showOnboarding = false;
    let backingError: string | null = null;

    // Propose modal
    let showProposeModal = false;
    let selectedSessionId: number | null = null;
    let selectedMissionId: number | null = null;
    let dataLoaded = false;

    $: user = $auth.user;
    $: campaign = $auth.campaign;
    $: char = user?.active_character;
    $: myCharacterId = char?.id;

    onMount(() => {
        if (!localStorage.getItem('accessToken')) {
            goto('/login');
        }
    });

    // Fires when auth hydrates (may be before or after onMount)
    $: if ($auth.token && !dataLoaded) {
        dataLoaded = true;
        loadData();
    }

    $: if ($auth.isAuthenticated && !$auth.campaign) {
        goto('/campaigns');
    }

    function dismissOnboarding() {
        showOnboarding = false;
        localStorage.setItem('onboarding_dismissed', '1');
    }

    $: if (!loading && user && !user.active_character) {
        if (!localStorage.getItem('onboarding_dismissed')) {
            showOnboarding = true;
        }
    }

    async function loadData() {
        const [s, sessions, missions] = await Promise.all([
            api('GET', '/ship/').catch(() => null),
            api('GET', '/sessions/').catch(() => []),
            api('GET', '/missions/').catch(() => []),
        ]);
        ship = s;
        const all: GameSessionWithPlayers[] = sessions ?? [];
        upcomingSessions = all
            .filter(s => s.status !== 'Completed' && s.status !== 'Cancelled')
            .sort((a, b) => new Date(a.session_date).getTime() - new Date(b.session_date).getTime());
        availableMissions = (missions ?? []).filter((m: Mission) => !m.is_retired && m.is_discoverable);
        loading = false;
    }

    function isBacking(proposalId: number): boolean {
        if (!myCharacterId) return false;
        for (const session of upcomingSessions) {
            const proposal = session.proposals.find(p => p.id === proposalId);
            if (proposal) return proposal.backers.some(b => b.id === myCharacterId);
        }
        return false;
    }

    async function toggleBacking(proposalId: number) {
        backingError = null;
        try {
            await api('POST', `/sessions/proposals/${proposalId}/toggle_back`);
            await loadData();
        } catch (e) {
            backingError = e instanceof Error ? e.message : 'Failed to update backing.';
        }
    }

    async function proposeMission() {
        if (!selectedSessionId || !selectedMissionId) return;
        try {
            await api('POST', '/sessions/proposals', {
                session_id: selectedSessionId,
                mission_id: selectedMissionId,
            });
            showProposeModal = false;
            await loadData();
        } catch (e) {
            backingError = e instanceof Error ? e.message : 'Failed to propose mission.';
        }
    }

    function formatDate(iso: string) {
        return new Date(iso).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
    }

    function inCooldown(m: Mission): boolean {
        if (!m.last_run_date) return false;
        return Date.now() - new Date(m.last_run_date).getTime() < m.cooldown_days * 86400000;
    }

    $: statusColor = ship?.status === 'critical' ? 'error' : ship?.status === 'low' ? 'warning' : 'success';
    $: levelPct = ship ? (ship.next_threshold ? Math.round((ship.essence / ship.next_threshold) * 100) : 100) : 0;
</script>

<div class="min-h-screen">

    {#if loading}
        <div class="flex justify-center py-32">
            <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>
    {:else if user}

    <!-- Character Identity Banner -->
    <div class="border-b border-base-content/10 bg-base-200/60 px-4 py-6">
        <div class="container mx-auto max-w-5xl">
            {#if char}
                <div class="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <p class="text-xs uppercase tracking-widest opacity-50 mb-1">Active Crew Member</p>
                        <h1 class="text-3xl font-bold font-[var(--font-cinzel)] text-primary tracking-tight">
                            {char.name}
                        </h1>
                        <div class="flex items-center gap-3 mt-1 text-sm opacity-70">
                            {#if char.class_name}<span>{char.class_name}</span><span class="opacity-30">·</span>{/if}
                            <span>Level {char.level}</span>
                            <span class="opacity-30">·</span>
                            <span>{char.missions_completed} mission{char.missions_completed !== 1 ? 's' : ''} completed</span>
                        </div>
                    </div>
                    <div class="flex flex-col items-end gap-1">
                        {#if ship}
                            <div class="flex items-center gap-2">
                                <span class="text-xs opacity-50">Ship Essence</span>
                                <span class="badge badge-{statusColor} badge-sm">⚡ {ship.essence}</span>
                            </div>
                            {#if ship.next_threshold}
                                <div class="flex items-center gap-2 text-xs opacity-50">
                                    <span>Level {ship.level} → {ship.level + 1}</span>
                                    <progress class="progress progress-primary w-24 h-1.5" value={levelPct} max="100"></progress>
                                </div>
                            {/if}
                        {/if}
                        {#if ship?.motd}
                            <p class="text-xs italic opacity-50 max-w-xs text-right">"{ship.motd}"</p>
                        {/if}
                    </div>
                </div>
            {:else}
                <div class="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <h1 class="text-3xl font-bold font-[var(--font-cinzel)] text-primary tracking-tight">
                            {campaign?.name ?? 'The Inheritors'}
                        </h1>
                        <p class="text-sm opacity-60 mt-1">You haven't joined the crew yet.</p>
                    </div>
                    <a href="/characters" class="btn btn-primary btn-sm">Create Your Character →</a>
                </div>
            {/if}
        </div>
    </div>

    <div class="container mx-auto max-w-5xl px-4 py-8 space-y-10">

        <!-- Session Board — Visual Centerpiece -->
        <section>
            <div class="flex justify-between items-baseline mb-4">
                <div>
                    <h2 class="text-xl font-bold font-[var(--font-cinzel)] text-primary">Mission Board</h2>
                    <p class="text-xs opacity-50 mt-0.5">Back a proposal to put it on the slate. Needs {upcomingSessions[0]?.min_players ?? 4} crew minimum.</p>
                </div>
                <a href="/sessions" class="text-xs text-primary hover:underline opacity-70">All sessions →</a>
            </div>

            {#if backingError}
                <div class="alert alert-error mb-4 text-sm">{backingError}</div>
            {/if}

            {#if upcomingSessions.length === 0}
                <div class="rounded-xl border border-base-content/10 bg-base-200/40 p-8 text-center">
                    <p class="text-sm opacity-50 italic">No sessions on the board. The DM will post one soon.</p>
                </div>
            {:else}
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {#each upcomingSessions as session}
                    <div class="card bg-base-100 border border-base-content/10 shadow-sm">
                        <div class="card-body p-4">
                            <!-- Session header -->
                            <div class="flex justify-between items-start mb-3">
                                <div>
                                    <h3 class="font-bold font-[var(--font-cinzel)] text-base leading-tight">{session.name}</h3>
                                    <p class="text-xs opacity-50 mt-0.5">📅 {formatDate(session.session_date)}</p>
                                </div>
                                <span class="badge badge-sm badge-outline capitalize shrink-0">{session.status}</span>
                            </div>

                            {#if session.status === 'Confirmed' && session.confirmed_mission}
                                <!-- Confirmed session -->
                                <div class="rounded-lg border border-success/20 bg-success/10 p-3">
                                    <p class="text-xs font-bold uppercase tracking-widest text-success/70 mb-1">Confirmed</p>
                                    <p class="font-bold font-[var(--font-cinzel)]">{session.confirmed_mission.name}</p>
                                    {#if session.confirmed_mission.tier}
                                        <span class="badge badge-xs badge-outline mt-1">{session.confirmed_mission.tier}</span>
                                    {/if}
                                    <div class="flex flex-wrap gap-1 mt-2">
                                        {#each session.players as player}
                                            <span class="badge badge-ghost badge-xs">{player.name}</span>
                                        {/each}
                                    </div>
                                </div>
                            {:else}
                                <!-- Proposals -->
                                <div class="space-y-3">
                                    {#each session.proposals as proposal}
                                    <div class="rounded-lg border border-base-content/5 bg-base-200/50 p-3">
                                        <div class="flex justify-between items-start mb-1">
                                            <span class="font-semibold text-sm">{proposal.mission.name}</span>
                                            <button
                                                class="btn btn-xs shrink-0 ml-2 {isBacking(proposal.id) ? 'btn-secondary' : 'btn-outline btn-primary'}"
                                                on:click={() => toggleBacking(proposal.id)}
                                                disabled={!myCharacterId}
                                            >
                                                {isBacking(proposal.id) ? '✓ Backing' : 'Back This'}
                                            </button>
                                        </div>
                                        {#if proposal.mission.tier}
                                            <span class="badge badge-xs badge-outline opacity-60">{proposal.mission.tier}</span>
                                        {/if}
                                        <div class="mt-2">
                                            <progress
                                                class="progress progress-primary w-full h-1.5"
                                                value={proposal.backers.length}
                                                max={session.min_players}
                                            ></progress>
                                            <p class="text-xs opacity-50 mt-0.5">{proposal.backers.length} / {session.min_players} crew</p>
                                        </div>
                                    </div>
                                    {/each}

                                    {#if session.proposals.length === 0}
                                        <p class="text-xs italic opacity-40 text-center py-2">No proposals yet.</p>
                                    {/if}
                                </div>

                                <div class="mt-3">
                                    <button
                                        class="btn btn-ghost btn-xs w-full border border-base-content/10"
                                        disabled={!myCharacterId}
                                        on:click={() => { selectedSessionId = session.id; showProposeModal = true; }}
                                    >
                                        + Propose a Mission
                                    </button>
                                </div>
                            {/if}
                        </div>
                    </div>
                    {/each}
                </div>
            {/if}
        </section>

        <!-- Available Missions -->
        {#if availableMissions.length > 0}
        <section>
            <div class="flex justify-between items-baseline mb-4">
                <div>
                    <h2 class="text-xl font-bold font-[var(--font-cinzel)] text-primary">Available Contracts</h2>
                    <p class="text-xs opacity-50 mt-0.5">Missions cleared for dispatch from Laissetable.</p>
                </div>
                <a href="/missions" class="text-xs text-primary hover:underline opacity-70">Full board →</a>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {#each availableMissions.slice(0, 6) as mission}
                <div class="rounded-lg border border-base-content/10 bg-base-100 p-3 {inCooldown(mission) ? 'opacity-50' : ''}">
                    <div class="flex justify-between items-start gap-2">
                        <p class="font-semibold text-sm leading-tight">{mission.name}</p>
                        {#if inCooldown(mission)}
                            <span class="badge badge-xs badge-ghost shrink-0">❄️ Cooldown</span>
                        {/if}
                    </div>
                    <div class="flex gap-1 mt-1.5 flex-wrap">
                        {#if mission.tier}<span class="badge badge-xs badge-outline">{mission.tier}</span>{/if}
                        {#if mission.region}<span class="badge badge-xs badge-ghost opacity-60">{mission.region}</span>{/if}
                    </div>
                    {#if mission.description}
                        <p class="text-xs opacity-50 mt-1.5 line-clamp-2">{mission.description}</p>
                    {/if}
                </div>
                {/each}
            </div>
        </section>
        {/if}

        <!-- Bottom row: Ship + Quick Nav + Admin -->
        <section class="grid grid-cols-1 md:grid-cols-3 gap-4">

            <!-- Ship compact -->
            {#if ship}
            <div class="card bg-base-100 border border-base-content/10 shadow-sm">
                <div class="card-body p-4">
                    <h3 class="font-bold text-sm font-[var(--font-cinzel)] mb-2">🚀 {ship.name}</h3>
                    <div class="flex items-center justify-between text-xs mb-1">
                        <span class="opacity-60">⚡ Essence Reserve</span>
                        <span class="badge badge-{statusColor} badge-xs">{ship.essence}</span>
                    </div>
                    {#if ship.next_threshold}
                        <progress class="progress progress-primary w-full h-1.5" value={levelPct} max="100"></progress>
                        <p class="text-xs opacity-40 mt-1">Level {ship.level} → {ship.level + 1} · {ship.essence_to_next_level} to go</p>
                    {:else}
                        <p class="text-xs opacity-40 mt-1">Max Level</p>
                    {/if}
                    <p class="text-xs opacity-40 mt-1">Long rest: {ship.long_rest_cost} Essence</p>
                </div>
            </div>
            {/if}

            <!-- Quick Nav -->
            <div class="card bg-base-100 border border-base-content/10 shadow-sm">
                <div class="card-body p-4">
                    <h3 class="font-bold text-sm font-[var(--font-cinzel)] mb-2">Navigation</h3>
                    <div class="grid grid-cols-2 gap-1 text-xs">
                        <a href="/characters" class="p-1.5 hover:bg-base-200 rounded text-primary">⚔️ Character</a>
                        <a href="/sessions" class="p-1.5 hover:bg-base-200 rounded text-primary">📅 Sessions</a>
                        <a href="/missions" class="p-1.5 hover:bg-base-200 rounded text-primary">📋 Missions</a>
                        <a href="/store" class="p-1.5 hover:bg-base-200 rounded text-primary">🛒 Store</a>
                        <a href="/maps" class="p-1.5 hover:bg-base-200 rounded text-primary">🗺️ Maps</a>
                        <a href="/factions" class="p-1.5 hover:bg-base-200 rounded text-primary">⚖️ Factions</a>
                        <a href="/ledger" class="p-1.5 hover:bg-base-200 rounded text-primary">📖 Ledger</a>
                        <a href="/roster" class="p-1.5 hover:bg-base-200 rounded text-primary">👥 Roster</a>
                    </div>
                </div>
            </div>

            <!-- Admin Tools -->
            {#if user.role === 'admin'}
            <div class="card bg-error/5 border border-error/20 shadow-sm">
                <div class="card-body p-4">
                    <h3 class="font-bold text-sm font-[var(--font-cinzel)] text-error/70 mb-2">⚙️ DM Tools</h3>
                    <div class="space-y-1">
                        <a href="/admin/sessions" class="btn btn-xs btn-outline btn-error w-full justify-start">Sessions</a>
                        <a href="/admin/missions" class="btn btn-xs btn-outline btn-error w-full justify-start">Missions</a>
                        <a href="/admin/items" class="btn btn-xs btn-outline btn-error w-full justify-start">Items</a>
                        <a href="/admin/ship" class="btn btn-xs btn-outline btn-error w-full justify-start">Ship Config</a>
                        <a href="/admin/maps" class="btn btn-xs btn-outline btn-error w-full justify-start">Maps</a>
                    </div>
                </div>
            </div>
            {/if}

        </section>

    </div>
    {:else}
        <p class="p-8 opacity-50">Loading...</p>
    {/if}
</div>

<!-- Propose Mission Modal -->
<Modal show={showProposeModal} title="Propose a Mission" onClose={() => showProposeModal = false}>
    <div class="form-control w-full">
        <label class="label" for="mission-select">
            <span class="label-text">Select a Mission</span>
        </label>
        <select id="mission-select" bind:value={selectedMissionId} class="select select-bordered w-full">
            <option value={null}>— Pick a Mission —</option>
            {#each availableMissions as mission}
                <option value={mission.id} disabled={inCooldown(mission)}>
                    {mission.name} {mission.tier ? `(${mission.tier})` : ''}{inCooldown(mission) ? ' — ❄️ Cooldown' : ''}
                </option>
            {/each}
        </select>
        <p class="mt-3 text-sm opacity-60 italic">
            Proposing adds you as the first backer.
        </p>
    </div>
    <div slot="action">
        <button class="btn btn-primary w-full" on:click={proposeMission} disabled={!selectedMissionId}>
            Propose Now
        </button>
    </div>
</Modal>

<!-- Onboarding modal -->
{#if showOnboarding}
<div class="modal modal-open">
    <div class="modal-box max-w-lg">
        <h3 class="font-bold text-2xl font-[var(--font-cinzel)] text-primary mb-1">Welcome aboard.</h3>
        <p class="text-sm opacity-60 mb-4">— Meridian</p>
        <div class="prose prose-sm max-w-none opacity-80 mb-6">
            <p>
                "New crew. Good. I'll keep this brief because I always do.
                You're sworn to this ship. That means you share in what we earn
                and what we spend. The ledger doesn't lie, and I don't either —
                not about reserves, anyway."
            </p>
            <p>
                "First thing: make yourself a character record. I need to know
                who's on my manifest. After that, check the mission board.
                Vote on what runs. Show up when the session starts."
            </p>
            <p class="text-xs opacity-60">
                "Questions? Read the briefing docs. After that, ask your crewmates.
                After that, ask me — but I'll answer the question I think you're
                actually asking, not the one you said."
            </p>
        </div>
        <div class="flex flex-col gap-3">
            <a href="/characters" class="btn btn-primary w-full" on:click={dismissOnboarding}>
                Create Your Character
            </a>
            <div class="divider text-xs opacity-40">or read first</div>
            <div class="flex gap-2">
                <a href="https://docs.google.com/document" target="_blank" rel="noopener" class="btn btn-outline btn-sm flex-1">
                    📖 World Bible
                </a>
                <a href="/missions" class="btn btn-outline btn-sm flex-1" on:click={dismissOnboarding}>
                    📋 Mission Board
                </a>
            </div>
            <button class="btn btn-ghost btn-xs opacity-50 mt-2" on:click={dismissOnboarding}>
                Dismiss — I know what I'm doing
            </button>
        </div>
    </div>
    <button class="modal-backdrop" aria-label="Close" on:click={dismissOnboarding}></button>
</div>
{/if}
