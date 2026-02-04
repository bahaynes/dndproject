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

	function handleClick() {
		dispatch('click', { q, r, terrain, isDiscovered, label });
	}
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
		fill={isDiscovered ? getColor(terrain) : '#1a1a1a'}
		stroke={isSelected ? '#fff' : '#333'}
		stroke-width={isSelected ? 3 : 1}
		class={isSelected ? 'selected-glow' : ''}
	/>

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
