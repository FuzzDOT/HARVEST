# HARVEST

**Hackathon project by Team HARVEST - an end to end crop planning platform that combines agronomic rules, weather data, and profitability modeling to recommend what to plant next.**

---

## Overview

HARVEST is a full stack agricultural decision support system built during a hackathon.

It helps landowners and growers choose crops based on:
- expected profitability
- seasonality and eligibility rules
- weather forecasts and historical normals
- fertilizer fit and pricing context

The app supports both:
- **Short term planning** (monthly recommendations)
- **Long term planning** (12 month crop rotation plans)

---

## Hackathon Context

This repository is the team’s hackathon build: rapid, practical, and demo ready.

The goal was to ship a complete workflow quickly from data loading and scoring logic in the backend to an interactive frontend that makes recommendations easy to explore.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript + Vite |
| Styling | Custom CSS / inline style system |
| Backend API | FastAPI + Pydantic |
| Data/Compute | Python + pandas |
| Async integrations | aiohttp |
| Runtime | Node.js + Python |

---

## Core Features

### Product features
- Input driven planning flow (plan type, state, month, investment, land area)
- **Short term mode** for immediate monthly crop actions
- **Long term mode** for annual crop rotation sequencing
- Plan selector for browsing backend returned options
- Revenue estimate based on selected crop recommendation and land size
- Crop specific image mapping for visual result cards

### Backend capabilities
- Profit, ROI, and ranking pipelines for crop recommendations
- Crop eligibility filters by month and region
- Fertilizer matching and recommendation enrichment
- Forecast based and normals based weather handling
- Location based prediction endpoint for frontend clients
- Session backed result access endpoints
- Optional image sending integration for external APIs

---

## Repository Structure

```text
HARVEST/
├── Backend/
│   ├── main.py                  # FastAPI app + API routes
│   ├── src/
│   │   ├── pipelines/           # short term + long term prediction pipelines
│   │   ├── model/               # profit/yield/confidence/ranking logic
│   │   ├── rules/               # crop eligibility + fertilizer matching rules
│   │   ├── io_/                 # CSV/data loading and writing utilities
│   │   ├── services/            # location prediction + image service integration
│   │   ├── cli/                 # command line entry points
│   │   └── utils/               # sessions, tables, date helpers
│   ├── data/                    # crops, weather, parcel, fertilizer, and price data
│   ├── images/                  # crop imagery assets
│   └── requirements.txt
├── Frontend/
│   └── harvest ui/
│       ├── src/App.tsx          # main UI flow and API integration
│       ├── src/assets/          # logos, backgrounds, crop images
│       └── package.json
├── requirements.txt             # backend dependency list
└── README.md
```

---

## Key API Endpoints

Main backend routes include:

- `POST /api/v1/predict/month` - monthly recommendations
- `POST /api/v1/plan/annual` - annual rotation plan
- `POST /api/v1/predict/location` - location/timezone based prediction
- `GET /api/v1/health` and `GET /health`   health checks
- `GET /docs` - Swagger UI

The backend also exposes data, comparison, utility, and per session result endpoints in `Backend/main.py`.

---

## Running Locally

### 1) Backend

```bash
cd Backend
pip install -r requirements.txt
python main.py
```

Backend URLs:
- API base: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 2) Frontend

```bash
cd Frontend/harvest-ui
npm install
npm run dev
```

Optional frontend commands:

```bash
npm run lint
npm run build
npm run preview
```

---

## Data Inputs

The backend expects CSV datasets in `Backend/data/` for:
- crops
- fertilizers
- market prices
- weather forecast
- weather normals
- parcel metadata

---

## Team

- Faaz Mohamed - Backend / ML
- Evan Jackson - Frontend
- Ayaan Mahajan - Frontend
- Zhengyao Zhou - Data Management

---

## Notes

- This project was built for a hackathon and optimized for rapid delivery and end to end demo functionality.
- If you are extending it for production, start with stronger validation, tighter CORS policy, and deployment grade environment management.
