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

export function getFactionBadgeStyle(faction: string | null): string {
	switch (faction) {
		case 'Collegium':
			return 'background:rgba(59,130,246,0.2);border-color:rgba(59,130,246,0.4)';
		case 'Limes':
			return 'background:rgba(245,158,11,0.2);border-color:rgba(245,158,11,0.4)';
		default:
			return '';
	}
}
