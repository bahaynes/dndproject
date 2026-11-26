<script lang="ts">
	import { onMount } from 'svelte';
	import HexCell from './HexCell.svelte';
	import { computeMapViewBox, type HexCoord } from '../utils/hexMath';
	import { routeToSvgPath, type MapRoute, type RouteCoord } from '../utils/mapLayers';

	interface HexData {
		q: number;
		r: number;
		terrain: string;
		is_discovered: boolean;
		linked_location_name?: string;
		linked_mission_id?: number;
		hex_state?: string;
		controlling_faction?: string | null;
		player_notes?: any[];
	}

	export let hexes: HexData[] = [];
	export let hexSize: number = 60;
	export let selectedHex: HexCoord | null = null;
	export let showCoords: boolean = false;
	export let showLegend: boolean = true;
	export let adminMode: boolean = false;
	export let baseLayerUrl: string | null = null;
	export let layerBounds: { min_x: number; min_y: number; max_x: number; max_y: number } | null = null;
	export let showDangerTiers: boolean = false;
	export let routes: MapRoute[] = [];
	export let activeDraftRoute: MapRoute | null = null;

	$: discoveredKeys = new Set(hexes.filter((h) => h.is_discovered).map((h) => `${h.q},${h.r}`));

	function visibleRouteSegments(route: MapRoute): RouteCoord[][] {
		if (adminMode) return route.hexes.length >= 2 ? [route.hexes] : [];
		const segments: RouteCoord[][] = [];
		let current: RouteCoord[] = [];
		for (let i = 0; i < route.hexes.length - 1; i++) {
			const a = route.hexes[i];
			const b = route.hexes[i + 1];
			const visible = discoveredKeys.has(`${a.q},${a.r}`) || discoveredKeys.has(`${b.q},${b.r}`);
			if (visible) {
				if (current.length === 0) current.push(a);
				current.push(b);
			} else if (current.length > 0) {
				if (current.length >= 2) segments.push(current);
				current = [];
			}
		}
		if (current.length >= 2) segments.push(current);
		return segments;
	}

	const ROUTE_STYLES: Record<string, { stroke: string; width: number; dash?: string; casing?: string }> = {
		road: { stroke: '#e2c07d', width: 3.2, casing: 'rgba(20, 16, 12, 0.8)' },
		trail: { stroke: '#c8a97e', width: 2, dash: '5 5' },
		sea_lane: { stroke: '#38bdf8', width: 2.5, dash: '8 6' },
		river: { stroke: '#60a5fa', width: 3.5, casing: 'rgba(15, 35, 65, 0.7)' }
	};

	$: overlayMode = Boolean(baseLayerUrl && layerBounds);
	$: dangerRings = [
		{ tier: 'T1', radius: hexSize * Math.sqrt(3) * 2.2, color: 'rgba(16, 185, 129, 0.5)' },
		{ tier: 'T2', radius: hexSize * Math.sqrt(3) * 4.2, color: 'rgba(245, 158, 11, 0.5)' },
		{ tier: 'T3', radius: hexSize * Math.sqrt(3) * 6.2, color: 'rgba(239, 68, 68, 0.5)' }
	];

	const FACTION_OVERLAY_PALETTE = [
		'rgba(59,130,246,0.5)',
		'rgba(245,158,11,0.5)',
		'rgba(16,185,129,0.45)',
		'rgba(239,68,68,0.45)',
		'rgba(168,85,247,0.45)'
	];

	function getFactionLegendColor(faction: string): string {
		let hash = 0;
		for (let i = 0; i < faction.length; i++) {
			hash = (hash * 31 + faction.charCodeAt(i)) >>> 0;
		}
		return FACTION_OVERLAY_PALETTE[hash % FACTION_OVERLAY_PALETTE.length];
	}

	$: legendFactions = Array.from(
		new Set(hexes.map((h) => h.controlling_faction).filter((f): f is string => Boolean(f)))
	).sort();

	const DRAG_THRESHOLD_PX = 5;

	let viewBox = { x: -500, y: -300, w: 1000, h: 600 };
	let isDragging = false;
	let hasDragged = false;
	let suppressNextClick = false;
	let downPos = { x: 0, y: 0 };
	let startPan = { x: 0, y: 0 };
	let lastPinchDist: number | null = null;
	let svgElement: SVGSVGElement;
	let lastAutoFitKey = '';

	function getContainerAspectRatio(): number {
		if (svgElement && svgElement.clientWidth > 0 && svgElement.clientHeight > 0) {
			return svgElement.clientWidth / svgElement.clientHeight;
		}
		return 16 / 9;
	}

	function getFitViewBox() {
		return computeMapViewBox(hexes, hexSize, layerBounds, getContainerAspectRatio());
	}

	export function resetView() {
		viewBox = getFitViewBox();
	}

	onMount(() => {
		resetView();
	});

	$: autoFitKey = `${hexes.length}:${hexSize}:${layerBounds ? `${layerBounds.min_x},${layerBounds.min_y},${layerBounds.max_x},${layerBounds.max_y}` : ''}`;
	$: if (autoFitKey !== lastAutoFitKey && (hexes.length > 0 || layerBounds)) {
		lastAutoFitKey = autoFitKey;
		viewBox = getFitViewBox();
	}

	function zoomAtClientPoint(scaleFactor: number, clientX: number, clientY: number) {
		if (!svgElement) return;
		const rect = svgElement.getBoundingClientRect();
		if (rect.width <= 0 || rect.height <= 0) return;

		const fit = getFitViewBox();
		const minW = Math.max(hexSize * 3.5, 180);
		const maxW = Math.max(8000, fit.w * 4);

		const targetW = Math.min(maxW, Math.max(minW, viewBox.w * scaleFactor));
		const actualScale = targetW / viewBox.w;
		const targetH = viewBox.h * actualScale;

		const relX = (clientX - rect.left) / rect.width;
		const relY = (clientY - rect.top) / rect.height;
		const vx = viewBox.x + relX * viewBox.w;
		const vy = viewBox.y + relY * viewBox.h;

		viewBox = {
			x: vx - relX * targetW,
			y: vy - relY * targetH,
			w: targetW,
			h: targetH
		};
	}

	function zoomByCenter(scaleFactor: number) {
		if (!svgElement) return;
		const rect = svgElement.getBoundingClientRect();
		zoomAtClientPoint(scaleFactor, rect.left + rect.width / 2, rect.top + rect.height / 2);
	}

	function handleMouseDown(e: MouseEvent) {
		if (e.button !== 0 && e.button !== 1) return; // Left or Middle click
		isDragging = true;
		hasDragged = false;
		suppressNextClick = false;
		downPos = { x: e.clientX, y: e.clientY };
		startPan = { x: e.clientX, y: e.clientY };
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isDragging || !svgElement) return;
		if (!hasDragged) {
			const moved = Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y);
			if (moved <= DRAG_THRESHOLD_PX) return;
			hasDragged = true;
			suppressNextClick = true;
		}
		const rect = svgElement.getBoundingClientRect();
		if (rect.width <= 0 || rect.height <= 0) return;
		const dx = (e.clientX - startPan.x) * (viewBox.w / rect.width);
		const dy = (e.clientY - startPan.y) * (viewBox.h / rect.height);

		viewBox = {
			...viewBox,
			x: viewBox.x - dx,
			y: viewBox.y - dy
		};

		startPan = { x: e.clientX, y: e.clientY };
	}

	function handleMouseUp() {
		if (hasDragged) {
			suppressNextClick = true;
			setTimeout(() => {
				suppressNextClick = false;
			}, 0);
		}
		isDragging = false;
		hasDragged = false;
	}

	function handleSvgClickCapture(e: MouseEvent) {
		if (suppressNextClick) {
			e.stopPropagation();
			e.preventDefault();
			suppressNextClick = false;
		}
	}

	function getTouchDist(t1: Touch, t2: Touch): number {
		return Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY);
	}

	function handleTouchStart(e: TouchEvent) {
		if (e.touches.length === 1) {
			isDragging = true;
			hasDragged = false;
			lastPinchDist = null;
			downPos = { x: e.touches[0].clientX, y: e.touches[0].clientY };
			startPan = { x: e.touches[0].clientX, y: e.touches[0].clientY };
		} else if (e.touches.length === 2) {
			isDragging = false;
			lastPinchDist = getTouchDist(e.touches[0], e.touches[1]);
		}
	}

	function handleTouchMove(e: TouchEvent) {
		if (!svgElement) return;
		const rect = svgElement.getBoundingClientRect();
		if (rect.width <= 0 || rect.height <= 0) return;

		if (e.touches.length === 1 && isDragging) {
			e.preventDefault();
			if (!hasDragged) {
				const moved = Math.hypot(
					e.touches[0].clientX - downPos.x,
					e.touches[0].clientY - downPos.y
				);
				if (moved <= DRAG_THRESHOLD_PX) return;
				hasDragged = true;
			}
			const dx = (e.touches[0].clientX - startPan.x) * (viewBox.w / rect.width);
			const dy = (e.touches[0].clientY - startPan.y) * (viewBox.h / rect.height);
			viewBox = {
				...viewBox,
				x: viewBox.x - dx,
				y: viewBox.y - dy
			};
			startPan = { x: e.touches[0].clientX, y: e.touches[0].clientY };
		} else if (e.touches.length === 2 && lastPinchDist !== null) {
			e.preventDefault();
			const dist = getTouchDist(e.touches[0], e.touches[1]);
			if (dist > 0) {
				const scaleFactor = lastPinchDist / dist;
				const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
				const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
				zoomAtClientPoint(scaleFactor, cx, cy);
				lastPinchDist = dist;
			}
		}
	}

	function handleTouchEnd() {
		isDragging = false;
		hasDragged = false;
		lastPinchDist = null;
	}

	function handleWheel(e: WheelEvent) {
		e.preventDefault();
		const scaleFactor = e.deltaY > 0 ? 1.12 : 0.89;
		zoomAtClientPoint(scaleFactor, e.clientX, e.clientY);
	}
