# SupportOps Copilot

An AI triage system for a software company's support team, built around a fictional product called Lumora Cloud. For each incoming ticket it sets the category and priority, spots angry customers, and either answers from a help-article knowledge base (naming the article it used) or escalates the ticket to a human with the reason.

**Live demo:** ADD-YOUR-RENDER-LINK-HERE (login required, runs in demo mode, may take about a minute to wake up)

## How it works

1. A ticket arrives from the web page or from a webhook.
2. The ticket is matched against the knowledge base. In Gemini mode this uses embeddings, so it matches by meaning. In demo mode it uses keywords and makes no Gemini requests.
3. Fixed rules always escalate security reports, refund and double-charge disputes, and legal threats, because a bot should not decide those.
4. If the best match is below a confidence cutoff, the bot does not guess. It escalates.
5. Every ticket and result is saved in SQLite and shown on the dashboard.

## Features

- Category and priority for every ticket, plus an angry-customer flag
- Answers only from the knowledge base, with the source article shown
- Escalation to a human with a stated reason
- Dashboard: tickets handled, auto-answer rate, and counts by category and priority
- Webhook endpoint with a secret token, so other tools can send tickets in
- Ticket history with CSV export
- Login for the page and its data
- Mock mode that uses no Gemini requests

## Evaluation

`eval.py` runs 28 hand-written tickets (16 that should be answered, 12 that should go to a human) and checks each result against the expected outcome.

| Mode | Routing correct | Category correct | Needed a human and got one | Wrongly auto-answered |
|---|---|---|---|---|
| Gemini | 28/28 | 26/26 | 12/12 | 0 |

This is a small test set written by the author, so treat it as a sanity check and not a benchmark.

## Project files

| File | Purpose |
|---|---|
| knowledge_base.json | The help articles |
| search.py | Finds the best matching article (Gemini embeddings or keyword mock) |
| triage.py | Category, priority, confidence and the answer-or-escalate decision |
| db.py | SQLite tables and queries |
| main.py | FastAPI app and endpoints |
| index.html | Web page and dashboard |
| eval.py | Test set and scores |

## Setup

1. Create and activate a virtual environment:

```
python -m venv venv
venv\Scripts\activate
```

2. Install the packages:

```
pip install -r requirements.txt
```

3. Create a file named `.env` in the project folder:

```
MOCK_MODE=true
GEMINI_API_KEY=your-gemini-api-key
APP_USER=admin
APP_PASSWORD=a-long-random-password
WEBHOOK_TOKEN=any-long-random-text
```

Never share `.env` or commit it. `.gitignore` already excludes it.

## Run

```
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 and sign in with the username and password from `.env`. Set `MOCK_MODE=false` and restart to use Gemini.

## Webhook

```
curl -X POST http://127.0.0.1:8000/webhook/ticket -H "Content-Type: application/json" -H "X-Webhook-Token: YOUR_TOKEN" -d "{\"text\": \"I was charged twice this month and I want a refund.\"}"
```

The reply is `201` with the triage result. A wrong token returns `401`, and a ticket under 10 or over 3000 characters returns `400`.

## Endpoints

- `GET /` web page (needs the login)
- `GET /status` current mode (needs the login)
- `GET /tickets` ticket history (needs the login)
- `GET /stats` dashboard numbers (needs the login)
- `GET /export.csv` download the history as CSV (needs the login)
- `POST /tickets` triage one ticket (needs the login)
- `POST /webhook/ticket` triage one ticket (needs the webhook token)

## Limits

- The knowledge base has 12 articles about a fictional product.
- Answers are the article text, not a rewritten reply.
- The keyword mock mode is only for demos and tests.