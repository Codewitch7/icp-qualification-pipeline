# icp-qualification-pipeline
Automated GTM lead scoring pipeline — filters, scores, and pushes qualified contacts to HubSpot via n8n
# ICP Qualification & Signal Scoring Pipeline

A GTM intelligence pipeline built with Claude Code, Python, n8n, and HubSpot.

## What it does

- Reads a raw Apollo/Clay CSV export
- Filters out contacts missing email, name, or job title
- Scores each contact High, Medium, or Low across three signals:
  - Job title (CRO, VP Sales, Head of Sales = High)
  - Tech stack (Salesforce, Gong, Salesloft = High stack signal)
  - Headcount (51-200 employees = High growth stage)
- Generates a personalised outreach angle per contact based on their actual signals
- Pushes all High and Medium contacts to HubSpot via n8n webhook automatically

## Output

A clean CSV with four new columns added to the original data:
- ICP_Score (High / Medium / Low / Filtered)
- Score_Breakdown (Title: High | Stack: High | Headcount: Medium)
- Outreach_Angle (one sentence per contact explaining the score)
- Filter_Reason (why a contact was removed if applicable)

## How to run

1. Drop your Apollo or Clay CSV export into the project folder
2. Update the CSV filename in pipeline.py
3. Run: python pipeline.py
4. Check qualified_leads.csv for output
5. Qualified contacts are automatically pushed to HubSpot via n8n webhook

## Tech stack

- Python + pandas
- Claude Code
- n8n (webhook automation)
- HubSpot CRM API

## Built by

Rebecca Akparanta — GTM Engineer
Portfolio: rebeccaakparanta.vercel.app
