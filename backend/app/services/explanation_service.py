from google import genai

from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def explain_biomarker(name: str, value: float, unit: str, ref_low: float, ref_high: float, status: str) -> str:
    prompt = f"""You are a medical report explainer assistant. Explain the following lab result in 2-3 simple, plain-language sentences a non-medical person can understand. 

Biomarker: {name}
Value: {value} {unit}
Normal range: {ref_low} - {ref_high} {unit}
Status: {status}

Rules:
- Do NOT diagnose any condition.
- Do NOT give medical advice or treatment suggestions.
- End by gently suggesting the person discuss this with their healthcare provider if the value is LOW or HIGH.
- Keep it concise, 2-3 sentences maximum.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )
    return response.text.strip()


def summarize_report(biomarkers: list[dict]) -> str:
    biomarker_lines = "\n".join(
        f"- {b['name']}: {b['value']} {b['unit']} ({b['status']})" for b in biomarkers
    )

    prompt = f"""You are a medical report explainer assistant. Below are lab results from a patient's report.

{biomarker_lines}

Write a brief, plain-language overall summary (3-4 sentences) of these results for the patient. 

Rules:
- Do NOT diagnose any condition.
- Do NOT give medical advice or treatment suggestions.
- Mention which values are outside normal range, if any.
- End by recommending the person discuss these results with their healthcare provider.
- Keep it concise.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )
    return response.text.strip()


def summarize_trend(biomarker_name: str, history: list[dict]) -> str:
    history_lines = "\n".join(
        f"- {h['report_date']}: {h['value']} ({h['status']})" for h in history
    )

    prompt = f"""You are a medical report explainer assistant. Below is the history of a patient's {biomarker_name} values over multiple reports, ordered oldest to newest.

{history_lines}

Write a brief, plain-language summary (1-2 sentences) describing the trend — whether it's improving, worsening, or staying stable.

Rules:
- Do NOT diagnose any condition.
- Do NOT give medical advice.
- Keep it concise and factual about the trend direction.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )
    return response.text.strip()