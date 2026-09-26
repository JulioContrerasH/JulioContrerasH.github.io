"""Genera la textura de puntos del globo (estilo cobe) desde Natural Earth.

Uso:
    /data/users/julio/.conda/envs/deep/bin/python scripts/globe_texture.py

Necesita ne_110m_land.geojson; si no está, lo descarga.
Salida: public/assets/img/globe-dots.png (2048x1024, fondo transparente).
"""

from pathlib import Path
import json
import urllib.request

import numpy as np
from matplotlib.path import Path as MplPath
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
GEO = ROOT / "scripts" / "ne_110m_land.geojson"
OUT = ROOT / "public" / "assets" / "img" / "globe-dots.png"
TEXTURE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_land.geojson"
)

W, H = 4096, 2048
STEP = 0.6
DOT_R = 2.6
COLOR = (178, 168, 214, 235)


def load_geojson() -> dict:
    if not GEO.exists():
        GEO.parent.mkdir(parents=True, exist_ok=True)
        print(f"descargando {TEXTURE_URL}")
        urllib.request.urlretrieve(TEXTURE_URL, GEO)
    return json.loads(GEO.read_text())


def polygons(geojson: dict) -> list[np.ndarray]:
    out = []
    for feature in geojson["features"]:
        geom = feature["geometry"]
        coords = geom["coordinates"]
        if geom["type"] == "Polygon":
            coords = [coords]
        for polygon in coords:
            ring = np.array(polygon[0], dtype=float)
            if len(ring) >= 3:
                out.append(ring)
    return out


def main() -> None:
    rings = polygons(load_geojson())
    paths = [MplPath(ring) for ring in rings]

    lons = np.arange(-180.0, 180.0, STEP)
    lats = np.arange(-90.0, 90.0, STEP)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    points = np.column_stack([lon_grid.ravel(), lat_grid.ravel()])

    inside = np.zeros(len(points), dtype=bool)
    for path in paths:
        inside |= path.contains_points(points)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    px = (points[inside, 0] + 180.0) / 360.0 * W
    py = (90.0 - points[inside, 1]) / 180.0 * H
    for x, y in zip(px, py):
        draw.ellipse((x - DOT_R, y - DOT_R, x + DOT_R, y + DOT_R), fill=COLOR)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"{OUT} listo ({inside.sum()} puntos dibujados)")


if __name__ == "__main__":
    main()
