import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from theme import (
    BG,
    CARD_BG,
    TEXT,
    MUTED,
    ACCENT,
    ENTRY_BG,
    BORDER,
    BUTTON_FG,
    FONT,
    FONT_BOLD,
    FONT_TITLE,
    JSON_TYPES,
)
from json_utils import parse_typed_value, guess_json_type_from_value


class JsonEditorWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("JSON Editor")
        self.window.geometry("1100x720")
        self.window.configure(bg=BG)

        self.rows = []
        self.selected_row = None
        self.status_var = tk.StringVar(value="Select a row here, then click a field in the XML editor.")
        self.recent_config_var = tk.StringVar()

        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure("Dark.TCombobox", fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=TEXT)

        self._build()
        self.refresh_rows()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    def _build(self):
        header = tk.Frame(self.window, bg=BG)
        header.pack(fill="x", padx=12, pady=12)

        tk.Label(
            header,
            text="JSON Editor",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG,
        ).pack(side="left")

        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right")

        button_specs = [
            ("Load JSON", self.load_json),
            ("Save JSON", self.save_json),
            ("Save JSON As", self.save_json_as),
            ("New Element", self.add_row),
            ("Delete Element", self.delete_selected_row),
        ]
        for index, (text, cmd) in enumerate(button_specs):
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
            ).pack(side="left", padx=(0, 8 if index < len(button_specs) - 1 else 0))

        preset_bar = tk.Frame(self.window, bg=BG)
        preset_bar.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(
            preset_bar,
            text="Recent configs",
            font=FONT,
            fg=MUTED,
            bg=BG,
        ).pack(side="left", padx=(0, 8))

        self.recent_combo = ttk.Combobox(
            preset_bar,
            textvariable=self.recent_config_var,
            state="readonly",
            width=70,
            style="Dark.TCombobox",
        )
        self.recent_combo.pack(side="left", padx=(0, 8))

        tk.Button(
            preset_bar,
            text="Load Recent",
            command=self.load_recent,
            bg=ACCENT,
            fg=BUTTON_FG,
            relief="flat",
            padx=12,
            pady=6,
            font=FONT_BOLD,
        ).pack(side="left")

        tools = tk.Frame(self.window, bg=BG)
        tools.pack(fill="x", padx=12, pady=(0, 8))

        tool_specs = [
            ("Use Selected XML Path", self.use_selected_xml_path),
            ("Pull XML Value", self.pull_selected_xml_value),
        ]
        for index, (text, cmd) in enumerate(tool_specs):
            tk.Button(
                tools,
                text=text,
                command=cmd,
                bg=ACCENT,
                fg=BUTTON_FG,
                relief="flat",
                padx=12,
                pady=6,
                font=FONT_BOLD,
            ).pack(side="left", padx=(0, 8 if index < len(tool_specs) - 1 else 0))

        tk.Label(
            self.window,
            textvariable=self.status_var,
            font=FONT,
            fg=MUTED,
            bg=BG,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 8))

        outer = tk.Frame(self.window, bg=BG)
        outer.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        self.scroll = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.rows_frame = tk.Frame(self.canvas, bg=BG)
        self.rows_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )
        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

    def _refresh_recent_combo(self):
        self.recent_combo["values"] = self.app.recent_config_paths
        if self.app.loaded_config_path:
            self.recent_config_var.set(self.app.loaded_config_path)

    def set_status(self, text):
        self.status_var.set(text)

    def refresh_rows(self):
        for widget in self.rows_frame.winfo_children():
            widget.destroy()

        self.rows.clear()
        self.selected_row = None

        replacements = self.app.loaded_config.get("replacements", [])
        if not replacements:
            self.add_row(rule=None, refresh_status=False)
        else:
            for rule in replacements:
                if isinstance(rule, dict):
                    self.add_row(rule=rule, refresh_status=False)

        self._refresh_recent_combo()
        self.set_status("Select a row, then click a field in the XML editor if you want its path or value.")

    def add_row(self, rule=None, refresh_status=True):
        if rule is None:
            rule = {}

        row_frame = tk.Frame(
            self.rows_frame,
            bg=CARD_BG,
            bd=1,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        row_frame.pack(fill="x", padx=8, pady=6)

        header = tk.Label(
            row_frame,
            text=f"Replacement #{len(self.rows) + 1}",
            font=FONT_BOLD,
            fg=TEXT,
            bg=CARD_BG,
            anchor="w",
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        path_var = tk.StringVar(value=rule.get("path", ""))
        attr_var = tk.StringVar(value=rule.get("attribute", ""))
        type_var = tk.StringVar(value=(rule.get("type") or "auto"))
        value_var = tk.StringVar(value="" if rule.get("value") is None else str(rule.get("value")))
        match_var = tk.StringVar(value="Matches: 0")

        self._make_field(row_frame, 1, "Path", path_var)
        self._make_field(row_frame, 2, "Attribute", attr_var)
        self._make_type_field(row_frame, 3, "Type", type_var)
        self._make_field(row_frame, 4, "Value", value_var)

        tk.Label(
            row_frame,
            textvariable=match_var,
            font=FONT,
            fg=ACCENT,
            bg=CARD_BG,
            anchor="w",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        row_frame.grid_columnconfigure(1, weight=1)

        row_data = {
            "frame": row_frame,
            "header": header,
            "path_var": path_var,
            "attr_var": attr_var,
            "type_var": type_var,
            "value_var": value_var,
            "match_var": match_var,
        }
        self.rows.append(row_data)

        self._bind_selection(row_frame, row_data)
        self._bind_selection(header, row_data)
        self.select_row(row_data)

        if refresh_status:
            self.set_status("New JSON replacement row added.")

    def _make_field(self, parent, row, label_text, var):
        tk.Label(
            parent,
            text=label_text,
            font=FONT,
            fg=MUTED,
            bg=CARD_BG,
            anchor="w",
            width=12,
        ).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=4)

        tk.Entry(
            parent,
            textvariable=var,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
        ).grid(row=row, column=1, sticky="ew", pady=4, ipady=4)

    def _make_type_field(self, parent, row, label_text, var):
        tk.Label(
            parent,
            text=label_text,
            font=FONT,
            fg=MUTED,
            bg=CARD_BG,
            anchor="w",
            width=12,
        ).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=4)

        ttk.Combobox(
            parent,
            textvariable=var,
            values=JSON_TYPES,
            state="readonly",
            width=18,
        ).grid(row=row, column=1, sticky="w", pady=4)

    def _bind_selection(self, widget, row_data):
        widget.bind("<Button-1>", lambda event, r=row_data: self.select_row(r))

    def select_row(self, row_data):
        self.selected_row = row_data
        self.app.selected_json_rule = row_data

        for item in self.rows:
            selected = item is row_data
            item["frame"].configure(
                highlightbackground=ACCENT if selected else BORDER,
                highlightthickness=2 if selected else 1,
            )

        self.app.highlight_matches_for_json_row(row_data)

    def delete_selected_row(self):
        if self.selected_row is None:
            messagebox.showwarning("No row", "Select a JSON row first.")
            return

        row = self.selected_row
        row["frame"].destroy()
        self.rows = [item for item in self.rows if item is not row]
        self.selected_row = None
        self.app.selected_json_rule = None

        for index, item in enumerate(self.rows, start=1):
            item["header"].configure(text=f"Replacement #{index}")

        if not self.rows:
            self.add_row(rule=None, refresh_status=False)

        self.app.reset_xml_match_highlights()
        self.set_status("Selected JSON row deleted.")

    def use_selected_xml_path(self):
        if self.selected_row is None:
            messagebox.showwarning("No row", "Select a JSON row in the JSON editor first.")
            return
        if self.app.selected_xml_target is None:
            messagebox.showwarning("No XML selection", "Click a field in the XML editor first.")
            return

        self.selected_row["path_var"].set(self.app.selected_xml_target["path"])
        self.selected_row["attr_var"].set(self.app.selected_xml_target.get("attribute") or "")
        self.set_status(f"Inserted XML path: {self.app.selected_xml_target['path']}")
        self.app.highlight_matches_for_json_row(self.selected_row)

    def pull_selected_xml_value(self):
        if self.selected_row is None:
            messagebox.showwarning("No row", "Select a JSON row in the JSON editor first.")
            return
        if self.app.selected_xml_target is None:
            messagebox.showwarning("No XML selection", "Click a field in the XML editor first.")
            return

        self.selected_row["path_var"].set(self.app.selected_xml_target["path"])
        self.selected_row["attr_var"].set(self.app.selected_xml_target.get("attribute") or "")
        self.selected_row["value_var"].set(self.app.selected_xml_target.get("value", ""))
        self.selected_row["type_var"].set(guess_json_type_from_value(self.app.selected_xml_target.get("value", "")))
        self.set_status(f"Pulled XML path and value from: {self.app.selected_xml_target['path']}")
        self.app.highlight_matches_for_json_row(self.selected_row)

    def push_rows_to_config(self):
        replacements = []
        for row in self.rows:
            path = row["path_var"].get().strip()
            attribute = row["attr_var"].get().strip()
            value_text = row["value_var"].get()
            value_type = (row["type_var"].get() or "auto").strip().lower()

            if not path:
                continue

            parsed_value = parse_typed_value(value_text, value_type)
            rule = {
                "path": path,
                "type": value_type,
                "value": parsed_value,
            }
            if attribute:
                rule["attribute"] = attribute
            replacements.append(rule)

        self.app.loaded_config = {"replacements": replacements}

    def load_json(self):
        self.app.load_config()
        self.refresh_rows()

    def load_recent(self):
        selected = self.recent_config_var.get().strip()
        if not selected:
            return
        if self.app._load_config_from_path(selected):
            self.refresh_rows()

    def save_json(self):
        self.push_rows_to_config()
        if not self.app.loaded_config_path:
            self.save_json_as()
            return
        self.app._save_json_to_path(self.app.loaded_config_path)
        self._refresh_recent_combo()

    def save_json_as(self):
        self.push_rows_to_config()
        file_path = filedialog.asksaveasfilename(
            title="Save JSON Config As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        self.app.loaded_config_path = file_path
        self.app._remember_recent_config(file_path)
        self.app._save_json_to_path(file_path)
        self._refresh_recent_combo()
