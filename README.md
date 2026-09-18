# Public Promise — Week 1 Live Activity

A small real-time full-stack app for a founder residency's end-of-Week-1 "public promise" activity.
Founders scan a QR code, submit their name and one concrete goal for the coming week, and it
appears live on a projected screen as everyone submits.

Built with Python (FastAPI + native WebSockets + SQLite). No Node/npm required.

## The three URLs

Once deployed, your app has three distinct pages (replace `YOUR-APP` with your actual Render URL):

| Purpose | URL | Who opens it |
|---|---|---|
| **Submission form** | `https://YOUR-APP.onrender.com/` | Everyone, via QR code, on their phone |
| **Live display / projector** | `https://YOUR-APP.onrender.com/display` | You, on your laptop, full-screen on the projector |
| **QR code screen** | `https://YOUR-APP.onrender.com/qr` | You, to project/screenshot before the activity starts |
| **Admin / export** | `https://YOUR-APP.onrender.com/admin` | You, password-protected, to review promises afterward |
| Plain-text export | `https://YOUR-APP.onrender.com/export` | You, password-protected, for a copy/paste list |

The admin and export pages are protected with HTTP Basic Auth — your browser will prompt for a
username/password. Username is `admin` by default; the password is whatever you set as
`ADMIN_PASSWORD` (see below). **Set a real password before the event** — the code ships with a
placeholder default that is not secure.

## How it works

- `/` — mobile submission form: name/team name + the prompt question + a long-form text area.
  On submit, the browser gets a `Thank you` screen and the form is disabled via both a
  `localStorage` flag and an httpOnly cookie, so the same phone can't submit twice.
- `/display` — full-screen, high-contrast live feed. On load it fetches everything submitted so
  far (so a refresh never loses data), then opens a WebSocket and animates each new submission in
  one at a time (roomy hold time so people can read it), sliding older ones into a running feed
  below. Meant to run unattended on your laptop connected to the projector.
- `/qr` — a big QR code (auto-generated, always points at wherever the app is actually deployed)
  pointing at `/`.
- `/admin` and `/export` — everyone's name + promise, for Week 2 follow-up.
- Submissions persist in a SQLite file. On Render this file lives on a small persistent disk
  (configured in `render.yaml`) so a redeploy or restart mid-event does not lose data.
- Basic spam guard: an IP-based rate limit (8 requests/minute) on the submit endpoint, plus the
  cookie/localStorage one-submission-per-device check. No moderation queue — submissions appear
  live immediately, since this is a name-attached, in-person activity.

## Changing the question (or other text) later

The prompt text, event title, and admin credentials are environment variables, not hardcoded
strings — you can change them without touching code:

| Env var | What it controls | Default |
|---|---|---|
| `QUESTION_TEXT` | The prompt shown on the submit form and display screen | The "one concrete goal..." prompt from the brief |
| `EVENT_TITLE` | Heading shown on submit/display/QR/admin pages | `Founder Residency — Week 1` |
| `ADMIN_USERNAME` | Basic-auth username for `/admin` and `/export` | `admin` |
| `ADMIN_PASSWORD` | Basic-auth password for `/admin` and `/export` | `changeme` — **change this** |
| `DB_PATH` | Where the SQLite file lives | `/var/data/submissions.db` on Render |

To change one: open the Render dashboard → your service → **Environment** → edit the variable →
**Save Changes**. Render redeploys automatically; no code change or git push needed for these.

If you want to change layout, copy, colors, or animation timing, edit the files under
`app/templates/` and push to `main` — Render redeploys automatically on every push (see below).

## Local development

Requires Python 3.9+ (no Node/npm needed).

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
ADMIN_PASSWORD=localtest ./.venv/bin/uvicorn app.main:app --reload --port 8000
```

Then visit `http://127.0.0.1:8000/` (submit), `http://127.0.0.1:8000/display` (live feed), and
`http://127.0.0.1:8000/qr` (QR code). Locally the SQLite file is created at `./data/submissions.db`
(gitignored).

## Deploying to Render

This repo includes a `render.yaml` Blueprint, so Render can configure everything (web service,
Python build/start commands, and the persistent disk for SQLite) automatically.

1. Push this repo to GitHub (already done if you're reading this from the repo).
2. Go to the [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**.
3. Connect your GitHub account (first time only) and select this repo.
4. Render reads `render.yaml` and proposes one service: `public-promise-week1` on the **Starter**
   plan with a 1 GB persistent disk (needed so SQLite survives restarts — the free plan's disk is
   ephemeral). Click **Apply**.
5. Once it deploys, open the service → **Environment** and set `ADMIN_PASSWORD` to something only
   you know (it's intentionally left blank in `render.yaml` so it's never committed to git).
6. Your live URL will be `https://public-promise-week1-<random>.onrender.com` (or a name you
   choose during setup). Visit `/qr` on that URL to get your scannable code, `/` is what it points
   to, and `/display` is what you project.

**Cold start note:** Render's Starter plan does not spin down between requests, so the app stays
warm and responsive throughout your 30–45 minute window. Avoid the free plan for this event — it
sleeps after inactivity and the first request after sleep can take ~30–60 seconds, which will
confuse people scanning the QR code.

**Single instance only:** Do not turn on autoscaling / multiple instances. Both the WebSocket
broadcast and the SQLite file assume one running process; scaling to multiple instances would
split live viewers and writes across processes.

### Redeploying after a code change

Any `git push` to the branch Render is watching triggers an automatic redeploy. No manual steps
needed. Submissions already in the database are preserved across the redeploy because they live
on the persistent disk, not in the app's ephemeral filesystem.

## Before the event: pre-flight checklist

- [ ] Set `ADMIN_PASSWORD` in Render to a real password.
- [ ] Open `/qr` on your laptop, project it, and do a real test scan + submission from your own
      phone on cellular data (not just the venue Wi-Fi) to confirm the live URL works outside
      localhost.
- [ ] Open `/display` on the laptop that's connected to the projector and leave it open.
- [ ] Do one test submission from a phone and confirm it appears on `/display` within a few
      seconds, then check `/admin` shows it too.
- [ ] Bump your browser zoom out on the projector laptop if the room is large, since `/display`
      already scales with viewport width but a bit of extra zoom-out helps very large rooms.

## Tech stack

- **Backend:** FastAPI (Python), native WebSockets for real-time push — no separate real-time
  service needed.
- **Storage:** SQLite file on a Render persistent disk.
- **Frontend:** Plain HTML/CSS/JS (no build step, no framework) rendered via Jinja2 templates.
- **Hosting:** Render (Blueprint-based, auto-deploys on push to GitHub).
