"""Turns a report into pieces that can be stored and searched."""
from langchain_text_splitters import RecursiveCharacterTextSplitter

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def split_text(text: str | None) -> list[str]:
    """Split the raw text of a report into overlapping chunks."""
    text = (text or "").strip()
    if not text:
        return []
    return [c.strip() for c in _splitter.split_text(text) if c.strip()]


def biomarker_summary(report_name: str, report_date, biomarkers) -> str:
    """One readable block listing every biomarker of a report.

    Used both as a searchable chunk and as the always-included data for the
    report the user is currently looking at.
    """
    if not biomarkers:
        return f"Report '{report_name}' ({report_date}): no biomarkers were extracted."

    lines = [f"Biomarker results for report '{report_name}' dated {report_date}:"]
    for b in biomarkers:
        status = getattr(b.status, "value", b.status)
        unit = f" {b.unit}" if b.unit else ""
        lines.append(
            f"- {b.name}: {b.value}{unit} (normal range {b.ref_low}-{b.ref_high}) -> {status}"
        )
    return "\n".join(lines)
