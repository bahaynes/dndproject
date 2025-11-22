<script lang="ts">
    import { onMount } from 'svelte';
    import HexMap from '$lib/components/map/HexMap.svelte';
    import type { MapTile } from '$lib/types';
    import { auth } from '$lib/auth';
    import { page } from '$app/stores';
    import { get } from 'svelte/store';

    let tiles: MapTile[] = [];
    let loading = true;
    let error: string | null = null;
    let selectedTile: MapTile | null = null;
    let isDm = false;

    // DM editing
    let editTile: Partial<MapTile> = {};

    $: isDm = ($auth.user as any)?.role === 'admin';

    onMount(async () => {
        await fetchTiles();
    });

    async function fetchTiles() {
        loading = true;
        try {
            const token = localStorage.getItem('accessToken');
            const headers: HeadersInit = {};
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const res = await fetch('/api/map/tiles', { headers });
            if (!res.ok) throw new Error('Failed to fetch map tiles');
            tiles = await res.json();

            const tileIdParam = get(page).url.searchParams.get('tile');
            if (tileIdParam) {
                const tid = parseInt(tileIdParam);
                const tile = tiles.find(t => t.id === tid);
                if (tile) {
                    selectedTile = tile;
                }
            }
        } catch (e) {
            error = (e as Error).message;
        } finally {
            loading = false;
        }
    }

    function handleTileClick(tile: MapTile) {
        selectedTile = tile;
        editTile = {}; // Reset edit mode on selection change
    }

    async function saveTile() {
        if (!selectedTile) return;
        try {
             const token = localStorage.getItem('accessToken');
             if (!token) throw new Error("Not authenticated");

             const res = await fetch(`/api/map/tiles/${selectedTile.id}`, {
                 method: 'PUT',
                 headers: {
                     'Content-Type': 'application/json',
                     'Authorization': `Bearer ${token}`
                 },
                 body: JSON.stringify({
                     terrain: editTile.terrain,
                     is_revealed: editTile.is_revealed,
                     description: editTile.description,
                     notes: editTile.notes
                 })
             });

             if (!res.ok) throw new Error("Failed to update tile");

             // Refresh
             await fetchTiles();
             // Keep selection but close edit? Or keep edit open?
             // Clos edit
             editTile = {};
        } catch (e) {
            alert((e as Error).message);
        }
    }
</script>

