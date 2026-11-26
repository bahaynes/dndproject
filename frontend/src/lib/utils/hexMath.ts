export interface HexCoord {
    q: number;
    r: number;
}

export interface PixelCoord {
    x: number;
    y: number;
}

export const HEX_SIZE = 60;

export function hexToPixel(q: number, r: number, size: number = HEX_SIZE): PixelCoord {
    const x = size * (3 / 2 * q);
    const y = size * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r);
    return { x, y };
}

export function pixelToHex(x: number, y: number, size: number = HEX_SIZE): HexCoord {
    const q = (2 / 3 * x) / size;
    const r = (-1 / 3 * x + Math.sqrt(3) / 3 * y) / size;
    return hexRound(q, r);
}

function hexRound(q: number, r: number): HexCoord {
    let s = -q - r;
    let rq = Math.round(q);
    let rr = Math.round(r);
    let rs = Math.round(s);

    const q_diff = Math.abs(rq - q);
    const r_diff = Math.abs(rr - r);
    const s_diff = Math.abs(rs - s);

    if (q_diff > r_diff && q_diff > s_diff) {
        rq = -rr - rs;
    } else if (r_diff > s_diff) {
        rr = -rq - rs;
    } else {
        rs = -rq - rr;
    }

    return { q: rq, r: rr };
}

export function hexDistance(a: HexCoord, b: HexCoord): number {
    return (Math.abs(a.q - b.q) + Math.abs(a.q + a.r - b.q - b.r) + Math.abs(a.r - b.r)) / 2;
}

// Generates points string for an SVG polygon
export function hexCornerPoints(size: number = HEX_SIZE): string {
    const points: string[] = [];
    for (let i = 0; i < 6; i++) {
        const angle_deg = 60 * i;
        const angle_rad = Math.PI / 180 * angle_deg;
        const x = size * Math.cos(angle_rad);
        const y = size * Math.sin(angle_rad);
        points.push(`${x},${y}`);
    }
    return points.join(" ");
}

export interface ViewBoxRect {
    x: number;
    y: number;
    w: number;
    h: number;
}

export interface LayerBoundsRect {
    min_x: number;
    min_y: number;
    max_x: number;
    max_y: number;
}

/**
 * Compute a centered SVG viewBox that fits all hexes (and optional layerBounds)
 * with comfortable padding, matched to the container's aspect ratio.
 */
export function computeMapViewBox(
    hexes: HexCoord[],
    hexSize: number = HEX_SIZE,
    layerBounds: LayerBoundsRect | null = null,
    aspectRatio: number = 16 / 9
): ViewBoxRect {
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;

    if (layerBounds) {
        minX = Math.min(minX, layerBounds.min_x);
        minY = Math.min(minY, layerBounds.min_y);
        maxX = Math.max(maxX, layerBounds.max_x);
        maxY = Math.max(maxY, layerBounds.max_y);
    }

    for (const h of hexes) {
        const p = hexToPixel(h.q, h.r, hexSize);
        minX = Math.min(minX, p.x - hexSize);
        minY = Math.min(minY, p.y - hexSize);
        maxX = Math.max(maxX, p.x + hexSize);
        maxY = Math.max(maxY, p.y + hexSize);
    }

    if (!Number.isFinite(minX)) {
        return { x: -500, y: -300, w: 1000, h: 600 };
    }

    const pad = hexSize * 1.25;
    minX -= pad;
    minY -= pad;
    maxX += pad;
    maxY += pad;

    let w = maxX - minX;
    let h = maxY - minY;
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;

    if (aspectRatio > 0 && Number.isFinite(aspectRatio)) {
        const currentRatio = w / h;
        if (currentRatio < aspectRatio) {
            w = h * aspectRatio;
        } else {
            h = w / aspectRatio;
        }
    }

    return {
        x: cx - w / 2,
        y: cy - h / 2,
        w,
        h
    };
}
