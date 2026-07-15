# TCF Discovery Agent

Stage 1 of the AI-powered career guidance system for TCF College.

This agent runs a structured self-assessment (RIASEC interests + lightweight Big Five personality + skills self-rating), detects contradictions in a student's own answers, and produces:

- A simple, jargon-free field-direction summary for the student
- A detailed report for the counsellor to use ahead of pre-work / interview sessions

Field-specific agents (Stage 2) plug in after this stage, once a direction has been identified.

Developed by Qarib Javed.

## Project structure

```
tcf-discovery-agent/
├── app.py                  Flask server + API routes
├── discovery_engine.py     Scoring, contradiction detection, report generation
├── requirements.txt
├── Procfile                 Render start command
├── render.yaml               Render blueprint (optional one-click deploy)
├── templates/index.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`.

## Deploy on Render

1. Push this repo to GitHub.
2. On Render: New → Web Service → connect the repo.
3. Render will detect `render.yaml` automatically (or set manually):
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. Deploy. Render gives you a public URL you can share with students for the pilot.

## Next steps (Stage 2)

- Add field-specific agents (Computer Science, Business, Engineering, etc.)
- Add a router that sends the student to the relevant field agent based on `suggested_fields`
- Add a counsellor-facing dashboard to view submitted reports (currently reports are returned inline, not persisted — add a database for the pilot if you want to store submissions)
