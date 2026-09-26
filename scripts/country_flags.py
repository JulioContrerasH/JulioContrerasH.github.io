"""Genera las franjas de bandera (semitransparentes) para los países del globo.

Uso:
    /data/users/julio/.conda/envs/deep/bin/python scripts/country_flags.py

Entrada: ne_110m_admin_0_countries.geojson (Natural Earth, lo descarga si falta).
Salida: public/assets/geo/country-stripes.json
"""

from pathlib import Path
import json
import urllib.request

from shapely.geometry import box, mapping, shape

ROOT = Path(__file__).resolve().parent.parent
GEO = ROOT / "scripts" / "ne_110m_admin_0_countries.geojson"
OUT = ROOT / "public" / "assets" / "geo" / "country-stripes.json"
GEO_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_admin_0_countries.geojson"
)

# iso: (eje, [colores], [pesos]) — eje 'lon' = franjas verticales, 'lat' = horizontales.
FLAGS = {
    "PER": ("lon", ["#d91023", "#f4f4f4", "#d91023"], [1, 1, 1]),
    "ESP": ("lat", ["#aa151b", "#f1bf00", "#aa151b"], [1, 2, 1]),
    "AUT": ("lat", ["#ed2939", "#f4f4f4", "#ed2939"], [1, 1, 1]),
}


def load() -> dict:
    if not GEO.exists():
        GEO.parent.mkdir(parents=True, exist_ok=True)
        print(f"descargando {GEO_URL}")
        urllib.request.urlretrieve(GEO_URL, GEO)
    return json.loads(GEO.read_text())


def main() -> None:
    data = load()
    features = []

    for feature in data["features"]:
        props = feature["properties"]
        code = props.get("ADM0_A3") or props.get("ISO_A3")
        if code not in FLAGS:
            continue

        axis, colors, weights = FLAGS[code]
        geom = shape(feature["geometry"])
        minx, miny, maxx, maxy = geom.bounds
        total = sum(weights)
        cursor = minx if axis == "lon" else miny
        span = (maxx - minx) if axis == "lon" else (maxy - miny)

        for color, weight in zip(colors, weights):
            size = span * weight / total
            if axis == "lon":
                band = box(cursor, miny - 1, cursor + size, maxy + 1)
            else:
                band = box(minx - 1, cursor, maxx + 1, cursor + size)
            piece = geom.intersection(band)
            cursor += size
            if piece.is_empty:
                continue
            features.append(
                {
                    "type": "Feature",
                    "properties": {"id": code.lower(), "color": color},
                    "geometry": mapping(piece),
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"{OUT} listo ({len(features)} franjas, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
