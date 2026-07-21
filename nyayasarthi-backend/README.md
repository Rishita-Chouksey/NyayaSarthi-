# NyayaSarthi Backend — Setup Guide (No Coding Experience Needed)

This is the real backend: it actually reads PDF judgments, actually calls Google's
Gemini AI to find the directives inside them, and actually stores everything in a
database — the same one your prototype simulated.

You will not need to write or understand any code to get this running. The easiest
way is to open this whole folder in **Claude Code** and let it do the setup for you.

## The easiest path: Claude Code

1. Install Claude Code (desktop app or `claude code` in a terminal — Claude can walk
   you through this if you're not sure how).
2. Open this `nyayasarthi-backend` folder in it.
3. Paste this as your first message:

   > "Set up this project on my machine: install Python dependencies from
   > requirements.txt, help me install PostgreSQL if I don't have it, create the
   > database, run seed.py, and then start the server with uvicorn. Walk me through
   > getting a free Gemini API key from https://aistudio.google.com/app/apikey and
   > putting it in a .env file. Then confirm everything is working by opening
   > http://localhost:8000/docs."

4. Claude Code will do the actual installing, configuring, and running — and ask you
   simple yes/no questions along the way if it needs a decision from you.

## What's actually in this folder, in plain terms

| File / folder | What it does |
|---|---|
| `app/models.py` | Defines the database tables (cases, directives, actions, audit log, etc.) |
| `app/services/extraction.py` | Reads the PDF and asks Gemini AI to find the directives — the "brain" of the product |
| `app/services/audit.py` | Makes sure every change gets logged, with no exceptions |
| `app/routers/cases.py` | The upload endpoint — this is what runs when someone uploads a judgment |
| `app/routers/verification.py` | The approve/edit/reject endpoints — this is what runs when an officer reviews a directive |
| `app/routers/actions.py` | Tracks approved actions and powers the dashboard numbers |
| `app/main.py` | The file that starts the whole server |
| `seed.py` | Fills in the default list of government departments |
| `.env.example` | Template for your secret keys — copy it to `.env` and fill in real values |

## How to try it once it's running

Once the server is running, open **http://localhost:8000/docs** in your browser.
This is an auto-generated page where you can literally click "Try it out" on any
endpoint — including uploading a real PDF judgment — without writing any code at all.
It's the best way to confirm the AI extraction actually works on a real document
before connecting the React frontend to it.

## Connecting this to the prototype you already saw

The React prototype from earlier used pretend data. The next step after this backend
is running is to swap those pretend function calls for real ones that hit this API
(`http://localhost:8000/api/v1/...`). I can do that swap for you once you confirm this
backend is up and a test upload works — just tell me and paste back what you see at
`/docs`.

## If something doesn't work

Copy the exact error message and paste it back to me (or to Claude Code) — these
setup errors are almost always one missing thing (Postgres not running, wrong API
key, a package that needs installing) and are quick to fix once we see the message.
