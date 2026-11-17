export function getTerrainColor(terrain: string): string {
	switch (terrain.toLowerCase()) {
		case 'plains':
			return '#6e8b5b';
		case 'forest':
			return '#2d5a36';
		case 'mountain':
			return '#6d655e';
		case 'water':
			return '#2b5470';
		case 'desert':
			return '#b9894f';
		case 'swamp':
			return '#465436';
		default:
			return '#78716c';
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
