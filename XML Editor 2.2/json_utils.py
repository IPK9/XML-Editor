def parse_typed_value(raw_value, value_type):
    text = "" if raw_value is None else str(raw_value)
    t = (value_type or "auto").lower()

    if t == "null":
        return None
    if t == "string":
        return text
    if t == "int":
        try:
            return int(text)
        except Exception:
            return 0
    if t == "float":
        try:
            return float(text)
        except Exception:
            return 0.0
    if t == "bool":
        return text.strip().lower() in ("1", "true", "yes", "on")

    lowered = text.strip().lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "none"):
        return None

    try:
        return int(text)
    except Exception:
        pass

    try:
        return float(text)
    except Exception:
        pass

    return text


def typed_value_to_xml_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def guess_json_type_from_value(value):
    lowered = str(value).strip().lower()

    if lowered in ("true", "false"):
        return "bool"
    if lowered in ("null", "none", ""):
        return "string" if lowered == "" else "null"

    try:
        int(str(value))
        return "int"
    except Exception:
        pass

    try:
        float(str(value))
        return "float"
    except Exception:
        pass

    return "string"
