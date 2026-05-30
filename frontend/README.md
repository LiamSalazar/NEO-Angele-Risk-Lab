# Neo Angele Risk Lab Frontend

Mission-control frontend for the Neo Angele Risk Lab FastAPI backend. It presents a dark space observatory for NEO risk ranking, object profiles, Monte Carlo simulations, ML/leakage status, GNN graph research, domain aggregates and pipeline readiness.

## Stack

- React + TypeScript + Vite
- Tailwind CSS
- React Router
- TanStack Query
- Framer Motion
- ECharts
- Lucide React
- Radix-based UI primitives
- React Three Fiber / Three.js
- ESLint, Prettier, Vitest, React Testing Library

## Setup

```bash
cd frontend
npm install
```

Create local env from the example if needed:

```bash
cp .env.example .env
```

Default backend URL:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Commands

```bash
npm run dev
npm run lint
npm run test
npm run build
```

## Backend Required

Run FastAPI from the repository root:

```bash
python -m neo_ange.cli api run --host 127.0.0.1 --port 8000 --reload
```

The frontend consumes local API endpoints directly through `VITE_API_BASE_URL`. Missing data, partial success, `insufficient_data`, `skipped_missing_dependency` and network failures are rendered as observatory states rather than hard UI failures.

## Routes

- `/` Mission Control
- `/ranking` Risk Ranking
- `/objects` and `/objects/:objectKey` Asteroid Profile/Search
- `/monte-carlo` Monte Carlo Lab
- `/ml-lab` ML & Leakage Lab
- `/gnn` GNN Research Lab
- `/domain` Domain Explorer
- `/pipeline` Pipeline Monitor
- `/methodology` Methodology
