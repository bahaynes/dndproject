<script lang="ts">
    import { auth } from '$lib/auth';
    import { onMount } from 'svelte';
    import { get } from 'svelte/store';
    import { API_BASE_URL } from '$lib/config';

    interface ReputationEvent {
        id: number;
        delta: number;
        description: string;
        session_id: number | null;
        created_at: string;
    }

    interface FactionReputation {
        id: number;
        faction_name: string;
        level: number;
        color: string | null;
        description: string | null;
        events: ReputationEvent[];
    }

    let reputations: FactionReputation[] = [];
    let loading = true;
    let isAdmin = false;

    // Create faction form
    let showCreateForm = false;
    let createName = '';
    let createColor = '#6b7280';
    let createDescription = '';
    let creating = false;
    let createError = '';

    // Adjust state
    let showAdjustFor: string | null = null;
    let adjustDelta = 1;
    let adjustDescription = '';
    let adjusting: string | null = null;

    // Delete confirm
    let confirmDeleteFor: string | null = null;
    let deleting: string | null = null;

    const MIN_LEVEL = -5;
    const MAX_LEVEL = 5;

    const LEVEL_LABELS: Record<number, string> = {
        5: 'Sworn Allies',
        4: 'Trusted',
        3: 'Friendly',
        2: 'Cooperative',
        1: 'Cautiously Warm',
        0: 'Neutral',
        '-1': 'Wary',
        '-2': 'Suspicious',
        '-3': 'Hostile',
        '-4': 'Enemies',
        '-5': 'Blood Feud',
    };

    auth.subscribe(v => { isAdmin = v.user?.role === 'admin'; });

    onMount(fetchReputations);

    async function fetchReputations() {
        loading = true;
        const { token } = get(auth);
        const res = await fetch(`${API_BASE_URL}/factions/`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) reputations = await res.json();
        loading = false;
    }

    async function submitCreate() {
        if (!createName.trim()) return;
        creating = true;
        createError = '';
        const { token } = get(auth);
        const res = await fetch(`${API_BASE_URL}/factions/`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                faction_name: createName.trim(),
                color: createColor,
                description: createDescription.trim() || null,
            }),
        });
        if (res.ok) {
            showCreateForm = false;
            createName = '';
            createColor = '#6b7280';
            createDescription = '';
            await fetchReputations();
        } else {
            const err = await res.json();
            createError = err.detail ?? 'Failed to create faction.';
        }
        creating = false;
    }

    async function submitAdjust(factionName: string) {
        if (!adjustDescription.trim()) return;
        adjusting = factionName;
        const { token } = get(auth);
        const res = await fetch(`${API_BASE_URL}/factions/${encodeURIComponent(factionName)}/adjust`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ delta: adjustDelta, description: adjustDescription.trim() }),
        });
        if (res.ok) {
            showAdjustFor = null;
            adjustDelta = 1;
            adjustDescription = '';
            await fetchReputations();
        }
        adjusting = null;
    }

    async function confirmDelete(factionName: string) {
        deleting = factionName;
        const { token } = get(auth);
        await fetch(`${API_BASE_URL}/factions/${encodeURIComponent(factionName)}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${token}` },
        });
        confirmDeleteFor = null;
        deleting = null;
        await fetchReputations();
    }

    function barFill(level: number): number {
        return ((level - MIN_LEVEL) / (MAX_LEVEL - MIN_LEVEL)) * 100;
    }

    function barColorClass(level: number): string {
        if (level >= 3) return 'bg-success';
        if (level >= 1) return 'bg-info';
        if (level === 0) return 'bg-base-content/30';
        if (level >= -2) return 'bg-warning';
        return 'bg-error';
    }

    function factionColor(rep: FactionReputation): string {
        return rep.color ?? '#6b7280';
    }

    function formatDate(iso: string): string {
        return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: '2-digit' });
    }
</script>

