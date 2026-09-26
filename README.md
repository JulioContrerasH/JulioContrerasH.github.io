# Web personal

Sitio estático en Astro que se genera por completo desde `data/`. El globo 3D es decoración sobre contenido real: todo se ve aunque el WebGL no cargue.

## Correr en local

```bash
export PATH=/data/users/julio/.conda/envs/web/bin:$PATH
npm install
npm run dev        # http://localhost:4321
npm run build      # genera dist/
npm run preview    # sirve dist/
```

## Editar contenido

Todo vive en `data/` y se edita a mano:

| Archivo | Qué lleva |
| --- | --- |
| `data/profile.yaml` | Nombre, bio ES/EN, foto, afiliaciones, links, email |
| `data/projects.yaml` | Proyectos. `include: true/false` decide si salen; `order` el orden; `type: ground` pone punto en el globo (necesita `coords`), `type: orbit` pone satélite |
| `data/publications.yaml` | Papers con DOI |
| `data/talks.yaml` | Charlas y eventos |
| `data/ui.yaml` | Textos de interfaz y capítulos (Perú, Valencia, Ahora) en ES/EN |

Para añadir un paper: copia una entrada de `publications.yaml`, cambia `title`, `year`, `venue` y `doi`. Nada más.

Para añadir un proyecto con lugar: añade la entrada en `projects.yaml` con `type: ground`, `coords: {lon, lat}` y `include: true`. Aparece como punto en el globo y como tarjeta.

La foto va en `public/assets/img/` (hoy `author.jpeg` desde `static/img/`, ver `data/profile.yaml`).

## Estructura

- `src/lib/content.ts` — lee y ordena los YAML.
- `src/components/` — tarjetas, listas, globo, CV.
- `src/pages/` — rutas EN (por defecto); `src/pages/es/` — rutas ES.
- `scripts/globe_texture.py` — regenera la textura de puntos del globo.
- `scripts/ne_110m_land.geojson` — costas de Natural Earth para esa textura.

## Publicar

Push a `main` dispara `.github/workflows/deploy.yml` y publica en GitHub Pages. El CV viejo vive en su propio repo (`JulioContrerasH/CV`); el sitio Hugo anterior quedó en la rama `legacy-hugo`.
