# DoSLR WebGIS Minister Demo

Premium React + Vite demo application for a state-level WebGIS showcase.

## Project Path

`C:\Users\Fahad\Desktop\rfp\doslr-platform\`

## Stack

- React + Vite + TypeScript
- React Router
- Tailwind CSS
- Framer Motion
- OpenLayers 9
- Turf.js
- Lucide React

## Run

```bash
npm install
npm run dev
```

Default dev URL is usually `http://localhost:5173/`.

Production build:

```bash
npm run build
```

## Demo Pages

- `/login` - glassmorphism login (any credentials work)
- `/app` - main map workbench
- `/workflows/online-mutation` - full interactive mutation demo
- `/workflows/georeferencing` - interactive georeferencing flow
- `/workflows/field-mobile`
- `/workflows/certified-extract`
- `/workflows/anomaly-pipeline`
- `/workflows/search-rbac`
- `/workflows/citizen-search`
- `/workflows/mutation-sync-back`
- `/workflows/field-georeferencing`

## Interaction Coverage

- **Fully interactive:** Online Mutation (submit -> queue -> preview -> approve/reject with mandatory reason -> sync -> timeline)
- **Interactive (step/state):** Georeferencing
- **Interactive generic flows:** Remaining workflows with 5-step progression + approve/reject status simulation

## Notes

- Region and layer semantics are adapted from the previous prototype mock data model.
- Map tooling included: vertex edit, split, amalgamate (gap-tolerant Turf union), measure, and buffer.
