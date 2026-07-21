# NyayaSarthi Frontend — Setup Guide (No Coding Experience Needed)

This is the real website — same screens you already liked in the prototype, but now
every button actually talks to your real backend: real PDF uploads, real Gemini AI
extraction, real database storage.

## Before you start

Make sure your backend from before is already running (you should still be able to
open http://localhost:8000/docs in your browser). This frontend won't work without it.

## Setup with Claude Code

1. Unzip this folder.
2. Open it in Claude Code (a separate window/session from the backend one is fine —
   they run independently).
3. Paste this as your first message:

   > "Set up and run this frontend: install the dependencies with npm install, then
   > start it with npm run dev. Confirm it opens in the browser and tell me the
   > address."

4. It should open at **http://localhost:5173**

## Trying it for real

1. Click **Process New Judgment**
2. Upload an actual court judgment PDF (any real or sample one you have — scanned or
   digital both work, the backend detects which and handles it differently)
3. Watch it actually process — this takes real seconds because it's a real AI call,
   not the instant fake progress bar from before
4. Review the AI's real extracted directives, approve/edit/reject them
5. See them tracked on the real dashboard

## If the upload fails

The most common causes, in order of likelihood:
- Backend isn't running — check http://localhost:8000/healthz shows `{"status":"ok"}`
- Missing or invalid Gemini API key in the backend's `.env` file
- The PDF is very large or heavily scanned and OCR is taking a long time — give it a minute before assuming it failed

Paste the exact error text back to me and I'll help you fix it.

## What's different from the prototype you saw first

| Prototype (artifact) | This (real app) |
|---|---|
| Two hardcoded sample judgments | Any real PDF you upload |
| Instant fake "AI analysis" | Real Gemini API call, takes real time |
| Saved in your browser only | Saved in a real PostgreSQL database |
| No way to run outside this chat | Runs on your own machine, shareable, deployable |
