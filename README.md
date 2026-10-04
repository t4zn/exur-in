# Exur

**Atmospheric intelligence for cleaner, safer Indian cities.**

Exur is a Next.js platform for exploring air quality, atmospheric conditions,
pollution sources, satellite observations, and practical health guidance across
the Delhi-NCR and Indo-Gangetic economic corridor.

It combines live environmental APIs, geospatial visualization, atmospheric
reasoning, citizen radiometry, satellite imagery, and an AI advisor in one
interface.

> Exur is a research/demo product and decision-support interface. It is not a
> substitute for official air-quality advisories, medical advice, or emergency
> services.

## Product capabilities

### Corridor air-shed intelligence

The corridor dashboard displays station-level air-quality and weather telemetry
across Delhi-NCR and nearby northern economic corridors.

- AQI and PM2.5/PM10 measurements
- Wind direction and speed
- Boundary-layer estimates
- Regional search and filtering
- Interactive Leaflet map
- Live refresh and source metadata

Open the dashboard at [`/corridor`](http://localhost:3000/corridor).

### INSAT and satellite analysis

The INSAT workspace provides a satellite-oriented view of atmospheric change and
pollution events.

- Time-based scan selection
- IR, visible, SWIR, and water-vapour channels
- AOD observations
- NASA FIRMS fire context
- Dusk stubble-burning window analysis
- Sector and hotspot inspection
- Satellite imagery and composite modes

Open it at [`/insat`](http://localhost:3000/insat).

### Source attribution

The attribution workspace estimates likely upwind pollution sources from a
selected receptor station.

- Historical wind observations
- Backward kinematic particle trajectories
- Dispersion envelope visualization
- Industrial cluster registry
- Ranked candidate sources
- Distance, bearing, and confidence-style scoring

Open it at [`/attribution`](http://localhost:3000/attribution).

### Citizen radiometry

The radiometry workspace estimates atmospheric optical depth and air-quality
signals from outdoor sky imagery and camera metadata.

- Image upload and demo observation
- EXIF extraction
- Scene and authenticity validation
- Luminance and pixel statistics
- Optical-depth estimation
- Approximate AQI/PM guidance
- Ground-truth comparison when location data is available
- Optional vision-model analysis

Open it at [`/radiometry`](http://localhost:3000/radiometry).

### Atmospheric advisor

The advisor is a ChatGPT-style assistant focused on Indian air-quality and
respiratory-health questions.

- Gemma-powered streaming responses
- Optional Groq streaming fallback
- Local atmospheric reasoning fallback
- Relocation and microclimate recommendations
- Asthma and vulnerable-person guidance
- Suggested follow-up questions
- Searchable local conversation history
- Persistent sessions in browser storage
- Copy and regenerate actions
- ElevenLabs text-to-speech with browser speech fallback

Open it at [`/advisor`](http://localhost:3000/advisor).

The floating advisor is available throughout the rest of the application.

## Tech stack

- [Next.js 16](https://nextjs.org/) App Router
- [React 19](https://react.dev/)
- TypeScript
- Leaflet and React Leaflet
- Open-Meteo air-quality and weather APIs
- OpenWeather support when configured
- Google Gemini/Gemma API
- Optional Groq API
- Optional ElevenLabs text-to-speech
- Google Earth Engine integration hooks
- NASA FIRMS fire data
- OpenAQ-compatible air-quality integration

## Project structure

```text
src/
├── app/
│   ├── advisor/                 AI advisor workspace
│   ├── api/
│   │   ├── chat/                Streaming AI chat endpoint
│   │   ├── voice/               ElevenLabs server-side voice endpoint
│   │   ├── corridor/            Corridor telemetry endpoint
│   │   ├── satellite/           Satellite data endpoint
│   │   ├── weather/             Weather endpoint
│   │   └── ...
│   ├── attribution/             Pollution source attribution UI
│   ├── corridor/                Live air-shed dashboard
│   ├── insat/                   Satellite analysis UI
│   ├── radiometry/              Citizen radiometry UI and calculations
│   └── page.tsx                 Product homepage
├── components/                  Shared UI and map components
├── data/                        Domain datasets and industrial registry
├── hooks/                       Client data and audio hooks
├── lib/
│   ├── advisorEngine.ts         Local atmospheric advice engine
│   ├── attribution.ts           Particle and source attribution logic
│   └── earthEngine.ts           Earth Engine integration helpers
└── types/                       Shared TypeScript types
```

The example file contains variable names and safe defaults only. Keep actual
credentials in the deployment platform or in the ignored `.env.local` file.

## Requirements

- Node.js 20 or newer
- npm, pnpm, or another compatible package manager
- API keys only for features that require external services

The repository declares `pnpm@10.17.0` as its package manager. npm can also run
the scripts when pnpm is not available.

## Installation

```bash
git clone <repository-url>
cd exur-in
pnpm install
```

Or with npm:

```bash
npm install
```

## Environment configuration

Copy [`.env.example`](.env.example) to `.env.local` and add credentials in the
repository root. Never commit `.env.local` or expose server-side credentials in
`NEXT_PUBLIC_*` variables.

```env
# AI advisor
GEMINI_API_KEY=your_gemini_or_gemma_key
# Optional alias supported by the app:
# GEMMA_API_KEY=your_gemma_key

# Optional Groq provider
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile

# ElevenLabs advisor voice
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=your_voice_id
ELEVENLABS_MODEL_ID=eleven_multilingual_v2

# Optional data providers
OPENWEATHER_API_KEY=your_openweather_key
OPENAQ_API_KEY=your_openaq_key
NASA_FIRMS_KEY=your_nasa_firms_key

# Optional client-side map/integration configuration
NEXT_PUBLIC_CARTO_KEY=your_carto_key
```

### Advisor provider behavior

The streaming chat endpoint at [`src/app/api/chat/route.ts`](src/app/api/chat/route.ts)
uses this order:

1. **Gemma** when selected or when Auto is selected and Gemma is configured.
2. **Groq** when selected, or when Auto needs a provider fallback.
3. **Local Atmospheric Physics Fallback** when external AI providers are
   unavailable.

The local fallback is deterministic domain guidance and should be treated as a
fallback/demo mode, not as a live generative model.

### Voice behavior

The voice endpoint at [`src/app/api/voice/route.ts`](src/app/api/voice/route.ts)
keeps the ElevenLabs API key on the server. The client requests audio by
sending text to `/api/voice`.

If ElevenLabs is not configured or unavailable, the advisor falls back to the
browser's built-in speech synthesis where supported.

## Running locally

Install dependencies and start the development server:

```bash
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

Available scripts:

```bash
pnpm dev          # Start Next.js development server
pnpm build        # Create a production build
pnpm start        # Start the production server
pnpm lint         # Run ESLint
```

The equivalent `npm run <script>` commands are supported.

## Chat memory and privacy

Advisor conversations are stored locally in the browser:

- Full advisor sessions use the versioned `exur_advisor_sessions_v3` key.
- Older Exur advisor storage formats are migrated when possible.
- Floating advisor messages use a separate local storage key.
- No chat database or account sync is currently required.

Clear browser site data to remove locally stored conversations. Do not use the
local-storage memory model for sensitive medical records or confidential
personal information.

## Data and attribution notes

The application combines live external observations with modeled, calibrated,
and demonstration data. Some domain datasets in [`src/data/`](src/data/) are
static or synthetic representations intended for product demonstration.

Relevant data and integration sources include:

- Open-Meteo air-quality and weather services
- OpenWeather, when configured
- NASA FIRMS
- OpenAQ-compatible endpoints
- OpenStreetMap-derived industrial locations
- Google Earth Engine integrations
- CPCB/DPCC-style station references and corridor metadata

Always verify operational decisions against current official sources.

## Design system

The interface follows an Apple-inspired visual system implemented in
[`src/app/globals.css`](src/app/globals.css) and shared components:

- White, parchment, and near-black canvas modes
- Action Blue as the primary interactive color
- SF Pro/system font stack with Inter fallback
- Rich spacing and restrained elevation
- Responsive layouts for desktop and mobile

The product and feature specification is documented in
the source structure and the technical notes in [`docs/`](docs/).

## Deployment

Build the application:

```bash
npm run build
```

Start the production server:

```bash
pnpm start
```

For Vercel or another hosting provider:

1. Configure the required environment variables in the deployment platform.
2. Keep API keys server-side.
3. Confirm external provider quotas and allowed origins.
4. Test streaming responses and voice playback in the deployed environment.
5. Configure appropriate rate limits before public release.

## Troubleshooting

### Advisor returns local fallback responses

Check that `GEMINI_API_KEY` or `GEMMA_API_KEY` is present, valid, and loaded by
the current server process. Restart the server after changing `.env.local`.

### Advisor stream does not update

Restart the server and hard-refresh the browser. Inspect the terminal for
provider errors and confirm that the selected model is available to the
configured provider account.

### ElevenLabs voice is unavailable

Confirm all three voice variables are set:

```env
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

The advisor should still provide browser speech fallback when supported.

### Maps do not render

Leaflet components are dynamically imported with SSR disabled. Check browser
console errors, network access to tile providers, and the relevant map
component under [`src/components/`](src/components/).

## Status

Exur is an actively developed prototype focused on atmospheric intelligence,
public-interest climate tooling, and hackathon/demo workflows. Production use
requires stronger data validation, authentication, observability, rate
limiting, and formal medical/data-governance review.
