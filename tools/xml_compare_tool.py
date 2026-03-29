import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET

from theme import (
    BG,
    PANEL_BG,
    CARD_BG,
    TEXT,
    MUTED,
    ACCENT,
    ENTRY_BG,
    BORDER,
    BUTTON_FG,
    HIGHLIGHT_ROW,
    FONT,
    FONT_BOLD,
    FONT_TITLE,
)

TOOL_ID = "xml_compare"
TOOL_NAME = "XML Comparison"
TOOL_ORDER = 10
TOOL_DESCRIPTION = "Compare two XML payloads and highlight structural or value differences."
SINGLE_INSTANCE = True


STATUS_SAME = "Same"
STATUS_CHANGED = "Changed"
STATUS_CHANGED_HEURISTIC = "Changed (Heuristic)"
STATUS_HEURISTIC_MATCH = "Heuristic Match"
STATUS_LEFT_ONLY = "Only in Left"
STATUS_RIGHT_ONLY = "Only in Right"


def launch(app):
    return XmlCompareToolWindow(app)


class XmlCompareToolWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("XML Comparison")
        self.window.geometry("1550x840")
        self.window.configure(bg=BG)

        self.left_xml_text = None
        self.right_xml_text = None
        self.left_source_name = None
        self.right_source_name = None
        self.compare_results = []

        self.left_path_var = tk.StringVar(value="Left XML: not loaded")
        self.right_path_var = tk.StringVar(value="Right XML: not loaded")
        self.summary_var = tk.StringVar(value="Load two XML files to begin.")
        self.filter_var = tk.StringVar(value="Differences only")
        self.ignore_whitespace_var = tk.BooleanVar(value=True)
        self.include_attributes_var = tk.BooleanVar(value=True)
        self.include_element_presence_var = tk.BooleanVar(value=True)
        self.heuristic_remap_var = tk.BooleanVar(value=True)

        self._build()

    def _build(self):
        self._configure_styles()

        header = tk.Frame(self.window, bg=BG)
        header.pack(fill="x", padx=12, pady=12)

        tk.Label(
            header,
            text="XML Comparison",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG,
        ).pack(side="left")

        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right")

        action_specs = [
            ("Use Current XML as Left", self.use_current_xml_as_left),
            ("Browse Left XML", self.browse_left_xml),
            ("Browse Right XML", self.browse_right_xml),
            ("Swap", self.swap_sources),
            ("Compare", self.compare_xmls),
        ]
        for index, (text, cmd) in enumerate(action_specs):
            tk.Button(
                actions,
                text=text,
                command=cmd,
                bg=ACCENT,
                fg=BUTTON_FG,
                relief="flat",
                padx=12,
                pady=6,
                font=FONT_BOLD,
            ).pack(side="left", padx=(0, 8 if index < len(action_specs) - 1 else 0))

        source_frame = tk.Frame(self.window, bg=BG)
        source_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(source_frame, textvariable=self.left_path_var, font=FONT, fg=MUTED, bg=BG, anchor="w").pack(fill="x")
        tk.Label(source_frame, textvariable=self.right_path_var, font=FONT, fg=MUTED, bg=BG, anchor="w").pack(fill="x", pady=(4, 0))

        options = tk.Frame(self.window, bg=BG)
        options.pack(fill="x", padx=12, pady=(0, 8))

        option_specs = [
            ("Ignore surrounding whitespace", self.ignore_whitespace_var),
            ("Compare attributes", self.include_attributes_var),
            ("Compare element presence", self.include_element_presence_var),
            ("Heuristic remapping", self.heuristic_remap_var),
        ]
        for text, variable in option_specs:
            tk.Checkbutton(
                options,
                text=text,
                variable=variable,
                bg=BG,
                fg=TEXT,
                activebackground=BG,
                activeforeground=TEXT,
                selectcolor=CARD_BG,
                font=FONT,
            ).pack(side="left", padx=(0, 12))

        tk.Label(options, text="View", font=FONT, fg=MUTED, bg=BG).pack(side="left", padx=(12, 8))

        filter_combo = ttk.Combobox(
            options,
            textvariable=self.filter_var,
            state="readonly",
            values=[
                "Differences only",
                "All results",
                "Changed only",
                "Heuristic only",
                "Only in Left",
                "Only in Right",
                "Same only",
            ],
            width=20,
            style="Dark.TCombobox",
        )
        filter_combo.pack(side="left")
        filter_combo.bind("<<ComboboxSelected>>", lambda _event: self._populate_results())

        summary_bar = tk.Frame(self.window, bg=PANEL_BG)
        summary_bar.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(
            summary_bar,
            textvariable=self.summary_var,
            font=FONT,
            fg=MUTED,
            bg=PANEL_BG,
            anchor="w",
            padx=10,
            pady=8,
        ).pack(fill="x")

        table_outer = tk.Frame(self.window, bg=BG)
        table_outer.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("status", "confidence", "left_path", "right_path", "left_value", "right_value")
        self.tree = ttk.Treeview(table_outer, columns=columns, show="headings", style="Compare.Treeview")
        self.tree.heading("status", text="Status")
        self.tree.heading("confidence", text="Confidence")
        self.tree.heading("left_path", text="Left Path")
        self.tree.heading("right_path", text="Right Path")
        self.tree.heading("left_value", text="Left Value")
        self.tree.heading("right_value", text="Right Value")

        self.tree.column("status", width=165, anchor="w")
        self.tree.column("confidence", width=95, anchor="center")
        self.tree.column("left_path", width=350, anchor="w")
        self.tree.column("right_path", width=350, anchor="w")
        self.tree.column("left_value", width=240, anchor="w")
        self.tree.column("right_value", width=240, anchor="w")

        y_scroll = ttk.Scrollbar(table_outer, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_outer, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        table_outer.grid_rowconfigure(0, weight=1)
        table_outer.grid_columnconfigure(0, weight=1)

    def _configure_styles(self):
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Dark.TCombobox", fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=TEXT)
        style.configure(
            "Compare.Treeview",
            background=ENTRY_BG,
            fieldbackground=ENTRY_BG,
            foreground=TEXT,
            bordercolor=BORDER,
            rowheight=26,
            font=FONT,
        )
        style.configure(
            "Compare.Treeview.Heading",
            background=CARD_BG,
            foreground=TEXT,
            relief="flat",
            font=FONT_BOLD,
        )
        style.map("Compare.Treeview", background=[("selected", HIGHLIGHT_ROW)], foreground=[("selected", TEXT)])

    def use_current_xml_as_left(self):
        xml_text = self.app.get_current_xml_text()
        if not xml_text:
            messagebox.showwarning("No XML", "Open an XML file in the editor first.")
            return

        self.left_xml_text = xml_text
        self.left_source_name = self.app.get_current_xml_display_name()
        self.left_path_var.set(f"Left XML: {self.left_source_name}")
        self.summary_var.set("Current XML loaded as left-hand comparison source.")

    def browse_left_xml(self):
        self._browse_xml(side="left")

    def browse_right_xml(self):
        self._browse_xml(side="right")

    def _browse_xml(self, side):
        file_path = filedialog.askopenfilename(
            title=f"Open {side.title()} XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                xml_text = handle.read()
        except Exception as exc:
            messagebox.showerror("Open error", f"Could not read XML file.\n\n{exc}")
            return

        if side == "left":
            self.left_xml_text = xml_text
            self.left_source_name = file_path
            self.left_path_var.set(f"Left XML: {file_path}")
        else:
            self.right_xml_text = xml_text
            self.right_source_name = file_path
            self.right_path_var.set(f"Right XML: {file_path}")

    def swap_sources(self):
        self.left_xml_text, self.right_xml_text = self.right_xml_text, self.left_xml_text
        self.left_source_name, self.right_source_name = self.right_source_name, self.left_source_name

        self.left_path_var.set(f"Left XML: {self.left_source_name or 'not loaded'}")
        self.right_path_var.set(f"Right XML: {self.right_source_name or 'not loaded'}")
        self.summary_var.set("Left and right XML sources swapped.")

    def compare_xmls(self):
        if not self.left_xml_text or not self.right_xml_text:
            messagebox.showwarning("Missing XML", "Load both left and right XML before comparing.")
            return

        try:
            left_root = ET.fromstring(self.left_xml_text)
            right_root = ET.fromstring(self.right_xml_text)
        except Exception as exc:
            messagebox.showerror("Parse error", f"One of the XML payloads could not be parsed.\n\n{exc}")
            return

        left_items = self._flatten_xml(left_root)
        right_items = self._flatten_xml(right_root)
        self.compare_results = self._build_compare_results(left_items, right_items)
        self._populate_results()

    def _clean_text(self, text):
        raw = "" if text is None else str(text)
        return raw.strip() if self.ignore_whitespace_var.get() else raw

    def _normalize_segment(self, segment):
        if "[" in segment:
            segment = segment.split("[", 1)[0]
        return segment

    def _path_segments(self, path):
        if not path:
            return []
        return [self._normalize_segment(part) for part in path.split("/") if part]

    def _flatten_xml(self, root):
        items = {}

        def add_item(path, value, item_type, owner_tag=None, leaf_name=None):
            segments = self._path_segments(path)
            parent_segments = segments[:-1]
            items[path] = {
                "path": path,
                "value": value,
                "item_type": item_type,
                "owner_tag": owner_tag or (segments[-1] if segments else ""),
                "leaf_name": leaf_name or (segments[-1] if segments else ""),
                "segments": segments,
                "parent_segments": parent_segments,
                "depth": len(segments),
            }

        def walk(element, current_path):
            if self.include_element_presence_var.get():
                add_item(current_path, f"<{element.tag}>", "element", owner_tag=element.tag, leaf_name=element.tag)

            text_value = self._clean_text(element.text)
            if text_value != "":
                add_item(
                    f"{current_path}/#text",
                    text_value,
                    "text",
                    owner_tag=element.tag,
                    leaf_name=element.tag,
                )

            if self.include_attributes_var.get():
                for attr_name, attr_value in sorted(element.attrib.items()):
                    add_item(
                        f"{current_path}/@{attr_name}",
                        self._clean_text(attr_value),
                        "attribute",
                        owner_tag=element.tag,
                        leaf_name=attr_name,
                    )

            tag_counts = {}
            for child in list(element):
                tag_counts[child.tag] = tag_counts.get(child.tag, 0) + 1
                child_path = f"{current_path}/{child.tag}[{tag_counts[child.tag]}]"
                walk(child, child_path)

        walk(root, f"/{root.tag}[1]")
        return items

    def _build_compare_results(self, left_items, right_items):
        results = []
        matched_left = set()
        matched_right = set()

        exact_paths = sorted(set(left_items.keys()) & set(right_items.keys()))
        for path in exact_paths:
            left_item = left_items[path]
            right_item = right_items[path]
            matched_left.add(path)
            matched_right.add(path)

            if left_item["value"] == right_item["value"]:
                status = STATUS_SAME
            else:
                status = STATUS_CHANGED

            results.append(
                {
                    "status": status,
                    "confidence": 1.0,
                    "left_path": path,
                    "right_path": path,
                    "left_value": left_item["value"],
                    "right_value": right_item["value"],
                }
            )

        if self.heuristic_remap_var.get():
            heuristic_matches = self._build_heuristic_matches(left_items, right_items, matched_left, matched_right)
            for left_path, right_path, score in heuristic_matches:
                left_item = left_items[left_path]
                right_item = right_items[right_path]
                matched_left.add(left_path)
                matched_right.add(right_path)

                if left_item["value"] == right_item["value"]:
                    status = STATUS_HEURISTIC_MATCH
                else:
                    status = STATUS_CHANGED_HEURISTIC

                results.append(
                    {
                        "status": status,
                        "confidence": round(score / 100.0, 2),
                        "left_path": left_path,
                        "right_path": right_path,
                        "left_value": left_item["value"],
                        "right_value": right_item["value"],
                    }
                )

        for path in sorted(set(left_items.keys()) - matched_left):
            left_item = left_items[path]
            results.append(
                {
                    "status": STATUS_LEFT_ONLY,
                    "confidence": 0.0,
                    "left_path": path,
                    "right_path": "",
                    "left_value": left_item["value"],
                    "right_value": "",
                }
            )

        for path in sorted(set(right_items.keys()) - matched_right):
            right_item = right_items[path]
            results.append(
                {
                    "status": STATUS_RIGHT_ONLY,
                    "confidence": 0.0,
                    "left_path": "",
                    "right_path": path,
                    "left_value": "",
                    "right_value": right_item["value"],
                }
            )

        return sorted(results, key=lambda item: (self._status_sort_key(item["status"]), item["left_path"] or item["right_path"]))

    def _build_heuristic_matches(self, left_items, right_items, matched_left, matched_right):
        candidates = []

        for left_path, left_item in left_items.items():
            if left_path in matched_left:
                continue
            for right_path, right_item in right_items.items():
                if right_path in matched_right:
                    continue
                score = self._score_pair(left_item, right_item)
                if score >= 55:
                    candidates.append((score, left_path, right_path))

        candidates.sort(key=lambda item: (-item[0], item[1], item[2]))

        chosen = []
        used_left = set()
        used_right = set()
        for score, left_path, right_path in candidates:
            if left_path in used_left or right_path in used_right:
                continue
            chosen.append((left_path, right_path, score))
            used_left.add(left_path)
            used_right.add(right_path)

        return chosen

    def _score_pair(self, left_item, right_item):
        if left_item["item_type"] != right_item["item_type"]:
            return 0

        score = 25
        if left_item["leaf_name"] == right_item["leaf_name"]:
            score += 35
        if left_item["owner_tag"] == right_item["owner_tag"]:
            score += 20

        left_parent = left_item["parent_segments"]
        right_parent = right_item["parent_segments"]
        left_parent_last = left_parent[-1] if left_parent else ""
        right_parent_last = right_parent[-1] if right_parent else ""
        if left_parent_last and left_parent_last == right_parent_last:
            score += 12

        left_segment_set = set(left_item["segments"])
        right_segment_set = set(right_item["segments"])
        if left_segment_set and right_segment_set:
            overlap = len(left_segment_set & right_segment_set)
            union = len(left_segment_set | right_segment_set)
            score += int((overlap / union) * 18)

        if left_item["value"] == right_item["value"]:
            score += 18

        depth_gap = abs(left_item["depth"] - right_item["depth"])
        score -= min(depth_gap * 3, 12)

        return max(score, 0)

    def _status_sort_key(self, status):
        order = {
            STATUS_CHANGED: 0,
            STATUS_CHANGED_HEURISTIC: 1,
            STATUS_HEURISTIC_MATCH: 2,
            STATUS_LEFT_ONLY: 3,
            STATUS_RIGHT_ONLY: 4,
            STATUS_SAME: 5,
        }
        return order.get(status, 99)

    def _populate_results(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        selected_filter = self.filter_var.get()
        visible = []
        for result in self.compare_results:
            status = result["status"]
            if selected_filter == "Differences only" and status == STATUS_SAME:
                continue
            if selected_filter == "Changed only" and status not in (STATUS_CHANGED, STATUS_CHANGED_HEURISTIC):
                continue
            if selected_filter == "Heuristic only" and status not in (STATUS_HEURISTIC_MATCH, STATUS_CHANGED_HEURISTIC):
                continue
            if selected_filter == "Only in Left" and status != STATUS_LEFT_ONLY:
                continue
            if selected_filter == "Only in Right" and status != STATUS_RIGHT_ONLY:
                continue
            if selected_filter == "Same only" and status != STATUS_SAME:
                continue
            visible.append(result)

        for result in visible:
            tags = ("difference",) if result["status"] != STATUS_SAME else ("same",)
            confidence_text = "" if result["confidence"] <= 0 else f"{int(result['confidence'] * 100)}%"
            self.tree.insert(
                "",
                "end",
                values=(
                    result["status"],
                    confidence_text,
                    result["left_path"],
                    result["right_path"],
                    self._shorten(result["left_value"]),
                    self._shorten(result["right_value"]),
                ),
                tags=tags,
            )

        self.tree.tag_configure("difference", background=HIGHLIGHT_ROW, foreground=TEXT)
        self.tree.tag_configure("same", background=ENTRY_BG, foreground=TEXT)

        changed_count = sum(1 for result in self.compare_results if result["status"] == STATUS_CHANGED)
        heuristic_changed_count = sum(1 for result in self.compare_results if result["status"] == STATUS_CHANGED_HEURISTIC)
        heuristic_match_count = sum(1 for result in self.compare_results if result["status"] == STATUS_HEURISTIC_MATCH)
        left_only_count = sum(1 for result in self.compare_results if result["status"] == STATUS_LEFT_ONLY)
        right_only_count = sum(1 for result in self.compare_results if result["status"] == STATUS_RIGHT_ONLY)
        same_count = sum(1 for result in self.compare_results if result["status"] == STATUS_SAME)

        self.summary_var.set(
            f"Showing {len(visible)} row(s). Changed: {changed_count} | Changed (Heuristic): {heuristic_changed_count} | "
            f"Heuristic Match: {heuristic_match_count} | Only in Left: {left_only_count} | "
            f"Only in Right: {right_only_count} | Same: {same_count}"
        )

    def _shorten(self, value, limit=120):
        text = "" if value is None else str(value).replace("\n", " ")
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."
