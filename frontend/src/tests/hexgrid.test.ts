import { render } from '@testing-library/svelte';
import { describe, expect, test } from 'vitest';
import HexGrid from '$lib/components/HexGrid.svelte';

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

		// Discovered hex is transparent in overlay mode; undiscovered hex is opaque fog
		const polygons = container.querySelectorAll('g.hex-cell polygon');
		expect(polygons[0].getAttribute('fill')).toBe('rgba(0, 0, 0, 0.01)');
		expect(polygons[1].getAttribute('fill')).toBe('#151412');

		// Danger tier rings T1, T2, T3 rendered
		expect(container.textContent).toContain('T1');
		expect(container.textContent).toContain('T2');
		expect(container.textContent).toContain('T3');
	});
});
