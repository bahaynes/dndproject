import { get } from 'svelte/store';
import { auth } from '$lib/auth';
import { API_BASE_URL } from '$lib/config';
import { hexToPixel } from './hexMath';

export type MapLayerMode = 'tactical' | 'topo' | 'satellite';
export type RouteType = 'road' | 'trail' | 'sea_lane' | 'river';

export interface RouteCoord {
	q: number;
	r: number;
}

export interface MapRoute {
	id: string;
	name: string;
	type: RouteType;
	hexes: RouteCoord[];
}

export interface LayerBounds {
	min_x: number;
	min_y: number;
	max_x: number;
	max_y: number;
}

export type TravelScale = 'local' | 'frontier' | 'expedition';

export const TRAVEL_SCALES: { value: TravelScale; label: string }[] = [
	{ value: 'frontier', label: 'Frontier — 2h / 6 mi hex (Standard)' },
	{ value: 'local', label: 'Local — 1h / 3 mi hex (Tight)' },
	{ value: 'expedition', label: 'Expedition — 1d / 24 mi hex (Sea/Ship)' }
];

export const EARTH_REGION_PRESETS = [
	{ label: 'Iceland — Volcanic Frontier', center_lat: 64.2, center_lon: -19.5 },
	{ label: 'Scottish Highlands — Lochs & Glens', center_lat: 57.0, center_lon: -4.9 },
	{ label: 'Pacific Northwest — Puget Archipelago', center_lat: 47.85, center_lon: -122.6 },
	{ label: 'Dalmatian Coast — Island Chain', center_lat: 43.25, center_lon: 16.6 }
];

/**
 * Parses a pasted Google Maps pin ("64.1466, -21.9426" or URL with "@64.1466,-21.9426").
 */
export function parseLatLonInput(raw: string): { lat: number; lon: number } | null {
	const atMatch = raw.match(/@(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)/);
	const pairMatch = atMatch || raw.match(/(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)/);
	if (!pairMatch) return null;
	const lat = Number(pairMatch[1]);
	const lon = Number(pairMatch[2]);
	if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -84 || lat > 84 || lon < -180 || lon > 180) {
		return null;
	}
	return { lat, lon };
}

/**
 * Fetches an authenticated map layer PNG and returns an Object URL suitable for SVG <image>.
 */
export async function fetchAuthedLayerUrl(apiPath: string): Promise<string> {
	const token = get(auth).token;
	const fullUrl = apiPath.startsWith('/api')
		? `${API_BASE_URL}${apiPath.slice(4)}`
		: `${API_BASE_URL}${apiPath}`;
	const res = await fetch(fullUrl, {
		headers: token ? { Authorization: `Bearer ${token}` } : {}
	});
	if (!res.ok) {
		throw new Error(`Failed to fetch map layer (${res.status})`);
	}
	const blob = await res.blob();
	return URL.createObjectURL(blob);
}

/**
 * Converts a sequence of hex coordinates into a smooth quadratic Bezier SVG path.
 */
export function routeToSvgPath(hexes: RouteCoord[], hexSize: number): string {
	if (hexes.length < 2) return '';
	const pts = hexes.map((h) => hexToPixel(h.q, h.r, hexSize));
	if (pts.length === 2) {
		return `M ${pts[0].x} ${pts[0].y} L ${pts[1].x} ${pts[1].y}`;
	}
	let d = `M ${pts[0].x} ${pts[0].y}`;
	for (let i = 1; i < pts.length - 1; i++) {
		const midX = (pts[i].x + pts[i + 1].x) / 2;
		const midY = (pts[i].y + pts[i + 1].y) / 2;
		d += ` Q ${pts[i].x} ${pts[i].y} ${midX} ${midY}`;
	}
	const last = pts[pts.length - 1];
	d += ` L ${last.x} ${last.y}`;
	return d;
}
