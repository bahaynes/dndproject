"""Real-Earth region baker using AWS Terrarium DEM tiles and OSM natural features."""

from __future__ import annotations

import asyncio
import io
import logging
import math
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import httpx
import numpy as np
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

TERRARIUM_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
TILE_SIZE = 256
MAX_OUTPUT_DIM = 1200


@dataclass
class BakedMapResult:
    """Outputs produced by baking a real-Earth bounding box."""

    topo_png: bytes
    satellite_png: bytes
    layer_bounds: dict[str, float]
    hex_terrains: dict[tuple[int, int], str]
    zoom: int


def compute_hex_layer_bounds(hex_coords: Iterable[tuple[int, int]], hex_size: int) -> dict[str, float]:
    """Compute the SVG world-coordinate bounding box covering all hex polygons."""
    coords = list(hex_coords)
    if not coords:
        return {"min_x": -500.0, "min_y": -500.0, "max_x": 500.0, "max_y": 500.0}

    sqrt3 = math.sqrt(3.0)
    half_h = hex_size * sqrt3 / 2.0
    xs = [hex_size * (1.5 * q) for q, _ in coords]
    ys = [hex_size * (sqrt3 / 2.0 * q + sqrt3 * r) for q, r in coords]
    return {
        "min_x": min(xs) - hex_size,
        "min_y": min(ys) - half_h,
        "max_x": max(xs) + hex_size,
        "max_y": max(ys) + half_h,
    }


