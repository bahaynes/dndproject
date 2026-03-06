<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { hexToPixel, hexCornerPoints } from '../utils/hexMath';
	import type { HexCoord } from '../utils/hexMath';

	export let q: number;
	export let r: number;
	export let size: number = 60;
	export let terrain: string = 'plains';
	export let isDiscovered: boolean = true;
	export let isSelected: boolean = false;
	export let showCoords: boolean = false;
	export let label: string = '';
	export let hexState: string = 'wilderness';
	export let controllingFaction: string | null = null;
	export let playerNotesCount: number = 0;
	export let adminMode: boolean = false;

	const dispatch = createEventDispatcher();

	$: pixel = hexToPixel(q, r, size);
	$: points = hexCornerPoints(size - 1); // -1 for padding/stroke

	function getColor(terrain: string): string {
		switch (terrain.toLowerCase()) {
			case 'plains':
				return '#90EE90'; // LightGreen
			case 'forest':
				return '#228B22'; // ForestGreen
			case 'mountain':
				return '#808080'; // Gray
			case 'water':
				return '#4682B4'; // SteelBlue
			case 'desert':
				return '#F4A460'; // SandyBrown
			case 'swamp':
				return '#556B2F'; // DarkOliveGreen
			default:
				return '#D3D3D3'; // LightGray
		}
	}

	function getFactionOverlay(faction: string | null): string | null {
		switch (faction) {
			case 'Kathedral':
				return 'rgba(59,130,246,0.35)';
			case 'Vastarei':
				return 'rgba(245,158,11,0.35)';
			case 'Inheritors':
				return 'rgba(34,197,94,0.25)';
			default:
				return null;
		}
	}

	function getStateIcon(state: string): string {
		switch (state) {
			case 'claimed_developed':
				return '⚑';
			case 'friendly':
				return '≡';
			case 'contested':
				return '⚔';
			case 'awakened':
				return '~';
			default:
				return '';
		}
	}

	function handleClick() {
		dispatch('click', { q, r, terrain, isDiscovered, label, hexState, controllingFaction, playerNotesCount });
	}

	$: factionOverlay = getFactionOverlay(controllingFaction);
	$: stateIcon = getStateIcon(hexState);
</script>

<g
	transform="translate({pixel.x}, {pixel.y})"
	on:click={handleClick}
	class="hex-cell cursor-pointer transition-opacity duration-200 hover:opacity-80"
	role="button"
	tabindex="0"
	on:keydown={(e) => e.key === 'Enter' && handleClick()}
>
	<polygon
		{points}
		fill={isDiscovered || adminMode ? getColor(terrain) : '#1a1a1a'}
		opacity={adminMode && !isDiscovered ? 0.45 : 1}
		stroke={isSelected ? '#fff' : '#444'}
		stroke-width={isSelected ? 3 : 1}
		class={isSelected ? 'selected-glow' : ''}
	/>

	{#if isDiscovered && factionOverlay}
		<polygon {points} fill={factionOverlay} stroke="none" pointer-events="none" />
	{/if}

	{#if label && (isDiscovered || showCoords)}
		<text
			x="0"
			y={showCoords ? -10 : 0}
			text-anchor="middle"
			alignment-baseline="middle"
			font-size="10"
			fill="white"
			pointer-events="none"
			font-weight="bold"
			class="drop-shadow-md"
		>
			{label}
		</text>
	{/if}

	{#if isDiscovered && stateIcon}
		<text
			x={size * 0.45}
			y={-(size * 0.45)}
			text-anchor="middle"
			alignment-baseline="middle"
			font-size="10"
			fill="rgba(255,255,255,0.85)"
			pointer-events="none"
		>
			{stateIcon}
		</text>
	{/if}

	{#if isDiscovered && playerNotesCount > 0}
		<text
			x={-(size * 0.45)}
			y={-(size * 0.45)}
			text-anchor="middle"
			alignment-baseline="middle"
			font-size="9"
			fill="rgba(255,200,100,0.9)"
			pointer-events="none"
		>
			✎
		</text>
	{/if}

	{#if showCoords}
		<text
			x="0"
			y="10"
			text-anchor="middle"
			alignment-baseline="middle"
			font-size="8"
			fill="rgba(255,255,255,0.5)"
			pointer-events="none"
		>
			{q},{r}
		</text>
	{/if}

	{#if !isDiscovered && !showCoords}
		<!-- Fog effect detail -->
		<text
			x="0"
			y="0"
			text-anchor="middle"
			alignment-baseline="middle"
			font-size="14"
			fill="#333"
			pointer-events="none"
		>
			?
		</text>
	{/if}
</g>

<style>
	.hex-cell:focus {
		outline: none;
	}
	.hex-cell:focus polygon {
		stroke: white;
		stroke-width: 2;
	}
	.selected-glow {
		filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.5));
	}
</style>
