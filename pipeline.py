import os
import pandas as pd

CSV_INPUT = "ICP-Saas-EU-Default-view-export-1780568201117.csv"
CSV_OUTPUT = "qualified_leads.csv"
MAX_ROWS = 40

TITLE_HIGH = ["cro", "chief revenue officer", "vp sales", "head of sales"]
TITLE_MEDIUM = ["sales director", "head of revops", "sales operations"]
COFOUNDER_REVENUE = ["revenue", "cro", "sales", "commercial"]

STACK_HIGH_TOOLS = ["salesforce", "salesloft", "gong", "outreach"]
STACK_MEDIUM_TOOLS = ["hubspot", "apollo", "clari"]
TOOL_DISPLAY = {
    "salesforce": "Salesforce",
    "salesloft": "Salesloft",
    "gong": "Gong",
    "outreach": "Outreach",
    "hubspot": "HubSpot",
    "apollo": "Apollo",
    "clari": "Clari",
}


def score_title(title):
    if not isinstance(title, str) or not title.strip():
        return "Low"
    t = title.lower()
    for kw in TITLE_HIGH:
        if kw in t:
            return "High"
    for kw in TITLE_MEDIUM:
        if kw in t:
            return "Medium"
    if "co-founder" in t or "cofounder" in t:
        for kw in COFOUNDER_REVENUE:
            if kw in t:
                return "Medium"
    return "Low"


def score_stack(tech_str):
    if not isinstance(tech_str, str) or not tech_str.strip():
        return "Low", []
    t = tech_str.lower()
    found_high = [TOOL_DISPLAY[tool] for tool in STACK_HIGH_TOOLS if tool in t]
    if found_high:
        return "High", found_high[:2]
    found_medium = [TOOL_DISPLAY[tool] for tool in STACK_MEDIUM_TOOLS if tool in t]
    if found_medium:
        return "Medium", found_medium[:2]
    return "Low", []


def score_headcount(count_val):
    try:
        n = int(float(str(count_val).strip().replace(",", "")))
    except (ValueError, TypeError):
        return "Low"
    if 51 <= n <= 200:
        return "High"
    if 201 <= n <= 500:
        return "Medium"
    return "Low"


def final_score(title_s, stack_s, head_s):
    scores = [title_s, stack_s, head_s]
    highs = scores.count("High")
    mediums = scores.count("Medium")
    if highs >= 2:
        return "High"
    if highs == 1 and mediums >= 1:
        return "Medium"
    return "Low"