<div class="min-h-screen bg-[#0f0f0f] text-[#d4d4d4] p-4">
    {#if loading}
        <p class="text-center mt-10">Loading map...</p>
    {:else if error}
        <p class="text-red-500 text-center mt-10">Error: {error}</p>
    {:else}
    <div class="flex flex-col lg:flex-row gap-6 h-[calc(100vh-6rem)]">

        <!-- Legend (Left) -->
        <div class="w-full lg:w-64 flex-shrink-0 bg-[#1a1a1a] border border-[#333] rounded-lg p-4 h-fit shadow-lg">
            <h2 class="text-[#a88932] font-bold mb-4 text-lg border-b border-[#333] pb-2">Legend</h2>
            <ul class="space-y-3 text-sm">
                <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#a88932] ring-1 ring-black"></span> City</li>
                <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#2d5a27] ring-1 ring-black"></span> Forest</li>
                <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#555555] ring-1 ring-black"></span> Mountain</li>
                <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#8b0000] ring-1 ring-black"></span> Ruin</li>
                 <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#8f9c3c] ring-1 ring-black"></span> Plains</li>
                 <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#1e3f66] ring-1 ring-black"></span> Water</li>
                 <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#424632] ring-1 ring-black"></span> Swamp</li>
                 <li class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#d2b48c] ring-1 ring-black"></span> Desert</li>
                 <li class="flex items-center gap-2"><span class="w-3 h-3 border border-[#444] bg-[#111]"></span> Unexplored</li>
                 <li class="flex items-center gap-2"><span class="w-3 h-3 border-2 border-[#FFD700] bg-transparent"></span> Active Mission</li>
            </ul>
        </div>

        <!-- Map (Center) -->
        <div class="flex-1 overflow-hidden flex flex-col items-center justify-center bg-[#0a0a0a] rounded-lg border border-[#222] p-2">
             <HexMap {tiles} onTileClick={handleTileClick} selectedTileId={selectedTile?.id || null} />
        </div>

        <!-- Details (Right) -->
         <div class="w-full lg:w-80 flex-shrink-0 bg-[#1a1a1a] border border-[#333] rounded-lg p-6 h-fit shadow-lg">
            <div class="flex items-center gap-2 mb-4 text-[#a88932]">
                <!-- Icon -->
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z" />
                </svg>
                <h2 class="text-xl font-serif font-bold">Hex Details</h2>
            </div>

            {#if selectedTile}
                <h3 class="text-lg font-bold text-white mb-1">
                    {selectedTile.is_revealed ? (selectedTile.description && selectedTile.description.length < 30 ? selectedTile.description : `Region ${selectedTile.q}, ${selectedTile.r}`) : "Uncharted Territory"}
                </h3>
                <div class="flex items-center gap-2 mb-4">
                    <span class="bg-[#2a2a2a] px-2 py-0.5 rounded text-xs text-gray-400 font-mono">{selectedTile.q}, {selectedTile.r}</span>
                    {#if !selectedTile.is_revealed}
                        <span class="bg-[#3a2a2a] px-2 py-0.5 rounded text-xs text-orange-300 flex items-center gap-1">
                            Fog of War
                        </span>
                    {/if}
                </div>

                {#if selectedTile.is_revealed}
                     <div class="p-3 bg-[#111] border border-[#333] rounded mb-4 italic text-gray-400 text-sm">
                        {selectedTile.description || "No description available."}
                     </div>

                     <div class="mb-4">
                        <h4 class="text-sm font-bold text-[#a88932] uppercase tracking-wider mb-1">Terrain</h4>
                        <p class="capitalize flex items-center gap-2">
                            <span class="inline-block w-3 h-3 rounded-full" style="background-color: {
                                selectedTile.terrain === 'forest' ? '#2d5a27' :
                                selectedTile.terrain === 'plains' ? '#8f9c3c' :
                                selectedTile.terrain === 'mountain' ? '#555555' :
                                selectedTile.terrain === 'water' ? '#1e3f66' :
                                selectedTile.terrain === 'city' ? '#a88932' :
                                selectedTile.terrain === 'ruin' ? '#8b0000' :
                                selectedTile.terrain === 'desert' ? '#d2b48c' :
                                '#333'
                            }"></span>
                            {selectedTile.terrain}
                        </p>
                     </div>
                {:else}
                     <div class="p-3 bg-[#111] border border-[#333] rounded mb-4 italic text-orange-200/70 text-sm border-l-2 border-l-orange-900">
                        The details of this region are unknown to the guild.
                     </div>
                {/if}

                {#if isDm}
                    <button on:click={() => { if (selectedTile) editTile = { ...selectedTile }; }} class="w-full mt-4 py-2 bg-[#a88932] hover:bg-[#8c722a] text-[#1a1a1a] font-bold rounded flex items-center justify-center gap-2 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                          <path d="m5.433 13.917 1.262-3.155A4 4 0 0 1 7.58 9.42l6.92-6.918a2.121 2.121 0 0 1 3 3l-6.92 6.918c-.383.383-.84.685-1.343.886l-3.154 1.262a.5.5 0 0 1-.65-.65Z" />
                          <path d="M3.5 5.75c0-.69.56-1.25 1.25-1.25H10A.75.75 0 0 0 10 3H4.75A2.75 2.75 0 0 0 2 5.75v9.5A2.75 2.75 0 0 0 4.75 18h9.5A2.75 2.75 0 0 0 17 15.25V10a.75.75 0 0 0-1.5 0v5.25c0 .69-.56 1.25-1.25 1.25h-9.5c-.69 0-1.25-.56-1.25-1.25v-9.5Z" />
                        </svg>
                        Edit Hex Data
                    </button>

                    {#if editTile.id === selectedTile.id}
                         <div class="mt-4 p-4 bg-[#222] rounded border border-[#444]">
                             <div class="space-y-3">
                                <div>
                                    <label class="block text-xs font-bold text-gray-500">Terrain</label>
                                    <select bind:value={editTile.terrain} class="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-white">
                                        <option value="plains">Plains</option>
                                        <option value="forest">Forest</option>
                                        <option value="mountain">Mountain</option>
                                        <option value="water">Water</option>
                                        <option value="swamp">Swamp</option>
                                        <option value="desert">Desert</option>
                                        <option value="city">City</option>
                                        <option value="ruin">Ruin</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="flex items-center gap-2 text-sm">
                                        <input type="checkbox" bind:checked={editTile.is_revealed} class="rounded bg-[#111] border-[#333] text-[#a88932]" />
                                        Revealed
                                    </label>
                                </div>
                                <div>
                                     <label class="block text-xs font-bold text-gray-500">Description</label>
                                     <textarea bind:value={editTile.description} class="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-white text-sm" rows="3"></textarea>
                                </div>
                                <div>
                                     <label class="block text-xs font-bold text-gray-500">Notes (DM)</label>
                                     <textarea bind:value={editTile.notes} class="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-white text-sm" rows="2"></textarea>
                                </div>
                                <div class="flex gap-2">
                                    <button on:click={saveTile} class="flex-1 bg-[#2d5a27] text-white py-1 rounded hover:bg-green-800">Save</button>
                                    <button on:click={() => editTile = {}} class="flex-1 bg-[#444] text-white py-1 rounded hover:bg-[#555]">Cancel</button>
                                </div>
                             </div>
                         </div>
                    {/if}
                {/if}
            {:else}
                <div class="text-center text-gray-500 italic mt-10">
                    Select a hex to view details.
                </div>
            {/if}
         </div>
    </div>
    {/if}
</div>
