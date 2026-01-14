<script lang="ts">
	import { onMount } from 'svelte';
	import HexCell from './HexCell.svelte';
	import type { HexCoord } from '../utils/hexMath';

	interface HexData {
		q: number;
		r: number;
		terrain: string;
		is_discovered: boolean;
		linked_location_name?: string;
	}

	export let hexes: HexData[] = [];
	export let hexSize: number = 60;
	export let selectedHex: HexCoord | null = null;
	export let showCoords: boolean = false;

	let viewBox = { x: -500, y: -500, w: 2000, h: 1200 };
	let isDragging = false;
	let startPan = { x: 0, y: 0 };
	let svgElement: SVGSVGElement;

	function handleMouseDown(e: MouseEvent) {
		if (e.button !== 0 && e.button !== 1) return; // Left or Middle click
		isDragging = true;
		startPan = { x: e.clientX, y: e.clientY };
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isDragging) return;
		const dx = (e.clientX - startPan.x) * (viewBox.w / svgElement.clientWidth);
		const dy = (e.clientY - startPan.y) * (viewBox.h / svgElement.clientHeight);

		viewBox.x -= dx;
		viewBox.y -= dy;

		startPan = { x: e.clientX, y: e.clientY };
	}

	function handleMouseUp() {
		isDragging = false;
	}

	function handleWheel(e: WheelEvent) {
		e.preventDefault();
		const scaleFactor = e.deltaY > 0 ? 1.1 : 0.9;

		const mouseX = e.offsetX;
		const mouseY = e.offsetY;

		// Calculate mouse position relative to viewBox
		const vx = viewBox.x + (mouseX / svgElement.clientWidth) * viewBox.w;
		const vy = viewBox.y + (mouseY / svgElement.clientHeight) * viewBox.h;

		viewBox.w *= scaleFactor;
		viewBox.h *= scaleFactor;

		// Maintain mouse position
		viewBox.x = vx - (mouseX / svgElement.clientWidth) * viewBox.w;
		viewBox.y = vy - (mouseY / svgElement.clientHeight) * viewBox.h;
	}
</script>

<div
	class="border-base-300 bg-base-100 relative h-full w-full overflow-hidden rounded-xl border shadow-inner"
>
	<svg
		bind:this={svgElement}
		class="h-full w-full cursor-move bg-[#111]"
		viewBox="{viewBox.x} {viewBox.y} {viewBox.w} {viewBox.h}"
		role="application"
		on:mousedown={handleMouseDown}
		on:mousemove={handleMouseMove}
		on:mouseup={handleMouseUp}
		on:mouseleave={handleMouseUp}
		on:wheel={handleWheel}
	>
		<defs>
			<pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
				<path
					d="M 100 0 L 0 0 0 100"
					fill="none"
					stroke="rgba(255,255,255,0.05)"
					stroke-width="1"
				/>
			</pattern>
		</defs>
		<!-- Background grid for flavor -->
		<rect x="-10000" y="-10000" width="20000" height="20000" fill="url(#grid)" />

		<!-- Hex Layers -->
		<g>
			{#each hexes as hex (hex.q + ',' + hex.r)}
				<HexCell
					q={hex.q}
					r={hex.r}
					size={hexSize}
					terrain={hex.terrain}
					isDiscovered={hex.is_discovered}
					label={hex.linked_location_name || ''}
					isSelected={selectedHex?.q === hex.q && selectedHex?.r === hex.r}
					{showCoords}
					on:click
				/>
			{/each}
		</g>
	</svg>

	<div
		class="bg-base-300/80 pointer-events-none absolute bottom-4 right-4 rounded p-2 text-xs opacity-50"
	>
		Scroll to Zoom • Drag to Pan
	</div>
</div>
