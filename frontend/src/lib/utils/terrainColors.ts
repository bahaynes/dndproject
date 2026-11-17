export function getTerrainColor(terrain: string): string {
	switch (terrain.toLowerCase()) {
		case 'plains':
			return '#90EE90';
		case 'forest':
			return '#228B22';
		case 'mountain':
			return '#808080';
		case 'water':
			return '#4682B4';
		case 'desert':
			return '#F4A460';
		case 'swamp':
			return '#556B2F';
		default:
			return '#D3D3D3';
	}
}

const FACTION_BADGE_STYLES = [
	'background:rgba(59,130,246,0.2);border-color:rgba(59,130,246,0.4)',
	'background:rgba(245,158,11,0.2);border-color:rgba(245,158,11,0.4)',
	'background:rgba(16,185,129,0.2);border-color:rgba(16,185,129,0.4)',
	'background:rgba(239,68,68,0.2);border-color:rgba(239,68,68,0.4)'
];

export function getFactionBadgeStyle(faction: string | null): string {
	if (!faction) return '';
	let hash = 0;
	for (let i = 0; i < faction.length; i++) {
		hash = (hash * 31 + faction.charCodeAt(i)) >>> 0;
	}
	return FACTION_BADGE_STYLES[hash % FACTION_BADGE_STYLES.length];
}
