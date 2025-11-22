<script lang="ts">
    import type { MapTile } from '$lib/types';

    export let tiles: MapTile[] = [];
    export let onTileClick: (tile: MapTile) => void = () => {};
    export let selectedTileId: number | null = null;

    const hexSize = 30;

    function hexToPixel(q: number, r: number) {
        const x = hexSize * (Math.sqrt(3) * q + (Math.sqrt(3) / 2) * r);
        const y = hexSize * ((3 / 2) * r);
        return { x, y };
    }

    function getTerrainColor(terrain: string) {
        switch (terrain.toLowerCase()) {
            case 'forest': return '#2d5a27';
            case 'plains': return '#8f9c3c';
            case 'mountain': return '#555555';
            case 'water': return '#1e3f66';
            case 'desert': return '#d2b48c';
            case 'swamp': return '#424632';
            case 'city': return '#a88932';
            case 'ruin': return '#8b0000';
            default: return '#333333';
        }
    }

    function getTerrainIcon(terrain: string) {
        switch (terrain.toLowerCase()) {
            case 'forest': return '🌲';
            case 'mountain': return '⛰️';
            case 'water': return '≈';
            case 'city': return '🏰';
            case 'ruin': return '💀';
            case 'swamp': return '🐊';
            case 'desert': return '🌵';
            default: return '';
        }
    }

    // Calculate bounds
    $: points = tiles.map(t => hexToPixel(t.q, t.r));
    $: minX = points.length ? Math.min(...points.map(p => p.x)) : 0;
    $: maxX = points.length ? Math.max(...points.map(p => p.x)) : 0;
    $: minY = points.length ? Math.min(...points.map(p => p.y)) : 0;
    $: maxY = points.length ? Math.max(...points.map(p => p.y)) : 0;

    $: width = (maxX - minX) + hexSize * 3;
    $: height = (maxY - minY) + hexSize * 3;
    $: viewBox = `${minX - hexSize * 1.5} ${minY - hexSize * 1.5} ${width} ${height}`;

    function handleKeydown(e: KeyboardEvent, tile: MapTile) {
        if (e.key === 'Enter' || e.key === ' ') {
            onTileClick(tile);
            e.preventDefault();
        }
    }
</script>

<div class="overflow-auto bg-[#1a1a1a] p-8 rounded-lg shadow-inner flex justify-center border border-[#333]">
    {#if tiles.length === 0}
        <div class="p-4 text-gray-500">No map tiles available.</div>
    {:else}
        <svg {viewBox} class="w-full h-auto" style="max-height: 80vh;">
            <g>
                {#each tiles as tile (tile.id)}
                    {@const { x, y } = hexToPixel(tile.q, tile.r)}
                    <g transform="translate({x}, {y})">
                        <polygon
                            points="0,-{hexSize} {hexSize * Math.sqrt(3)/2},-{hexSize/2} {hexSize * Math.sqrt(3)/2},{hexSize/2} 0,{hexSize} -{hexSize * Math.sqrt(3)/2},{hexSize/2} -{hexSize * Math.sqrt(3)/2},-{hexSize/2}"
                            fill={tile.is_revealed ? getTerrainColor(tile.terrain) : '#111'}
                            stroke={selectedTileId === tile.id ? '#FFD700' : '#444'}
                            stroke-width={selectedTileId === tile.id ? 3 : 1}
                            class="cursor-pointer hover:opacity-90 transition-opacity"
                            on:click={() => onTileClick(tile)}
                            role="button"
                            tabindex="0"
                            on:keydown={(e) => handleKeydown(e, tile)}
                        />

                        {#if tile.is_revealed}
                            <text x="0" y="0" text-anchor="middle" dy=".3em" font-size="14" fill="rgba(255,255,255,0.7)" pointer-events="none">
                                {getTerrainIcon(tile.terrain)}
                            </text>
                            <text x="0" y="-{hexSize/1.5}" text-anchor="middle" font-size="8" fill="rgba(255,255,255,0.3)" pointer-events="none">
                                {tile.q},{tile.r}
                            </text>
                        {:else}
                             <text x="0" y="0" text-anchor="middle" dy=".3em" font-size="10" fill="rgba(255,255,255,0.1)" pointer-events="none">
                                {tile.q},{tile.r}
                            </text>
                        {/if}
                    </g>
                {/each}
            </g>
        </svg>
    {/if}
</div>
