# Orbital Robotics Test Fixtures — Multi-Source RAG Project

All 11 files below describe the same fictional company, **Orbital Robotics Pvt Ltd**,
on purpose — so once you're querying across multiple sources in later layers, questions
like *"who approves parental leave, and what's the current backlog on the ticket about it"*
actually pull from two or three different file types and produce a coherent answer. That's
the real test of a multi-source system — unrelated PDFs won't exercise that.

## Layer 1 (use now)

| File | Use for |
|---|---|
| `orbital_leave_policy.pdf` | Your first `ingest.py` test — clean, text-based PDF |
| `falcon_onboarding_guide.pdf` | Second clean PDF — good for testing multiple-PDF ingestion |

## Layer 2+ (save for later phases)

| File | Tests |
|---|---|
| `skyline_invoice_scanned.pdf` | **OCR fallback** — this PDF has zero extractable text (image-only), confirmed with `pypdf`. Your text-extraction step should come back empty, triggering the `pytesseract` OCR path from Project 1's design. |
| `support_faq_clean.csv` | Clean CSV matching the `id, title, body` schema from Project 1's `ExpectedRowSchema` — should ingest with zero DLQ entries |
| `support_faq_dirty.csv` | **Schema drift** — has an extra column, two rows with missing `title`, and one fully empty row. Should produce exactly the number of DLQ entries you'd expect from validating against `ExpectedRowSchema` |
| `engineering_handbook.docx` | A Word source — you'll need a small `.docx` connector (use `python-docx` or `pandoc` in a Python subprocess) when you add this source type |
| `sprint14_retro_notes.docx` | Second `.docx` — deliberately references people/decisions that also appear in the CSVs and Slack export, for cross-source query testing |
| `support_tickets.xlsx` | A spreadsheet source (`pandas.read_excel` or `openpyxl`) — structured columns, no messy data, for your first spreadsheet connector |
| `falcon_slack_export.json` | Simulates a future API/Slack/Notion connector — a JSON payload with a `messages` array, each with `user`, `timestamp`, `text` |
| `employees_seed.sql` | Run this against a scratch Postgres DB/table to test a **SQL source connector** — `CREATE TABLE` + `INSERT` for an `employees` table |
| `company_overview.txt` | Plain-text baseline — simplest possible source, useful as a control case when debugging chunking logic |

## Suggested cross-source test queries (for once you have 3+ sources ingested)

- *"Who is the Falcon engineering lead, and what did the team decide about the on-call rotation?"* → pulls from `engineering_handbook.docx` + `sprint14_retro_notes.docx`
- *"What's the status of the ticket about the fleet-manager 500 error, and who's fixing it?"* → `support_tickets.xlsx`
- *"How much was the Skyline Parts invoice, and was it mentioned anywhere else?"* → `skyline_invoice_scanned.pdf` (via OCR) + `falcon_slack_export.json`
- *"Who approves parental leave requests?"* → `orbital_leave_policy.pdf`, cross-checkable against `employees_seed.sql` (Priya Nandakumar, Head of HR)
- Ask something **not covered anywhere** in these files (e.g., "what's Orbital Robotics' revenue?") to verify your system says it doesn't know rather than hallucinating — this is the grounding check from Day 8.
