import { fireEvent, render } from '@testing-library/svelte';
import { describe, expect, test, vi } from 'vitest';
import HexGrid from '$lib/components/HexGrid.svelte';
import { computeMapViewBox } from '$lib/utils/hexMath';

describe('HexGrid base layers and cartography overlays', () => {
	const sampleHexes = [
		{ q: 0, r: 0, terrain: 'plains', is_discovered: true, linked_location_name: 'Haven', linked_mission_id: 1 },
		{ q: 1, r: 0, terrain: 'mountain', is_discovered: false }
	];

	test('renders base <image> layer and transparent/fog hexes when baseLayerUrl and layerBounds are set', () => {
		const { container } = render(HexGrid, {
			props: {
				hexes: sampleHexes,
				hexSize: 60,
				baseLayerUrl: 'blob:http://localhost/topo-layer',
				layerBounds: { min_x: -100, min_y: -100, max_x: 200, max_y: 200 },
				showDangerTiers: true
			}
		});

		const img = container.querySelector('svg image');
		expect(img).not.toBeNull();
		expect(img?.getAttribute('href')).toBe('blob:http://localhost/topo-layer');
		expect(img?.getAttribute('width')).toBe('300');
		expect(img?.getAttribute('height')).toBe('300');

		// Discovered hex is transparent in overlay mode; undiscovered hex is a Civ VI translucent fog veil
		const polygons = container.querySelectorAll('g.hex-cell polygon');
		expect(polygons[0].getAttribute('fill')).toBe('rgba(0, 0, 0, 0.01)');
		expect(polygons[1].getAttribute('fill')).toBe('rgba(20, 20, 22, 0.62)');

		// Danger tier rings T1, T2, T3 rendered
		expect(container.textContent).toContain('T1');
		expect(container.textContent).toContain('T2');
		expect(container.textContent).toContain('T3');
	});

	test('renders visible routes and hides undiscovered route segments in player mode', () => {
		const { container } = render(HexGrid, {
			props: {
				hexes: [
					{ q: 0, r: 0, terrain: 'plains', is_discovered: true },
					{ q: 1, r: 0, terrain: 'plains', is_discovered: false },
					{ q: 2, r: 0, terrain: 'mountain', is_discovered: false }
				],
				hexSize: 60,
				adminMode: false,
				routes: [
					{
						id: 'r1',
						name: "King's Road",
						type: 'road',
						hexes: [
							{ q: 0, r: 0 },
							{ q: 1, r: 0 },
							{ q: 2, r: 0 }
						]
					}
				]
			}
		});

		// Segment (0,0)->(1,0) is visible (1 endpoint discovered); (1,0)->(2,0) is hidden
		const routePaths = container.querySelectorAll('g.map-routes path');
		expect(routePaths.length).toBe(2); // casing + core for 1 visible segment
	});

	test('computeMapViewBox fits hexes and layerBounds symmetrically', () => {
		const box = computeMapViewBox(
			[{ q: 0, r: 0 }, { q: 2, r: 0 }],
			60,
			{ min_x: -200, min_y: -150, max_x: 300, max_y: 150 },
			16 / 9
		);
		expect(box.w).toBeGreaterThan(500);
		expect(box.h).toBeGreaterThan(300);
		expect(box.x).toBeLessThan(-200);
		expect(box.y).toBeLessThan(-150);

		const emptyBox = computeMapViewBox([], 60, null);
		expect(emptyBox).toEqual({ x: -500, y: -300, w: 1000, h: 600 });
	});

	test('auto-fits viewBox, renders zoom/fit controls, and suppresses click after panning', async () => {
		const { container, getByLabelText } = render(HexGrid, {
			props: {
				hexes: sampleHexes,
				hexSize: 60
			}
		});

		const svg = container.querySelector('svg') as SVGSVGElement;
		expect(svg).not.toBeNull();
		const vb = svg.getAttribute('viewBox') || '';
		// Auto-fit should not stay at the old hardcoded -500 -500 2000 1200
		expect(vb).not.toBe('-500 -500 2000 1200');

		expect(getByLabelText('Zoom in')).toBeTruthy();
		expect(getByLabelText('Zoom out')).toBeTruthy();
		expect(getByLabelText('Fit map to view')).toBeTruthy();

		const clickSpy = vi.fn();
		const firstCell = container.querySelector('g.hex-cell') as SVGGElement;
		expect(firstCell).not.toBeNull();
		firstCell.addEventListener('click', clickSpy);

		// Normal click reaches hex cell
		await fireEvent.mouseDown(svg, { button: 0, clientX: 100, clientY: 100 });
		await fireEvent.mouseUp(svg, { button: 0, clientX: 101, clientY: 101 });
		await fireEvent.click(firstCell);
		expect(clickSpy).toHaveBeenCalledTimes(1);

		// Dragging > 5px suppresses the trailing click in capture phase
		await fireEvent.mouseDown(svg, { button: 0, clientX: 100, clientY: 100 });
		await fireEvent.mouseMove(svg, { clientX: 130, clientY: 120 });
		await fireEvent.mouseUp(svg, { button: 0, clientX: 130, clientY: 120 });
		await fireEvent.click(firstCell);
		expect(clickSpy).toHaveBeenCalledTimes(1);
	});
});
