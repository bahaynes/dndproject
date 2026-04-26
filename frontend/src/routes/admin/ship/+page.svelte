<script lang="ts">
    import { api } from '$lib/api';
    import { onMount } from 'svelte';
    import type { Ship } from '$lib/types';
    let ship: Ship | null = null;
    let loading = true;
    let saving = false;
    let adjusting = false;
    let saveMsg = '';
    let adjustMsg = '';
    let saveError = '';
    let adjustError = '';

    // Edit form
    let editName = '';
    let editLevel = 1;
    let editEssence = 0;
    let editGold = 0;
    let editMaxHp = 100;
    let editCurrentHp = 100;
    let editMotd = '';

    // Adjust form
    let adjEssenceDelta = 0;
    let adjGoldDelta = 0;
    let adjHpDelta = 0;
    let adjDescription = '';

    onMount(loadShip);

    async function loadShip() {
        loading = true;
        try {
            ship = await api('GET', '/ship/');
            editName = ship!.name;
            editLevel = ship!.level;
            editEssence = ship!.essence;
            editGold = ship!.gold;
            editMaxHp = ship!.max_hp;
            editCurrentHp = ship!.current_hp;
            editMotd = ship!.motd ?? '';
        } catch (e) {}
        loading = false;
    }

    async function saveShip() {
        saving = true;
        saveMsg = '';
        saveError = '';
        try {
            ship = await api('PUT', '/ship/', { 
                name: editName, 
                level: editLevel, 
                essence: editEssence,
                gold: editGold,
                max_hp: editMaxHp,
                current_hp: editCurrentHp,
                motd: editMotd || null 
            });
            saveMsg = 'Ship configuration saved.';
        } catch (e) {
            saveError = e instanceof Error ? e.message : 'Failed to save.';
        }
        saving = false;
    }

    async function adjustShip() {
        if (!adjDescription.trim()) { adjustError = 'Description is required.'; return; }
        adjusting = true;
        adjustMsg = '';
        adjustError = '';
        try {
            ship = await api('POST', '/ship/adjust', { 
                essence_delta: adjEssenceDelta, 
                gold_delta: adjGoldDelta,
                hp_delta: adjHpDelta,
                description: adjDescription 
            });
            editEssence = ship!.essence;
            editGold = ship!.gold;
            editCurrentHp = ship!.current_hp;
            adjustMsg = 'Resources adjusted and ledger entry created.';
            adjEssenceDelta = 0;
            adjGoldDelta = 0;
            adjHpDelta = 0;
            adjDescription = '';
        } catch (e) {
            adjustError = e instanceof Error ? e.message : 'Adjustment failed.';
        }
        adjusting = false;
    }

    $: statusColor = ship?.status === 'critical' ? 'error' : ship?.status === 'low' ? 'warning' : 'success';
    $: levelPct = ship && ship.next_threshold && ship.next_threshold > 0
			? Math.round((ship.essence / ship.next_threshold) * 100)
			: 100;
	$: hpPct = ship && ship.max_hp && ship.max_hp > 0 
        ? Math.round((ship.current_hp / ship.max_hp) * 100) 
        : 100;
    $: hpColor = hpPct < 25 ? 'error' : hpPct < 50 ? 'warning' : 'success';
</script>

