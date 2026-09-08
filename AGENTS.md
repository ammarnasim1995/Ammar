# Base44 Dev Environment

## Project Overview
Family Medicine Clinic — a Vite + React + TypeScript single-page app with an AI patient assistant powered by Google Gemini (`@google/genai`).

## Setup
- **Runtime:** Node.js 22 (via `docker-compose.base44.yml`)
- **Dev server:** Vite on port 3000, bind-mounted from source with live reload
- **Dependencies:** `npm install` runs automatically at container start
- **Entry point:** `index.tsx` → `App.tsx`

## Key Files
- `vite.config.ts` — Vite config; injects `GEMINI_API_KEY` into `process.env.API_KEY` / `process.env.GEMINI_API_KEY` via `define`
- `services/geminiService.ts` — Gemini chat client; initialized at module load with `process.env.API_KEY`
- `components/BookingWizard.tsx` — multi-step appointment booking UI
- `components/AiAssistant.tsx` — AI chat widget
- `constants.ts` — clinic services, doctors, and AI system instruction

## Secrets
- `GEMINI_API_KEY` — required for the AI assistant. Without a real key, the app boots and the booking wizard works, but the AI chat returns an error message. Get a key from https://aistudio.google.com/apikey.

## Verification
- App is live when `curl localhost:3000` returns the HTML with `<div id="root">`
- Vite dev server logs show "ready in" and module compilation
- The booking wizard works without the API key; the AI assistant needs it

## Quirks
- `index.html` uses an importmap pointing to `aistudiocdn.com`, but Vite resolves deps from `node_modules` during dev — both work
- `constants.ts` has a typo in the DOCTORS availability array (missing comma between 'Thu' and 'Fri')
