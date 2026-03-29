import xml.etree.ElementTree as ET


def normalize_config_paths(xml_root, raw_path: str) -> list[str]:
    path = raw_path.strip().replace("\\", "/")
    candidates: list[str] = []

    def add_candidate(candidate: str):
        candidate = candidate.strip()
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    add_candidate(path)

    root_tag = xml_root.tag if xml_root is not None else ""
    prefixes = [
        f".//{root_tag}/",
        f"./{root_tag}/",
        f"/{root_tag}/",
        f"{root_tag}/",
    ]

    for prefix in prefixes:
        if path.startswith(prefix):
            stripped = path[len(prefix):]
            add_candidate(f"./{stripped}")
            add_candidate(f".//{stripped}")

    if root_tag and path in (f".//{root_tag}", f"./{root_tag}", f"/{root_tag}", root_tag):
        add_candidate(".")

    if path.startswith("/"):
        add_candidate(f".{path}")

    return candidates


def group_children(children):
    groups = []
    seen = {}
    for child in children:
        if child.tag not in seen:
            seen[child.tag] = []
            groups.append((child.tag, seen[child.tag]))
        seen[child.tag].append(child)
    return groups


def build_child_path(parent, parent_path, target_child):
    index = 0
    for child in list(parent):
        if child.tag == target_child.tag:
            index += 1
        if child is target_child:
            return f"{parent_path}/{target_child.tag}[{index}]"
    return f"{parent_path}/{target_child.tag}[1]"


def matches_filter(name, value, path, filter_text):
    blob = f"{name} {value} {path}".lower()
    return filter_text in blob


def element_or_descendant_matches(element, path, filter_text):
    if filter_text == "":
        return True

    own_text = (element.text or "").strip()
    if matches_filter(element.tag, own_text, path, filter_text):
        return True

    for attr_name, attr_value in element.attrib.items():
        if matches_filter(attr_name, attr_value, path, filter_text):
            return True

    for child in element:
        child_path = build_child_path(element, path, child)
        if element_or_descendant_matches(child, child_path, filter_text):
            return True

    return False