<div class="container mx-auto p-4 max-w-3xl">
    <div class="flex justify-between items-center mb-6 border-b border-base-content/10 pb-4">
        <h1 class="text-3xl font-bold font-[var(--font-cinzel)] tracking-tight text-primary">🚀 Ship Configuration</h1>
        <a href="/dashboard" class="btn btn-sm btn-ghost">← Dashboard</a>
    </div>

    {#if loading}
        <div class="flex justify-center py-16"><span class="loading loading-spinner loading-lg text-primary"></span></div>
    {:else}

    <!-- Current Status -->
    {#if ship}
    <div class="card bg-base-100 border border-base-content/10 shadow-md mb-6">
        <div class="card-body">
            <div class="flex items-center gap-3 mb-3">
                <span class="text-xl font-bold">{ship.name}</span>
                <span class="badge badge-outline">Level {ship.level}</span>
                <span class="badge badge-{statusColor} capitalize">{ship.status.replace('_', ' ')}</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div class="bg-base-200 p-3 rounded-lg">
                    <div class="text-xs opacity-60 uppercase tracking-wider mb-1">Essence</div>
                    <div class="text-lg font-bold text-primary">⚡ {ship.essence}</div>
                </div>
                <div class="bg-base-200 p-3 rounded-lg">
                    <div class="text-xs opacity-60 uppercase tracking-wider mb-1">Gold</div>
                    <div class="text-lg font-bold text-secondary">🪙 {ship.gold}</div>
                </div>
                <div class="bg-base-200 p-3 rounded-lg">
                    <div class="text-xs opacity-60 uppercase tracking-wider mb-1">Hull</div>
                    <div class="text-lg font-bold text-{hpColor}">❤️ {ship.current_hp} / {ship.max_hp}</div>
                </div>
            </div>

            <div class="space-y-4">
                <div>
                    <div class="flex justify-between text-xs opacity-70 mb-1">
                        {#if ship.next_threshold !== null}
                            <span>Level {ship.level} → {ship.level + 1}</span>
                            <span>{ship.essence} / {ship.next_threshold} Essence ({levelPct}%)</span>
                        {:else}
                            <span>Max Level</span><span>Level {ship.level}</span>
                        {/if}
                    </div>
                    <progress class="progress progress-primary w-full h-2" value={levelPct} max="100"></progress>
                </div>

                <div>
                    <div class="flex justify-between text-xs opacity-70 mb-1">
                        <span>Hull Integrity</span>
                        <span>{hpPct}%</span>
                    </div>
                    <progress class="progress progress-{hpColor} w-full h-2" value={hpPct} max="100"></progress>
                </div>
            </div>
            {#if ship.motd}<p class="text-sm opacity-60 mt-2 italic">"{ship.motd}"</p>{/if}
        </div>
    </div>
    {/if}

    <!-- Edit Form -->
    <div class="card bg-base-100 border border-base-content/10 shadow-md mb-6">
        <div class="card-body">
            <h2 class="card-title text-base">Edit Ship</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label class="form-control">
                    <div class="label"><span class="label-text">Ship Name</span></div>
                    <input class="input input-bordered input-sm" bind:value={editName} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Level</span></div>
                    <input class="input input-bordered input-sm" type="number" min="1" max="20" bind:value={editLevel} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Essence Reserve</span></div>
                    <input class="input input-bordered input-sm" type="number" min="0" bind:value={editEssence} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Ship Gold (War Chest)</span></div>
                    <input class="input input-bordered input-sm" type="number" min="0" bind:value={editGold} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Current HP</span></div>
                    <input class="input input-bordered input-sm" type="number" min="0" max={editMaxHp} bind:value={editCurrentHp} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Max HP</span></div>
                    <input class="input input-bordered input-sm" type="number" min="1" bind:value={editMaxHp} />
                </label>
                <label class="form-control md:col-span-2">
                    <div class="label"><span class="label-text">MOTD / Announcement</span></div>
                    <textarea class="textarea textarea-bordered textarea-sm" rows="2" bind:value={editMotd} placeholder="Leave blank to clear..."></textarea>
                </label>
            </div>
            {#if saveMsg}<div class="alert alert-success mt-3 text-sm">{saveMsg}</div>{/if}
            {#if saveError}<div class="alert alert-error mt-3 text-sm">{saveError}</div>{/if}
            <div class="card-actions justify-end mt-4">
                <button class="btn btn-primary btn-sm" on:click={saveShip} disabled={saving}>
                    {saving ? 'Saving...' : 'Save Configuration'}
                </button>
            </div>
        </div>
    </div>

    <!-- Adjust Resources -->
    <div class="card bg-base-100 border border-base-content/10 shadow-md">
        <div class="card-body">
            <h2 class="card-title text-base">Adjust Resources</h2>
            <p class="text-sm opacity-60 mb-3">Each adjustment creates an immutable ledger entry.</p>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <label class="form-control">
                    <div class="label"><span class="label-text">Essence Δ</span></div>
                    <input class="input input-bordered input-sm" type="number" bind:value={adjEssenceDelta} placeholder="-4 or +12" />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Gold Δ</span></div>
                    <input class="input input-bordered input-sm" type="number" bind:value={adjGoldDelta} placeholder="-100 or +500" />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">HP Δ</span></div>
                    <input class="input input-bordered input-sm" type="number" bind:value={adjHpDelta} placeholder="-25 or +10" />
                </label>
            </div>
            <label class="form-control mt-3">
                <div class="label"><span class="label-text">Description <span class="text-error">*</span></span></div>
                <input class="input input-bordered input-sm" bind:value={adjDescription} placeholder="e.g. Fuel burned on Hex 3 mission" />
            </label>
            {#if adjustMsg}<div class="alert alert-success mt-3 text-sm">{adjustMsg}</div>{/if}
            {#if adjustError}<div class="alert alert-error mt-3 text-sm">{adjustError}</div>{/if}
            <div class="card-actions justify-end mt-4">
                <button class="btn btn-warning btn-sm" on:click={adjustShip} disabled={adjusting}>
                    {adjusting ? 'Adjusting...' : 'Apply Adjustment'}
                </button>
            </div>
        </div>
    </div>

    {/if}
</div>
