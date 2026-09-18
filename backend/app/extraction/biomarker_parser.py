import re


# Matches lines like: "Hemoglobin: 10.2 g/dL (Normal: 13.0-17.0)"
BIOMARKER_PATTERN = re.compile(
    r"([A-Za-z][A-Za-z0-9 /\-]*?):\s*"        # name (before colon)
    r"([\d.]+)\s*"                             # value
    r"([a-zA-Z/^0-9]+)?\s*"                    # unit (optional)
    r"\(?\s*Normal:\s*([\d.]+)\s*-\s*([\d.]+)\)?"  # ref range
)


def determine_status(value: float, ref_low: float, ref_high: float) -> str:
    if value < ref_low:
        return "LOW"
    elif value > ref_high:
        return "HIGH"
    return "NORMAL"


def parse_biomarkers(text: str) -> list[dict]:
    """
    Parse raw extracted report text into a list of structured biomarker dicts.
    Each dict: {name, value, unit, ref_low, ref_high, status}
    """
    results = []
    for match in BIOMARKER_PATTERN.finditer(text):
        name = match.group(1).strip()
        value = float(match.group(2))
        unit = (match.group(3) or "").strip()
        ref_low = float(match.group(4))
        ref_high = float(match.group(5))
        status = determine_status(value, ref_low, ref_high)

        results.append({
            "name": name,
            "value": value,
            "unit": unit,
            "ref_low": ref_low,
            "ref_high": ref_high,
            "status": status,
        })
    return results