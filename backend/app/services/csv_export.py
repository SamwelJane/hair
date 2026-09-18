def to_csv(rows: list[dict[str, str | int | float]]) -> str:
    """Direct port of src/lib/analytics/csv.ts::toCsv. Headers come from the
    first row's keys - every row passed in must share the same key set."""
    if not rows:
        return ""

    headers = list(rows[0].keys())

    def escape(value: str | float) -> str:
        text = str(value)
        if any(ch in text for ch in ('"', ",", "\n")):
            return '"' + text.replace('"', '""') + '"'
        return text

    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(escape(row[h]) for h in headers))
    return "\n".join(lines)