</script>

<div
	class="border-base-300 bg-base-100 relative h-full w-full overflow-hidden rounded-xl border shadow-inner"
>
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
	<svg
		bind:this={svgElement}
		class="h-full w-full cursor-move touch-none bg-base-300"
		viewBox="{viewBox.x} {viewBox.y} {viewBox.w} {viewBox.h}"
		role="application"
		on:click|capture={handleSvgClickCapture}
		on:mousedown={handleMouseDown}
		on:mousemove={handleMouseMove}
		on:mouseup={handleMouseUp}
		on:mouseleave={handleMouseUp}
		on:touchstart={handleTouchStart}
		on:touchmove={handleTouchMove}
		on:touchend={handleTouchEnd}
		on:touchcancel={handleTouchEnd}
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

		<!-- Real-Earth / AI Base Map Layer -->
		{#if baseLayerUrl && layerBounds}
			<image
				href={baseLayerUrl}
				x={layerBounds.min_x}
				y={layerBounds.min_y}
				width={layerBounds.max_x - layerBounds.min_x}
				height={layerBounds.max_y - layerBounds.min_y}
				preserveAspectRatio="none"
				pointer-events="none"
			/>
		{/if}

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
					hexState={hex.hex_state || 'wilderness'}
					controllingFaction={hex.controlling_faction || null}
					playerNotesCount={hex.player_notes?.length || 0}
					hasMission={Boolean(hex.linked_mission_id)}
					{showCoords}
					{adminMode}
					{overlayMode}
					on:click
				/>
			{/each}
		</g>

		<!-- Roads / Trails / Rivers / Sea Lanes -->
		{#if routes.length > 0 || (activeDraftRoute && activeDraftRoute.hexes.length >= 2)}
			<g pointer-events="none" class="map-routes">
				{#each routes as route (route.id)}
					{@const style = ROUTE_STYLES[route.type] || ROUTE_STYLES.road}
					{#each visibleRouteSegments(route) as seg}
						{@const d = routeToSvgPath(seg, hexSize)}
						{#if d}
							{#if style.casing}
								<path
									{d}
									fill="none"
									stroke={style.casing}
									stroke-width={style.width + 3}
									stroke-linecap="round"
									stroke-linejoin="round"
								/>
							{/if}
							<path
								{d}
								fill="none"
								stroke={style.stroke}
								stroke-width={style.width}
								stroke-dasharray={style.dash || undefined}
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						{/if}
					{/each}
				{/each}
				{#if activeDraftRoute && activeDraftRoute.hexes.length >= 2}
					{@const draftD = routeToSvgPath(activeDraftRoute.hexes, hexSize)}
					{#if draftD}
						<path
							d={draftD}
							fill="none"
							stroke="#facc15"
							stroke-width="3.5"
							stroke-dasharray="6 4"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					{/if}
				{/if}
			</g>
		{/if}

		{#if showDangerTiers}
			<g pointer-events="none">
				{#each dangerRings as ring}
					<circle
						cx="0"
						cy="0"
						r={ring.radius}
						fill="none"
						stroke={ring.color}
						stroke-width="2"
						stroke-dasharray="8 6"
					/>
					<text
						x="0"
						y={-ring.radius - 6}
						text-anchor="middle"
						font-size="11"
						font-weight="bold"
						fill={ring.color}
					>
						{ring.tier}
					</text>
				{/each}
			</g>
		{/if}
	</svg>

	<div class="absolute bottom-4 right-4 flex items-center gap-1.5">
		<div class="bg-base-300/80 pointer-events-none hidden rounded px-2 py-1 text-xs opacity-60 sm:block">
			Scroll to Zoom • Drag to Pan
		</div>
		<div class="join border-base-content/10 bg-base-100/90 border shadow backdrop-blur">
			<button
				type="button"
				class="btn btn-xs btn-ghost join-item"
				title="Zoom In"
				aria-label="Zoom in"
				on:click={() => zoomByCenter(0.8)}
			>
				+
			</button>
			<button
				type="button"
				class="btn btn-xs btn-ghost join-item"
				title="Zoom Out"
				aria-label="Zoom out"
				on:click={() => zoomByCenter(1.25)}
			>
				−
			</button>
			<button
				type="button"
				class="btn btn-xs btn-ghost join-item"
				title="Reset / Fit Map"
				aria-label="Fit map to view"
				on:click={resetView}
			>
				Fit
			</button>
		</div>
	</div>

	{#if showLegend}
		<div
			class="bg-base-100/90 border-base-content/10 pointer-events-none absolute bottom-4 left-4 rounded-lg border p-3 text-xs shadow backdrop-blur"
		>
			<div class="mb-2 font-bold uppercase opacity-50 tracking-widest">Legend</div>
			<div class="flex flex-col gap-1">
				{#each legendFactions as faction}
					<div class="flex items-center gap-2">
						<span
							class="inline-block h-3 w-3 rounded-sm"
							style="background:{getFactionLegendColor(faction)}"
						></span>
						<span>{faction}</span>
					</div>
				{/each}
				<div class="{legendFactions.length ? 'mt-1 border-t border-base-content/10 pt-1 ' : ''}flex flex-col gap-1 opacity-70">
					<span>⚑ Claimed &amp; Developed (0.5h)</span>
					<span>≡ Friendly Controlled (1h)</span>
					<span>⚔ Contested (3h)</span>
					<span>~ Awakened (variable)</span>
					<span>✎ Has player notes</span>
				</div>
			</div>
		</div>
	{/if}
</div>