def _lat_lon_to_global_px(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    lat_clamped = max(-85.05112878, min(85.05112878, lat))
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n * TILE_SIZE
    lat_rad = math.radians(lat_clamped)
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * TILE_SIZE
    return x, y


def choose_zoom(min_lat: float, min_lon: float, max_lat: float, max_lon: float, max_tiles: int = 16) -> int:
    """Pick the highest zoom level (5..12) whose bbox fits within ``max_tiles``."""
    for z in range(12, 4, -1):
        x0, y1 = _lat_lon_to_global_px(min_lat, min_lon, z)
        x1, y0 = _lat_lon_to_global_px(max_lat, max_lon, z)
        tx0, tx1 = int(x0 // TILE_SIZE), int(x1 // TILE_SIZE)
        ty0, ty1 = int(y0 // TILE_SIZE), int(y1 // TILE_SIZE)
        count = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
        if count <= max_tiles:
            return z
    return 5


async def _fetch_terrarium_grid(
    min_lat: float, min_lon: float, max_lat: float, max_lon: float, zoom: int
) -> np.ndarray:
    """Download AWS Terrarium PNG tiles and return a cropped float32 elevation array (meters)."""
    gx0, gy1 = _lat_lon_to_global_px(min_lat, min_lon, zoom)
    gx1, gy0 = _lat_lon_to_global_px(max_lat, max_lon, zoom)
    if gx1 <= gx0 or gy1 <= gy0:
        raise ValueError("Invalid bounding box: max_lat/max_lon must be greater than min_lat/min_lon")

    tx0, tx1 = int(gx0 // TILE_SIZE), int(gx1 // TILE_SIZE)
    ty0, ty1 = int(gy0 // TILE_SIZE), int(gy1 // TILE_SIZE)

    tiles_w = (tx1 - tx0 + 1) * TILE_SIZE
    tiles_h = (ty1 - ty0 + 1) * TILE_SIZE
    mosaic = np.zeros((tiles_h, tiles_w, 3), dtype=np.uint8)

    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = []
        coords = []
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                url = TERRARIUM_URL.format(z=zoom, x=tx, y=ty)
                tasks.append(client.get(url))
                coords.append((tx, ty))
        responses = await asyncio.gather(*tasks)

    for (tx, ty), resp in zip(coords, responses):
        resp.raise_for_status()
        tile_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        ox = (tx - tx0) * TILE_SIZE
        oy = (ty - ty0) * TILE_SIZE
        mosaic[oy : oy + TILE_SIZE, ox : ox + TILE_SIZE] = np.asarray(tile_img, dtype=np.uint8)

    cx0 = max(0, int(round(gx0 - tx0 * TILE_SIZE)))
    cy0 = max(0, int(round(gy0 - ty0 * TILE_SIZE)))
    cx1 = min(tiles_w, max(cx0 + 2, int(round(gx1 - tx0 * TILE_SIZE))))
    cy1 = min(tiles_h, max(cy0 + 2, int(round(gy1 - ty0 * TILE_SIZE))))
    cropped = mosaic[cy0:cy1, cx0:cx1].astype(np.float32)

    elev = (cropped[:, :, 0] * 256.0 + cropped[:, :, 1] + cropped[:, :, 2] / 256.0) - 32768.0
    return elev


async def _fetch_osm_natural_masks(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    width_px: int,
    height_px: int,
) -> dict[str, np.ndarray]:
    """Best-effort query to Overpass API for natural water, rivers, woods, and wetlands."""
    masks = {
        "water": np.zeros((height_px, width_px), dtype=bool),
        "wood": np.zeros((height_px, width_px), dtype=bool),
        "wetland": np.zeros((height_px, width_px), dtype=bool),
    }

    query = (
        f"[out:json][timeout:10];"
        f"("
        f'way["natural"~"^(water|wood|wetland)$"]({min_lat},{min_lon},{max_lat},{max_lon});'
        f'way["waterway"~"^(river|stream)$"]({min_lat},{min_lon},{max_lat},{max_lon});'
        f");out geom;"
    )

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
    except Exception as exc:
        logger.warning("Overpass natural-feature fetch skipped: %s", exc)
        return masks

    gx0, gy1 = _lat_lon_to_global_px(min_lat, min_lon, 12)
    gx1, gy0 = _lat_lon_to_global_px(max_lat, max_lon, 12)
    span_x = max(1e-6, gx1 - gx0)
    span_y = max(1e-6, gy1 - gy0)

    imgs = {k: Image.new("L", (width_px, height_px), 0) for k in masks}
    draws = {k: ImageDraw.Draw(img) for k, img in imgs.items()}

    for el in elements:
        geom = el.get("geometry") or []
        if len(geom) < 2:
            continue
        tags = el.get("tags") or {}
        pts = []
        for pt in geom:
            px, py = _lat_lon_to_global_px(pt["lat"], pt["lon"], 12)
            ix = (px - gx0) / span_x * width_px
            iy = (py - gy0) / span_y * height_px
            pts.append((ix, iy))

        nat = tags.get("natural", "")
        waterway = tags.get("waterway", "")
        if waterway in ("river", "stream"):
            draws["water"].line(pts, fill=255, width=max(2, width_px // 400))
        elif nat in ("water", "wood", "wetland") and len(pts) >= 3:
            draws[nat].polygon(pts, fill=255)

    for k, img in imgs.items():
        masks[k] = np.asarray(img, dtype=np.uint8) > 0
    return masks


def _compute_hillshade(elev: np.ndarray, azimuth_deg: float = 315.0, altitude_deg: float = 45.0) -> tuple[np.ndarray, np.ndarray]:
    """Return (hillshade [0..1], slope_magnitude) from a 2D elevation array."""
    dy, dx = np.gradient(elev)
    slope = np.hypot(dx, dy)
    slope_rad = np.arctan(slope * 0.04)
    aspect = np.arctan2(-dx, dy)
    az_rad = math.radians(azimuth_deg)
    alt_rad = math.radians(altitude_deg)
    shade = (
        math.sin(alt_rad) * np.cos(slope_rad)
        + math.cos(alt_rad) * np.sin(slope_rad) * np.cos(az_rad - aspect)
    )
    return np.clip(shade, 0.25, 1.0), slope


def _interp_palette(norm: np.ndarray, stops: list[tuple[float, tuple[int, int, int]]]) -> np.ndarray:
    """Vectorized linear color-ramp interpolation over normalized [0..1] array."""
    out = np.zeros((*norm.shape, 3), dtype=np.float32)
    t = np.clip(norm, 0.0, 1.0)
    for idx in range(len(stops) - 1):
        p0, c0 = stops[idx]
        p1, c1 = stops[idx + 1]
        mask = (t >= p0) & (t <= p1) if idx == len(stops) - 2 else (t >= p0) & (t < p1)
        alpha = np.where(p1 > p0, (t - p0) / max(1e-6, p1 - p0), 0.0)
        for ch in range(3):
            out[:, :, ch] = np.where(mask, c0[ch] + (c1[ch] - c0[ch]) * alpha, out[:, :, ch])
    return out


def render_topo_and_satellite(
    elev: np.ndarray,
    masks: dict[str, np.ndarray],
) -> tuple[bytes, bytes]:
    """Render Topographical (parchment + contours) and Satellite (biome + relief) PNGs."""
    shade, slope = _compute_hillshade(elev)
    water_mask = masks["water"] | (elev <= 0.5)
    land_elev = np.where(water_mask, 0.0, np.maximum(0.0, elev))
    max_elev = max(200.0, float(np.percentile(land_elev, 98)))
    norm = np.clip(land_elev / max_elev, 0.0, 1.0)

    # 1. Topographical parchment palette
    topo_stops = [
        (0.0, (224, 211, 182)),
        (0.25, (212, 194, 158)),
        (0.55, (194, 169, 128)),
        (0.80, (171, 143, 108)),
        (1.0, (222, 214, 202)),
    ]
    topo_rgb = _interp_palette(norm, topo_stops) * (0.65 + 0.35 * shade[:, :, None])

    # Contour lines
    contour_step = 50.0 if max_elev <= 600 else (100.0 if max_elev <= 1600 else 250.0)
    level = np.floor(land_elev / contour_step)
    contour_edge = np.zeros_like(water_mask)
    contour_edge[:-1, :] |= level[:-1, :] != level[1:, :]
    contour_edge[:, :-1] |= level[:, :-1] != level[:, 1:]
    contour_edge &= ~water_mask

    index_level = np.floor(land_elev / (contour_step * 5.0))
    index_edge = np.zeros_like(water_mask)
    index_edge[:-1, :] |= index_level[:-1, :] != index_level[1:, :]
    index_edge[:, :-1] |= index_level[:, :-1] != index_level[:, 1:]
    index_edge &= ~water_mask

    topo_rgb[contour_edge] = np.array([120, 96, 68], dtype=np.float32)
    topo_rgb[index_edge] = np.array([78, 58, 38], dtype=np.float32)
    topo_rgb[masks["wood"] & ~water_mask] = topo_rgb[masks["wood"] & ~water_mask] * 0.85 + np.array([42, 72, 42]) * 0.15
    topo_rgb[water_mask] = np.array([62, 98, 120], dtype=np.float32)

    # 2. Satellite / Biome palette
    sat_stops = [
        (0.0, (74, 108, 62)),
        (0.30, (92, 118, 68)),
        (0.60, (118, 112, 84)),
        (0.82, (124, 118, 112)),
        (1.0, (228, 232, 236)),
    ]
    sat_rgb = _interp_palette(norm, sat_stops)
    sat_rgb[masks["wood"] & ~water_mask] = np.array([44, 78, 46], dtype=np.float32)
    sat_rgb[masks["wetland"] & ~water_mask] = np.array([68, 86, 56], dtype=np.float32)
    steep = (slope > np.percentile(slope, 85)) & ~water_mask
    sat_rgb[steep] = sat_rgb[steep] * 0.55 + np.array([105, 98, 92]) * 0.45
    sat_rgb = sat_rgb * (0.42 + 0.65 * shade[:, :, None])
    sat_rgb[water_mask] = np.array([28, 62, 86], dtype=np.float32)

    def _encode_png(arr: np.ndarray) -> bytes:
        buf = io.BytesIO()
        Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    return _encode_png(topo_rgb), _encode_png(sat_rgb)


def classify_hex_terrains(
    elev: np.ndarray,
    masks: dict[str, np.ndarray],
    hex_coords: Iterable[tuple[int, int]],
    hex_size: int,
    bounds: dict[str, float],
) -> dict[tuple[int, int], str]:
    """Sample baked elevation & natural masks at each hex center to assign terrain."""
    h_px, w_px = elev.shape
    span_x = max(1e-6, bounds["max_x"] - bounds["min_x"])
    span_y = max(1e-6, bounds["max_y"] - bounds["min_y"])
    sqrt3 = math.sqrt(3.0)
    water_mask = masks["water"] | (elev <= 0.5)
    land_elev = elev[~water_mask]
    mountain_thresh = float(np.percentile(land_elev, 78)) if land_elev.size > 0 else 800.0
    mountain_thresh = max(350.0, mountain_thresh)

    result: dict[tuple[int, int], str] = {}
    for q, r in hex_coords:
        hx = hex_size * (1.5 * q)
        hy = hex_size * (sqrt3 / 2.0 * q + sqrt3 * r)
        px = int(np.clip((hx - bounds["min_x"]) / span_x * (w_px - 1), 0, w_px - 1))
        py = int(np.clip((hy - bounds["min_y"]) / span_y * (h_px - 1), 0, h_px - 1))

        y0, y1 = max(0, py - 4), min(h_px, py + 5)
        x0, x1 = max(0, px - 4), min(w_px, px + 5)

        if float(np.mean(water_mask[y0:y1, x0:x1])) >= 0.45:
            result[(q, r)] = "water"
        elif float(np.mean(masks["wetland"][y0:y1, x0:x1])) >= 0.35:
            result[(q, r)] = "swamp"
        elif float(np.mean(elev[y0:y1, x0:x1])) >= mountain_thresh:
            result[(q, r)] = "mountain"
        elif float(np.mean(masks["wood"][y0:y1, x0:x1])) >= 0.30:
            result[(q, r)] = "forest"
        else:
            result[(q, r)] = "plains"
    return result


async def bake_earth_region(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    hex_coords: list[tuple[int, int]],
    hex_size: int,
) -> BakedMapResult:
    """Fetch real-Earth DEM + natural features and bake Topo & Satellite PNG layers."""
    bounds = compute_hex_layer_bounds(hex_coords, hex_size)
    world_w = max(1.0, bounds["max_x"] - bounds["min_x"])
    world_h = max(1.0, bounds["max_y"] - bounds["min_y"])
    if world_w >= world_h:
        out_w = MAX_OUTPUT_DIM
        out_h = max(256, int(round(MAX_OUTPUT_DIM * (world_h / world_w))))
    else:
        out_h = MAX_OUTPUT_DIM
        out_w = max(256, int(round(MAX_OUTPUT_DIM * (world_w / world_h))))

    zoom = choose_zoom(min_lat, min_lon, max_lat, max_lon)
    raw_elev = await _fetch_terrarium_grid(min_lat, min_lon, max_lat, max_lon, zoom)

    elev_img = Image.fromarray(raw_elev, mode="F").resize((out_w, out_h), resample=Image.Resampling.BILINEAR)
    elev = np.asarray(elev_img, dtype=np.float32)

    masks = await _fetch_osm_natural_masks(min_lat, min_lon, max_lat, max_lon, out_w, out_h)
    topo_png, sat_png = render_topo_and_satellite(elev, masks)
    terrains = classify_hex_terrains(elev, masks, hex_coords, hex_size, bounds)

    return BakedMapResult(
        topo_png=topo_png,
        satellite_png=sat_png,
        layer_bounds=bounds,
        hex_terrains=terrains,
        zoom=zoom,
    )