def build_outreach_angle(row, icp_score, tools):
    company = str(row.get("Company Name", "")).strip() or "the company"
    title = str(row.get("Job Title", "")).strip() or "this contact"
    headcount_raw = str(row.get("Employee Count", "")).strip()

    try:
        hc = int(float(headcount_raw.replace(",", "")))
        hc_str = str(hc)
    except (ValueError, TypeError):
        hc_str = None

    tool_str = " + ".join(tools) if tools else None

    if icp_score == "High":
        if tool_str and hc_str:
            return (
                f"{tool_str} stack at {company} ({hc_str}-person team) with a {title} in seat"
                f" signals active revenue build-out — strong fit for outreach."
            )
        elif tool_str:
            return (
                f"{tool_str} stack at {company} with a {title} signals active revenue"
                f" infrastructure investment — strong fit for outreach."
            )
        elif hc_str:
            return (
                f"{title} at {company} ({hc_str}-person team) — title and headcount signal"
                f" a well-resourced revenue org, strong fit for outreach."
            )
        else:
            return f"{title} at {company} — title seniority signals budget ownership, strong fit for outreach."

    elif icp_score == "Medium":
        if tool_str and hc_str:
            return (
                f"{title} at {company} ({hc_str} employees) running {tool_str}"
                f" — signals process maturity, worth a targeted approach."
            )
        elif tool_str:
            return (
                f"{title} at {company} running {tool_str}"
                f" — signals emerging revenue ops investment, worth a targeted approach."
            )
        elif hc_str:
            return (
                f"{title} at {company} ({hc_str} employees)"
                f" — headcount suggests a growing revenue team, worth a targeted approach."
            )
        else:
            return f"{title} at {company} — moderate signal fit, worth a targeted approach."

    else:
        return f"{title} at {company} — limited tech signal or headcount fit; lower priority."


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, CSV_INPUT)
    output_path = os.path.join(script_dir, CSV_OUTPUT)

    # Step 1: Load
    print(f"[1/5] Reading CSV...")
    df = pd.read_csv(input_path, dtype=str, nrows=MAX_ROWS)
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    print(f"       {len(df)} rows loaded (capped at {MAX_ROWS})")

    # Step 2: Filter
    print(f"[2/5] Filtering...")
    required_cols = ["Work Email", "First Name", "Job Title"]
    filter_reasons = []
    for _, row in df.iterrows():
        missing = [c for c in required_cols if not isinstance(row.get(c), str) or not row[c]]
        filter_reasons.append(f"Missing: {', '.join(missing)}" if missing else "")
    df["Filter_Reason"] = filter_reasons

    filtered_mask = df["Filter_Reason"] != ""
    n_filtered = int(filtered_mask.sum())
    if n_filtered:
        for _, row in df[filtered_mask].iterrows():
            name = str(row.get("Full Name", "")).strip() or "unknown"
            print(f"       FILTERED - {name}: {row['Filter_Reason']}")
    else:
        print(f"       No rows filtered out.")

    # Step 3: Score
    n_active = int((~filtered_mask).sum())
    print(f"[3/5] Scoring {n_active} contacts...")
    icp_scores, breakdowns = [], []

    # Step 4: Outreach angles
    print(f"[4/5] Generating outreach angles...")
    outreach_angles = []

    for _, row in df.iterrows():
        if row["Filter_Reason"]:
            icp_scores.append("Filtered")
            breakdowns.append("")
            outreach_angles.append("")
            continue

        title_s = score_title(row.get("Job Title", ""))
        stack_s, tools = score_stack(row.get("Technologiesfound", ""))
        head_s = score_headcount(row.get("Employee Count", ""))
        icp = final_score(title_s, stack_s, head_s)

        icp_scores.append(icp)
        breakdowns.append(f"Title: {title_s} | Stack: {stack_s} | Headcount: {head_s}")
        outreach_angles.append(build_outreach_angle(row, icp, tools))

    df["ICP_Score"] = icp_scores
    df["Score_Breakdown"] = breakdowns
    df["Outreach_Angle"] = outreach_angles

    # Step 5: Write output
    print(f"[5/5] Writing {CSV_OUTPUT}...")
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"       done. {len(df)} rows written.")

    scored = df[~filtered_mask]
    high = int((scored["ICP_Score"] == "High").sum())
    medium = int((scored["ICP_Score"] == "Medium").sum())
    low = int((scored["ICP_Score"] == "Low").sum())
    filtered = int((df["Filter_Reason"] != "").sum())
    print(f"\nSummary: {high} High | {medium} Medium | {low} Low | {filtered} Filtered")

    # Step 6: Send High/Medium contacts to n8n webhook
    import requests
    webhook_url = "https://tryouts.app.n8n.cloud/webhook/icp-pipeline"
    sent = 0
    failed = 0
    send_df = df[df["ICP_Score"].isin(["High", "Medium"])]
    for _, row in send_df.iterrows():
        payload = {
            "first_name": str(row.get("First Name", "")),
            "last_name": str(row.get("Last Name", "")),
            "email": str(row.get("Work Email", "")),
            "company_name": str(row.get("Company Name", "")),
            "job_title": str(row.get("Job Title", "")),
            "ICP_Score": str(row.get("ICP_Score", "")),
            "Score_Breakdown": str(row.get("Score_Breakdown", "")),
            "Outreach_Angle": str(row.get("Outreach_Angle", ""))
        }
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            sent += 1
        except Exception as e:
            print(f"Failed to send {row.get('First Name', '')}: {e}")
            failed += 1
    print(f"\nWebhook: {sent} contacts sent to n8n | {failed} failed")




if __name__ == "__main__":
    main()
