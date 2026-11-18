<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { hexToPixel, hexCornerPoints } from '../utils/hexMath';
	import type { HexCoord } from '../utils/hexMath';
	import { getTerrainColor } from '../utils/terrainColors';

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
	export let hasMission: boolean = false;
	export let adminMode: boolean = false;
	export let overlayMode: boolean = false;

	const dispatch = createEventDispatcher();

	$: pixel = hexToPixel(q, r, size);
	$: points = hexCornerPoints(size - 1); // -1 for padding/stroke

	const FACTION_OVERLAY_PALETTE = [
		'rgba(59,130,246,0.32)',
		'rgba(245,158,11,0.32)',
		'rgba(16,185,129,0.28)',
		'rgba(239,68,68,0.28)',
		'rgba(168,85,247,0.28)'
	];

	function getFactionOverlay(faction: string | null): string | null {
		if (!faction) return null;
		let hash = 0;
		for (let i = 0; i < faction.length; i++) {
			hash = (hash * 31 + faction.charCodeAt(i)) >>> 0;
		}
		return FACTION_OVERLAY_PALETTE[hash % FACTION_OVERLAY_PALETTE.length];
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
		dispatch('click', {
			q,
			r,
			terrain,
			isDiscovered,
			label,
			hexState,
			controllingFaction,
			playerNotesCount
		});
	}

	$: factionOverlay = getFactionOverlay(controllingFaction);
	$: stateIcon = getStateIcon(hexState);
	$: cellFill = overlayMode
		? isDiscovered
			? 'rgba(0, 0, 0, 0.01)'
			: adminMode
				? 'rgba(20, 20, 22, 0.42)'
				: 'rgba(20, 20, 22, 0.62)'
		: !isDiscovered && !adminMode
			? '#151412'
			: getTerrainColor(terrain);
	$: cellStroke = isSelected
		? '#fff'
		: overlayMode
			? isDiscovered
				? 'rgba(255, 255, 255, 0.28)'
				: 'rgba(255, 255, 255, 0.12)'
			: '#444';
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
		fill={cellFill}
		opacity={!overlayMode && adminMode && !isDiscovered ? 0.45 : 1}
		stroke={cellStroke}
		stroke-width={isSelected ? 3 : 1}
		class={isSelected ? 'selected-glow' : ''}
	/>

	{#if !overlayMode && (isDiscovered || adminMode)}
		<g pointer-events="none" opacity={adminMode && !isDiscovered ? 0.35 : 0.45}>
			{#if terrain.toLowerCase() === 'mountain'}
				<path
					d="M -18 10 L -6 -12 L 4 4 L 10 -6 L 20 10 Z"
					fill="none"
					stroke="rgba(255,255,255,0.55)"
					stroke-width="1.4"
					stroke-linejoin="round"
				/>
			{:else if terrain.toLowerCase() === 'forest'}
				<path
					d="M -12 8 L -7 -6 L -2 8 Z M -1 10 L 5 -9 L 11 10 Z"
					fill="rgba(255,255,255,0.22)"
					stroke="rgba(255,255,255,0.45)"
					stroke-width="1"
					stroke-linejoin="round"
				/>
			{:else if terrain.toLowerCase() === 'water'}
				<path
					d="M -16 -3 Q -8 -7 0 -3 T 16 -3 M -14 6 Q -7 2 0 6 T 14 6"
					fill="none"
					stroke="rgba(255,255,255,0.45)"
					stroke-width="1.2"
					stroke-linecap="round"
				/>
			{:else if terrain.toLowerCase() === 'swamp'}
				<path
					d="M -10 8 L -10 -4 M -6 8 L -4 -2 M 4 8 L 4 -5 M 8 8 L 10 -2 M -14 9 L 14 9"
					fill="none"
					stroke="rgba(255,255,255,0.4)"
					stroke-width="1.1"
					stroke-linecap="round"
				/>
			{:else if terrain.toLowerCase() === 'desert'}
				<path
					d="M -18 5 Q -6 -6 6 5 T 20 3"
					fill="none"
					stroke="rgba(255,255,255,0.4)"
					stroke-width="1.2"
					stroke-linecap="round"
				/>
			{/if}
		</g>
	{/if}

	{#if isDiscovered && factionOverlay}
		<polygon {points} fill={factionOverlay} stroke="none" pointer-events="none" />
	{/if}

	{#if isDiscovered && hexState === 'awakened'}
		<polygon
			points={hexCornerPoints(size - 5)}
			fill="none"
			stroke="rgba(168, 85, 247, 0.75)"
			stroke-width="1.5"
			stroke-dasharray="4 3"
			pointer-events="none"
		/>
	{/if}

	{#if label && (isDiscovered || showCoords)}
		{@const pillW = Math.min(size * 1.7, Math.max(40, label.length * 5.8 + 12))}
		{@const pillY = showCoords ? -10 : 0}
		<g pointer-events="none">
			<rect
				x={-pillW / 2}
				y={pillY - 8}
				width={pillW}
				height="16"
				rx="4"
				fill="rgba(16, 14, 12, 0.78)"
				stroke={q === 0 && r === 0 ? 'rgba(212, 168, 83, 0.75)' : 'rgba(255, 255, 255, 0.2)'}
				stroke-width="0.9"
			/>
			<text
				x="0"
				y={pillY + 0.5}
				text-anchor="middle"
				alignment-baseline="middle"
				font-size="9.5"
				fill="#f5f0e6"
				font-weight="600"
			>
				{label}
			</text>
		</g>
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

	{#if isDiscovered && hasMission}
		<text
			x={-(size * 0.45)}
			y={size * 0.4}
			text-anchor="middle"
			alignment-baseline="middle"
			font-size="10"
			fill="#fbbf24"
			pointer-events="none"
		>
			★
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

	{#if !overlayMode && !isDiscovered && !showCoords}
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
