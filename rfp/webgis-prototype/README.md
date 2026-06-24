# DoSLR WebGIS — GIS Workbench Prototype

**RFP M-13/1237/2025 · Govt. of Puducherry, DoSLR · Module 2 (Sec 18.3.x)**

Single-page OpenLayers workbench for proposal demos. **Basemap tiles are live** (OSM, Esri World Imagery, Carto). **All cadastral overlays, attributes, and workflow actions are fictional** — no backend.

## Quick start

```bash
cd webgis-prototype
python -m http.server 8080
```

Open http://localhost:8080 (or serve `index.html` locally — CDN basemaps need network).

## Layout

| Area | Purpose |
|------|---------|
| **Demo banner** | Fictional data disclaimer |
| **Menu + toolbar** | All RFP 18.3.x features as defunct UI (toast on click) |
| **Map (center)** | OpenLayers map centered on Puducherry (11.9375°N, 79.8083°E) |
| **Layer panel (right)** | Photoshop-style groups: visibility toggles + opacity sliders |
| **Attribute dock (bottom)** | Selected parcel RoR fields (RBAC-aware owner masking) |

## Live vs mock

| Layer | Source |
|-------|--------|
| OpenStreetMap | Live CDN tiles |
| Esri World Imagery | Live CDN tiles |
| Carto Positron | Live CDN tiles |
| Parcels, FMB, admin boundaries, variance, DGPS, CollabLand, ortho | Region-aware synthetic cadastral GeoJSON generated in `js/mock-data.js` |

## Cadastral dataset notes (2026-06)

- Attempted real open cadastral vectors first for Puducherry and enclaves.
- Official DoSLR/Nilamagal services expose FMB copies via CSC workflow, not a public editable parcel GeoJSON/WFS bulk download.
- Bhuvan exposes cadastral reference mainly as WMS visualization layer, not guaranteed parcel-edit vector export for this prototype flow.
- Implemented high-fidelity synthetic cadastral fallback with real region/village naming and editable polygons.

Checked sources:

- [Puduvaisevai portal](https://puduvaisevai.py.gov.in/)
- [National Services Portal: digitized FMB copy service](https://services.india.gov.in/service/detail/directorate-of-survey-and-land-records-issue-of-digitized-cadastral-map-fmb-copy-puducherry-1)
- [Bhuvan OGC service documentation](https://bhuvan.nrsc.gov.in/wiki/index.php/How_to_use_WMS_services)
- [Bhuvan cadastral reference layer endpoint sample](https://bhuvan-vec1.nrsc.gov.in/bhuvan/gwc/service/wms?service=WMS&request=GetMap&layers=cadastral:cadastral_india&styles=&format=image/png&transparent=true&version=1.1.1&width=256&height=256&srs=EPSG:3857&bbox=9129485.784324883,2849572.414471373,9129638.658381453,2849725.288527942)

## Region switching

- Use `View -> Switch region`.
- Available regions: Puducherry, Karaikal, Mahe, Yanam.
- On switch, parcels + admin boundaries + FMB + analytics layers reload for the selected region and map recenters.

## Synthetic parcel schema

Each parcel feature includes:

- `surveyNo`, `subDiv`, `ulpin`, `village`, `taluk`, `ward`, `region`, `areaSqM`, `owner`, `status`, `id`

Counts (approx):

- Puducherry: 240 parcels
- Karaikal: 225 parcels
- Mahe: 196 parcels
- Yanam: 210 parcels

## RFP feature coverage (UI only)

- **18.3.1** Data viz layers — View menu + layer panel
- **18.3.2** Search, navigation, measurement, spatial queries, print/export — Tools menu + toolbar
- **18.3.3** Editing — Edit menu (vertex, subdivide, amalgamate, rubber sheet, version/audit)
- **18.3.4** Online mutation, Nilamagal sync, certified extract — Revenue menu + modals
- **18.3.5** AgriStack / DCS — Integrations menu + modal
- **18.3.6** ULPIN lifecycle — Integrations menu + modal
- **18.3.7** RBAC — Header role switcher + matrix modal
- **18.3.8** Anomaly analytics — Admin menu + modal
- **18.4.2** Georef workbench — GCP table, dry-run, transform select

## Files

```
index.html          Main SPA shell
css/styles.css      DoSLR branding (ink #13213B, accent #D9542B, paper #EEF1F5)
js/mock-data.js     Fictional GeoJSON + parcel attributes
js/map-engine.js    OpenLayers basemaps + overlay layers
js/app.js           Layer panel, attribute table, defunct action toasts
```

## Stack

Vanilla HTML/CSS/JS · OpenLayers 9 · Turf.js 7 (CDN) · no build step.

## Disclaimer

Not production software. Do not use for real land records.