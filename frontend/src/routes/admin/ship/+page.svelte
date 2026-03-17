<script lang="ts">
    import { auth } from '$lib/auth';
    import { onMount } from 'svelte';
    import { API_BASE_URL } from '$lib/config';
    import type { Ship } from '$lib/types';

    let authToken: string | null = null;
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
    let editFuel = 100;
    let editMaxFuel = 100;
    let editCrystals = 0;
    let editCredits = 0;
    let editMotd = '';

    // Adjust form
    let adjFuelDelta = 0;
    let adjCrystalDelta = 0;
    let adjCreditDelta = 0;
    let adjDescription = '';

    auth.subscribe(v => { authToken = v.token; });
    onMount(loadShip);

    async function loadShip() {
        loading = true;
        const res = await fetch(`${API_BASE_URL}/ship/`, {
            headers: { Authorization: `Bearer ${authToken}` },
        });
        if (res.ok) {
            ship = await res.json();
            editName = ship!.name;
            editLevel = ship!.level;
            editFuel = ship!.fuel;
            editMaxFuel = ship!.max_fuel;
            editCrystals = ship!.crystals;
            editCredits = ship!.credits;
            editMotd = ship!.motd ?? '';
        }
        loading = false;
    }

    async function saveShip() {
        saving = true;
        saveMsg = '';
        saveError = '';
        const res = await fetch(`${API_BASE_URL}/ship/`, {
            method: 'PUT',
            headers: { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: editName, level: editLevel, fuel: editFuel, max_fuel: editMaxFuel,
                crystals: editCrystals, credits: editCredits, motd: editMotd || null,
            }),
        });
        if (res.ok) {
            ship = await res.json();
            saveMsg = 'Ship configuration saved.';
        } else {
            const err = await res.json();
            saveError = err.detail ?? 'Failed to save.';
        }
        saving = false;
    }

    async function adjustShip() {
        if (!adjDescription.trim()) { adjustError = 'Description is required.'; return; }
        adjusting = true;
        adjustMsg = '';
        adjustError = '';
        const res = await fetch(`${API_BASE_URL}/ship/adjust`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${authToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                fuel_delta: adjFuelDelta,
                crystal_delta: adjCrystalDelta,
                credit_delta: adjCreditDelta,
                description: adjDescription,
            }),
        });
        if (res.ok) {
            ship = await res.json();
            editFuel = ship!.fuel;
            editCrystals = ship!.crystals;
            editCredits = ship!.credits;
            adjustMsg = 'Resources adjusted and ledger entry created.';
            adjFuelDelta = 0; adjCrystalDelta = 0; adjCreditDelta = 0; adjDescription = '';
        } else {
            const err = await res.json();
            adjustError = err.detail ?? 'Adjustment failed.';
        }
        adjusting = false;
    }

    $: fuelPct = ship ? Math.round((ship.fuel / ship.max_fuel) * 100) : 0;
    $: statusColor = ship?.status === 'critical' ? 'error' : ship?.status === 'low_fuel' ? 'warning' : 'success';
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
            <div class="mb-2">
                <div class="flex justify-between text-xs opacity-70 mb-1"><span>Fuel</span><span>{ship.fuel}/{ship.max_fuel}</span></div>
                <progress class="progress progress-{statusColor} w-full" value={fuelPct} max="100"></progress>
            </div>
            <div class="flex gap-6 text-sm mt-1">
                <span>💎 {ship.crystals} Crystals</span>
                <span>💰 {ship.credits.toLocaleString()} Credits</span>
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
                    <div class="label"><span class="label-text">Current Fuel</span></div>
                    <input class="input input-bordered input-sm" type="number" min="0" bind:value={editFuel} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Max Fuel</span></div>
                    <input class="input input-bordered input-sm" type="number" min="1" bind:value={editMaxFuel} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Crystals</span></div>
                    <input class="input input-bordered input-sm" type="number" min="0" bind:value={editCrystals} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Credits</span></div>
                    <input class="input input-bordered input-sm" type="number" min="0" bind:value={editCredits} />
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
                    <div class="label"><span class="label-text">Fuel Δ</span></div>
                    <input class="input input-bordered input-sm" type="number" bind:value={adjFuelDelta} placeholder="-20 or +10" />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Crystal Δ</span></div>
                    <input class="input input-bordered input-sm" type="number" bind:value={adjCrystalDelta} />
                </label>
                <label class="form-control">
                    <div class="label"><span class="label-text">Credit Δ</span></div>
                    <input class="input input-bordered input-sm" type="number" bind:value={adjCreditDelta} />
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
