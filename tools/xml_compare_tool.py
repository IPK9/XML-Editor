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


def launch(app):
    return XmlCompareToolWindow(app)


class XmlCompareToolWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("XML Comparison")
        self.window.geometry("1450x820")
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

        tk.Checkbutton(
            options,
            text="Ignore surrounding whitespace",
            variable=self.ignore_whitespace_var,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=CARD_BG,
            font=FONT,
        ).pack(side="left", padx=(0, 12))

        tk.Checkbutton(
            options,
            text="Compare attributes",
            variable=self.include_attributes_var,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=CARD_BG,
            font=FONT,
        ).pack(side="left", padx=(0, 12))

        tk.Checkbutton(
            options,
            text="Compare element presence",
            variable=self.include_element_presence_var,
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
            values=["Differences only", "All results", "Changed only", "Only in Left", "Only in Right", "Same only"],
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

        columns = ("status", "left_path", "right_path", "left_value", "right_value")
        self.tree = ttk.Treeview(table_outer, columns=columns, show="headings", style="Compare.Treeview")
        self.tree.heading("status", text="Status")
        self.tree.heading("left_path", text="Left Path")
        self.tree.heading("right_path", text="Right Path")
        self.tree.heading("left_value", text="Left Value")
        self.tree.heading("right_value", text="Right Value")

        self.tree.column("status", width=120, anchor="w")
        self.tree.column("left_path", width=360, anchor="w")
        self.tree.column("right_path", width=360, anchor="w")
        self.tree.column("left_value", width=260, anchor="w")
        self.tree.column("right_value", width=260, anchor="w")

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

    def _flatten_xml(self, root):
        items = {}

        def add_item(path, value, item_type):
            items[path] = {
                "path": path,
                "value": value,
                "item_type": item_type,
            }

        def clean_text(text):
            raw = "" if text is None else str(text)
            return raw.strip() if self.ignore_whitespace_var.get() else raw

        def walk(element, parent_path):
            sibling_index = 1
            if parent_path:
                current_path = f"{parent_path}/{element.tag}[{sibling_index}]"
            else:
                current_path = f"/{element.tag}[1]"

            if self.include_element_presence_var.get():
                add_item(current_path, f"<{element.tag}>", "element")

            text_value = clean_text(element.text)
            if text_value != "":
                add_item(f"{current_path}/#text", text_value, "text")

            if self.include_attributes_var.get():
                for attr_name, attr_value in sorted(element.attrib.items()):
                    add_item(f"{current_path}/@{attr_name}", clean_text(attr_value), "attribute")

            tag_counts = {}
            for child in list(element):
                tag_counts[child.tag] = tag_counts.get(child.tag, 0) + 1
                child_path = f"{current_path}/{child.tag}[{tag_counts[child.tag]}]"
                walk_with_path(child, child_path)

        def walk_with_path(element, current_path):
            if self.include_element_presence_var.get():
                add_item(current_path, f"<{element.tag}>", "element")

            text_value = clean_text(element.text)
            if text_value != "":
                add_item(f"{current_path}/#text", text_value, "text")

            if self.include_attributes_var.get():
                for attr_name, attr_value in sorted(element.attrib.items()):
                    add_item(f"{current_path}/@{attr_name}", clean_text(attr_value), "attribute")

            tag_counts = {}
            for child in list(element):
                tag_counts[child.tag] = tag_counts.get(child.tag, 0) + 1
                child_path = f"{current_path}/{child.tag}[{tag_counts[child.tag]}]"
                walk_with_path(child, child_path)

        walk(root, "")
        return items

    def _build_compare_results(self, left_items, right_items):
        all_paths = sorted(set(left_items.keys()) | set(right_items.keys()))
        results = []

        for path in all_paths:
            left_item = left_items.get(path)
            right_item = right_items.get(path)

            if left_item is None:
                results.append(
                    {
                        "status": "Only in Right",
                        "left_path": "",
                        "right_path": path,
                        "left_value": "",
                        "right_value": right_item["value"],
                    }
                )
                continue

            if right_item is None:
                results.append(
                    {
                        "status": "Only in Left",
                        "left_path": path,
                        "right_path": "",
                        "left_value": left_item["value"],
                        "right_value": "",
                    }
                )
                continue

            if left_item["value"] == right_item["value"]:
                results.append(
                    {
                        "status": "Same",
                        "left_path": path,
                        "right_path": path,
                        "left_value": left_item["value"],
                        "right_value": right_item["value"],
                    }
                )
            else:
                results.append(
                    {
                        "status": "Changed",
                        "left_path": path,
                        "right_path": path,
                        "left_value": left_item["value"],
                        "right_value": right_item["value"],
                    }
                )

        return results

    def _populate_results(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        selected_filter = self.filter_var.get()
        visible = []
        for result in self.compare_results:
            if selected_filter == "Differences only" and result["status"] == "Same":
                continue
            if selected_filter == "Changed only" and result["status"] != "Changed":
                continue
            if selected_filter == "Only in Left" and result["status"] != "Only in Left":
                continue
            if selected_filter == "Only in Right" and result["status"] != "Only in Right":
                continue
            if selected_filter == "Same only" and result["status"] != "Same":
                continue
            visible.append(result)

        for result in visible:
            tags = ("difference",) if result["status"] != "Same" else ("same",)
            self.tree.insert(
                "",
                "end",
                values=(
                    result["status"],
                    result["left_path"],
                    result["right_path"],
                    self._shorten(result["left_value"]),
                    self._shorten(result["right_value"]),
                ),
                tags=tags,
            )

        self.tree.tag_configure("difference", background=HIGHLIGHT_ROW, foreground=TEXT)
        self.tree.tag_configure("same", background=ENTRY_BG, foreground=TEXT)

        changed_count = sum(1 for result in self.compare_results if result["status"] == "Changed")
        left_only_count = sum(1 for result in self.compare_results if result["status"] == "Only in Left")
        right_only_count = sum(1 for result in self.compare_results if result["status"] == "Only in Right")
        same_count = sum(1 for result in self.compare_results if result["status"] == "Same")

        self.summary_var.set(
            f"Showing {len(visible)} row(s). Changed: {changed_count} | Only in Left: {left_only_count} | "
            f"Only in Right: {right_only_count} | Same: {same_count}"
        )

    def _shorten(self, value, limit=120):
        text = "" if value is None else str(value).replace("\n", " ")
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."
