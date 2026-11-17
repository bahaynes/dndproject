import { get } from 'svelte/store';
import { auth } from '$lib/auth';
import { API_BASE_URL } from '$lib/config';

export type MapLayerMode = 'tactical' | 'topo' | 'satellite';

export interface LayerBounds {
	min_x: number;
	min_y: number;
	max_x: number;
	max_y: number;
}

export const EARTH_REGION_PRESETS = [
	{
		label: 'Iceland — Volcanic Frontier',
		min_lat: 63.8,
		min_lon: -20.5,
		max_lat: 64.6,
		max_lon: -18.5
	},
	{
		label: 'Scottish Highlands — Lochs & Glens',
		min_lat: 56.6,
		min_lon: -5.6,
		max_lat: 57.4,
		max_lon: -4.2
	},
	{
		label: 'Pacific Northwest — Puget Archipelago',
		min_lat: 47.4,
		min_lon: -123.2,
		max_lat: 48.3,
		max_lon: -122.0
	},
	{
		label: 'Dalmatian Coast — Island Chain',
		min_lat: 42.9,
		min_lon: 16.0,
		max_lat: 43.6,
		max_lon: 17.2
	}
];

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
