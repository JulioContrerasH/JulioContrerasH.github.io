"""Extrae los lugares donde Julio hizo proyectos, para resaltarlos en el globo.

Uso:
    /data/users/julio/.conda/envs/deep/bin/python scripts/highlight_countries.py

Entrada: ne_110m_admin_0_countries.geojson (Natural Earth, lo descarga si falta).
Salida: public/assets/geo/countries.json
"""

from pathlib import Path
import json
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
GEO = ROOT / "scripts" / "ne_110m_admin_0_countries.geojson"
OUT = ROOT / "public" / "assets" / "geo" / "countries.json"
GEO_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_admin_0_countries.geojson"
)

# País -> ids de proyectos (y charlas con prefijo talk:) hechos ahí.
COUNTRIES = {
    "PER": ["andes-datacube", "tesis-mss", "insideo", "cloudsen12plus"],
    "ESP": ["sen2naip", "sen2sr", "sen2neon", "methanset", "taco", "cubexpress"],
    "AUT": ["sen2sr", "talk:lps25-sen2sr"],
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
        if code in COUNTRIES:
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "id": code.lower(),
                        "name": props.get("NAME_ES") or props.get("NAME"),
                        "name_en": props.get("NAME_EN") or props.get("NAME"),
                        "projects": COUNTRIES[code],
                    },
                    "geometry": feature["geometry"],
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"{OUT} listo ({len(features)} países, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