<div class="container mx-auto p-4 max-w-4xl">
    <div class="flex justify-between items-center mb-6 border-b border-base-content/10 pb-4">
        <div>
            <h1 class="text-3xl font-bold font-[var(--font-cinzel)] tracking-tight text-primary">
                Faction Standing
            </h1>
            <p class="text-sm opacity-50 mt-1">Current relations between Meridian's crew and the powers of the Rim.</p>
        </div>
        {#if isAdmin}
            <button
                class="btn btn-sm btn-outline btn-primary"
                on:click={() => { showCreateForm = !showCreateForm; createError = ''; }}
            >
                {showCreateForm ? 'Cancel' : '+ Add Faction'}
            </button>
        {/if}
    </div>

    <!-- Create faction form (admin only) -->
    {#if isAdmin && showCreateForm}
        <div class="card bg-base-200 border border-primary/20 mb-6">
            <div class="card-body">
                <h2 class="font-semibold text-sm mb-3 uppercase tracking-wide opacity-70">New Faction</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <label class="form-control">
                        <div class="label"><span class="label-text text-xs">Name</span></div>
                        <input
                            type="text"
                            bind:value={createName}
                            placeholder="e.g. The Syndicate"
                            class="input input-sm input-bordered"
                        />
                    </label>
                    <label class="form-control">
                        <div class="label"><span class="label-text text-xs">Color</span></div>
                        <div class="flex gap-2 items-center">
                            <input type="color" bind:value={createColor} class="w-10 h-9 rounded cursor-pointer border border-base-content/20 bg-transparent" />
                            <input type="text" bind:value={createColor} class="input input-sm input-bordered flex-1 font-mono" placeholder="#6b7280" />
                        </div>
                    </label>
                    <label class="form-control md:col-span-2">
                        <div class="label"><span class="label-text text-xs">Description <span class="opacity-40">(optional)</span></span></div>
                        <input
                            type="text"
                            bind:value={createDescription}
                            placeholder="One-line flavor text"
                            class="input input-sm input-bordered"
                        />
                    </label>
                </div>
                {#if createError}
                    <p class="text-error text-xs mt-2">{createError}</p>
                {/if}
                <div class="flex justify-end mt-3">
                    <button
                        class="btn btn-sm btn-primary"
                        disabled={creating || !createName.trim()}
                        on:click={submitCreate}
                    >
                        {creating ? 'Creating...' : 'Create Faction'}
                    </button>
                </div>
            </div>
        </div>
    {/if}

    {#if loading}
        <div class="flex justify-center py-16">
            <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>
    {:else if reputations.length === 0}
        <div class="text-center py-16 opacity-50">
            <p class="text-lg">No factions recorded.</p>
            {#if isAdmin}<p class="text-sm mt-1">Add one above to start tracking standing.</p>{/if}
        </div>
    {:else}
        <div class="space-y-4">
            {#each reputations as rep (rep.id)}
                {@const levelLabel = LEVEL_LABELS[rep.level] ?? 'Unknown'}
                <div
                    class="card bg-base-100 border border-base-content/10 overflow-hidden"
                    style="border-left: 4px solid {factionColor(rep)}"
                >
                    <div class="card-body">
                        <!-- Header row -->
                        <div class="flex items-start justify-between gap-3">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 flex-wrap">
                                    <span
                                        class="w-2.5 h-2.5 rounded-full flex-shrink-0"
                                        style="background-color: {factionColor(rep)}"
                                    ></span>
                                    <h2 class="font-bold text-base font-[var(--font-cinzel)]">{rep.faction_name}</h2>
                                    <span class="badge badge-sm badge-outline opacity-70">{levelLabel}</span>
                                </div>
                                {#if rep.description}
                                    <p class="text-xs opacity-50 mt-0.5 ml-4">{rep.description}</p>
                                {/if}
                            </div>
                            <div class="flex items-center gap-2 flex-shrink-0">
                                <span class="font-mono font-bold text-lg {rep.level > 0 ? 'text-success' : rep.level < 0 ? 'text-error' : 'opacity-40'}">
                                    {rep.level > 0 ? '+' : ''}{rep.level}
                                </span>
                                {#if isAdmin}
                                    <button
                                        class="btn btn-xs btn-ghost"
                                        on:click={() => {
                                            showAdjustFor = showAdjustFor === rep.faction_name ? null : rep.faction_name;
                                            adjustDelta = 1;
                                            adjustDescription = '';
                                        }}
                                    >
                                        Adjust
                                    </button>
                                    <button
                                        class="btn btn-xs btn-ghost text-error"
                                        on:click={() => { confirmDeleteFor = rep.faction_name; }}
                                    >
                                        ✕
                                    </button>
                                {/if}
                            </div>
                        </div>

                        <!-- Reputation bar -->
                        <div class="w-full bg-base-300 rounded-full h-2 mt-2">
                            <div
                                class="h-2 rounded-full transition-all duration-500 {barColorClass(rep.level)}"
                                style="width: {barFill(rep.level)}%"
                            ></div>
                        </div>

                        <!-- Admin adjust panel -->
                        {#if isAdmin && showAdjustFor === rep.faction_name}
                            <div class="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2 border-t border-base-content/10 pt-3">
                                <div class="flex items-center gap-2">
                                    <label class="text-xs opacity-60 w-14 flex-shrink-0">Change</label>
                                    <input
                                        type="number"
                                        min="-10"
                                        max="10"
                                        bind:value={adjustDelta}
                                        class="input input-xs input-bordered w-20 font-mono"
                                    />
                                </div>
                                <div class="flex items-center gap-2 sm:col-span-2">
                                    <label class="text-xs opacity-60 w-14 flex-shrink-0">Reason</label>
                                    <input
                                        type="text"
                                        bind:value={adjustDescription}
                                        placeholder="What happened?"
                                        class="input input-xs input-bordered flex-1"
                                    />
                                    <button
                                        class="btn btn-xs btn-primary flex-shrink-0"
                                        disabled={!!adjusting || !adjustDescription.trim()}
                                        on:click={() => submitAdjust(rep.faction_name)}
                                    >
                                        {adjusting === rep.faction_name ? '...' : 'Save'}
                                    </button>
                                </div>
                            </div>
                        {/if}

                        <!-- Delete confirm -->
                        {#if isAdmin && confirmDeleteFor === rep.faction_name}
                            <div class="mt-3 flex items-center gap-3 border-t border-error/20 pt-3">
                                <p class="text-xs text-error flex-1">Remove <strong>{rep.faction_name}</strong> and all its history?</p>
                                <button
                                    class="btn btn-xs btn-error"
                                    disabled={deleting === rep.faction_name}
                                    on:click={() => confirmDelete(rep.faction_name)}
                                >
                                    {deleting === rep.faction_name ? '...' : 'Delete'}
                                </button>
                                <button class="btn btn-xs btn-ghost" on:click={() => { confirmDeleteFor = null; }}>Cancel</button>
                            </div>
                        {/if}

                        <!-- Full event log -->
                        {#if rep.events.length > 0}
                            <div class="mt-3 border-t border-base-content/5 pt-3 space-y-1">
                                <p class="text-xs font-semibold uppercase opacity-40 tracking-wide mb-2">History</p>
                                {#each rep.events as event}
                                    <div class="flex items-baseline gap-2 text-xs">
                                        <span class="font-mono font-bold w-8 text-right flex-shrink-0 {event.delta > 0 ? 'text-success' : 'text-error'}">
                                            {event.delta > 0 ? '+' : ''}{event.delta}
                                        </span>
                                        <span class="flex-1 opacity-70">{event.description}</span>
                                        <span class="opacity-40 flex-shrink-0">{formatDate(event.created_at)}</span>
                                    </div>
                                {/each}
                            </div>
                        {:else}
                            <p class="text-xs opacity-30 mt-2">No history yet.</p>
                        {/if}
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>
