import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml.etree.ElementTree as ET

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
from json_utils import parse_typed_value, typed_value_to_xml_text
from xml_utils import normalize_config_paths

TOOL_ID = "xml_generator"
TOOL_NAME = "XML Generator"
TOOL_ORDER = 20
TOOL_DESCRIPTION = "Create reusable XML generator templates from existing XML files."
SINGLE_INSTANCE = True


class XmlGeneratorToolWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("XML Generator")
        self.window.geometry("1280x780")
        self.window.configure(bg=BG)

        self.generator_data = {
            "generator_name": "",
            "source_xml_path": "",
            "xml_snapshot": "",
            "fields": [],
        }
        self.generator_path = None
        self.recent_generator_paths = []
        self.filtered_indices = []
        self.selected_field_index = None
        self.updating_editor = False

        self.source_xml_var = tk.StringVar(value="Source XML: not loaded")
        self.generator_var = tk.StringVar(value="Generator file: not saved")
        self.status_var = tk.StringVar(value="Load XML to build a generator.")
        self.generator_name_var = tk.StringVar(value="")
        self.recent_generator_var = tk.StringVar(value="")
        self.search_var = tk.StringVar(value="")

        self.label_var = tk.StringVar(value="")
        self.path_var = tk.StringVar(value="")
        self.attr_var = tk.StringVar(value="")
        self.type_var = tk.StringVar(value="string")
        self.value_var = tk.StringVar(value="")

        self.search_var.trace_add("write", self.refresh_rows)

        self._configure_styles()
        self._build()
        self.refresh_rows()

    def _configure_styles(self):
        style = ttk.Style(self.window)
        style.theme_use("clam")
        style.configure(
            "Dark.Treeview",
            background=ENTRY_BG,
            foreground=TEXT,
            fieldbackground=ENTRY_BG,
            bordercolor=BORDER,
            rowheight=24,
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=CARD_BG,
            foreground=TEXT,
            relief="flat",
        )
        style.map(
            "Dark.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", BUTTON_FG)],
        )
        style.configure("Dark.TCombobox", fieldbackground=ENTRY_BG, background=ENTRY_BG, foreground=TEXT)

    def _build(self):
        header = tk.Frame(self.window, bg=BG)
        header.pack(fill="x", padx=12, pady=12)

        tk.Label(header, text="XML Generator", font=FONT_TITLE, fg=TEXT, bg=BG).pack(side="left")

        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right")

        button_specs = [
            ("Use Current XML", self.use_current_xml),
            ("Browse XML", self.browse_xml),
            ("Load Generator", self.load_generator),
            ("Save Generator", self.save_generator),
            ("Save Generator As", self.save_generator_as),
            ("Generate XML", self.generate_xml),
            ("Generate XML As", self.generate_xml_as),
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

        meta = tk.Frame(self.window, bg=BG)
        meta.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(meta, text="Generator Name", font=FONT, fg=MUTED, bg=BG).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        tk.Entry(
            meta,
            textvariable=self.generator_name_var,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
        ).grid(row=0, column=1, sticky="ew", pady=(0, 6), ipady=4)

        tk.Label(meta, text="Search Fields", font=FONT, fg=MUTED, bg=BG).grid(row=0, column=2, sticky="w", padx=(12, 8), pady=(0, 6))
        tk.Entry(
            meta,
            textvariable=self.search_var,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
        ).grid(row=0, column=3, sticky="ew", pady=(0, 6), ipady=4)

        tk.Label(meta, textvariable=self.source_xml_var, font=FONT, fg=MUTED, bg=BG, anchor="w").grid(row=1, column=0, columnspan=4, sticky="ew", pady=(2, 0))
        tk.Label(meta, textvariable=self.generator_var, font=FONT, fg=MUTED, bg=BG, anchor="w").grid(row=2, column=0, columnspan=4, sticky="ew", pady=(4, 0))

        meta.grid_columnconfigure(1, weight=1)
        meta.grid_columnconfigure(3, weight=1)

        recent_bar = tk.Frame(self.window, bg=BG)
        recent_bar.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(recent_bar, text="Recent Generators", font=FONT, fg=MUTED, bg=BG).pack(side="left", padx=(0, 8))
        self.recent_combo = ttk.Combobox(
            recent_bar,
            textvariable=self.recent_generator_var,
            state="readonly",
            width=70,
            style="Dark.TCombobox",
        )
        self.recent_combo.pack(side="left", padx=(0, 8))
        tk.Button(
            recent_bar,
            text="Load Recent",
            command=self.load_recent_generator,
            bg=ACCENT,
            fg=BUTTON_FG,
            relief="flat",
            padx=12,
            pady=6,
            font=FONT_BOLD,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            recent_bar,
            text="Add From Current XML Selection",
            command=self.add_from_current_selection,
            bg=ACCENT,
            fg=BUTTON_FG,
            relief="flat",
            padx=12,
            pady=6,
            font=FONT_BOLD,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            recent_bar,
            text="Add Blank Field",
            command=self.add_blank_field,
            bg=ACCENT,
            fg=BUTTON_FG,
            relief="flat",
            padx=12,
            pady=6,
            font=FONT_BOLD,
        ).pack(side="left")

        tk.Label(
            self.window,
            textvariable=self.status_var,
            font=FONT,
            fg=MUTED,
            bg=BG,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 8))

        body = tk.Frame(self.window, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        tree_container = tk.Frame(left, bg=CARD_BG, bd=1, highlightbackground=BORDER, highlightthickness=1)
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        columns = ("label", "path", "attribute", "type", "value")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", style="Dark.Treeview")
        headings = {
            "label": "Label",
            "path": "Path",
            "attribute": "Attribute",
            "type": "Type",
            "value": "Value",
        }
        widths = {
            "label": 180,
            "path": 360,
            "attribute": 100,
            "type": 80,
            "value": 260,
        }
        for name in columns:
            self.tree.heading(name, text=headings[name])
            self.tree.column(name, width=widths[name], anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        tree_scroll_y = tk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll_y.set)

        tree_scroll_x = tk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=tree_scroll_x.set)

        right = tk.Frame(body, bg=CARD_BG, bd=1, highlightbackground=BORDER, highlightthickness=1, padx=12, pady=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(1, weight=1)

        tk.Label(right, text="Selected Field", font=FONT_BOLD, fg=TEXT, bg=CARD_BG, anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._make_editor_field(right, 1, "Label", self.label_var)
        self._make_editor_field(right, 2, "Path", self.path_var)
        self._make_editor_field(right, 3, "Attribute", self.attr_var)

        tk.Label(right, text="Type", font=FONT, fg=MUTED, bg=CARD_BG, anchor="w", width=12).grid(row=4, column=0, sticky="nw", padx=(0, 10), pady=4)
        self.type_combo = ttk.Combobox(
            right,
            textvariable=self.type_var,
            values=JSON_TYPES,
            state="readonly",
            width=16,
            style="Dark.TCombobox",
        )
        self.type_combo.grid(row=4, column=1, sticky="w", pady=4)

        self._make_editor_field(right, 5, "Value", self.value_var)

        editor_actions = tk.Frame(right, bg=CARD_BG)
        editor_actions.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        editor_actions.grid_columnconfigure(0, weight=1)
        editor_actions.grid_columnconfigure(1, weight=1)
        editor_actions.grid_columnconfigure(2, weight=1)

        tk.Button(editor_actions, text="Apply Changes", command=self.apply_selected_field, bg=ACCENT, fg=BUTTON_FG, relief="flat", padx=12, pady=6, font=FONT_BOLD).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Button(editor_actions, text="Delete Field", command=self.delete_selected_field, bg=ACCENT, fg=BUTTON_FG, relief="flat", padx=12, pady=6, font=FONT_BOLD).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        tk.Button(editor_actions, text="Rebuild From Snapshot", command=self.rebuild_rows_from_snapshot, bg=ACCENT, fg=BUTTON_FG, relief="flat", padx=12, pady=6, font=FONT_BOLD).grid(row=0, column=2, sticky="ew")

    def _make_editor_field(self, parent, row, label_text, variable):
        tk.Label(parent, text=label_text, font=FONT, fg=MUTED, bg=CARD_BG, anchor="w", width=12).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=4)
        tk.Entry(
            parent,
            textvariable=variable,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT,
        ).grid(row=row, column=1, sticky="ew", pady=4, ipady=4)

    def _safe_askopenfilename(self, **kwargs):
        options = dict(kwargs)
        options.setdefault("parent", self.window)
        options.setdefault("initialdir", self._default_dialog_dir())
        try:
            return filedialog.askopenfilename(**options)
        except Exception as exc:
            messagebox.showerror("Dialog error", f"Could not open file dialog.\n\n{exc}", parent=self.window)
            return ""

    def _safe_asksaveasfilename(self, **kwargs):
        options = dict(kwargs)
        options.setdefault("parent", self.window)
        options.setdefault("initialdir", self._default_dialog_dir())
        try:
            return filedialog.asksaveasfilename(**options)
        except Exception as exc:
            messagebox.showerror("Dialog error", f"Could not open save dialog.\n\n{exc}", parent=self.window)
            return ""

    def _default_dialog_dir(self):
        if self.generator_path:
            return os.path.dirname(self.generator_path) or os.getcwd()
        source_path = (self.generator_data.get("source_xml_path") or "").strip()
        if source_path and os.path.exists(source_path):
            return os.path.dirname(source_path) or os.getcwd()
        current_file = getattr(self.app, "current_file", None)
        if current_file:
            return os.path.dirname(current_file) or os.getcwd()
        return os.getcwd()

    def _refresh_recent_combo(self):
        self.recent_combo["values"] = self.recent_generator_paths
        if self.generator_path:
            self.recent_generator_var.set(self.generator_path)

    def _remember_recent_generator(self, file_path):
        if not file_path:
            return
        if file_path in self.recent_generator_paths:
            self.recent_generator_paths.remove(file_path)
        self.recent_generator_paths.insert(0, file_path)
        self.recent_generator_paths = self.recent_generator_paths[:10]
        self._refresh_recent_combo()

    def set_status(self, text):
        self.status_var.set(text)

    def use_current_xml(self):
        xml_text = self.app.get_current_xml_text()
        if not xml_text:
            messagebox.showwarning("No XML", "Open an XML file in the editor first.", parent=self.window)
            return
        source_name = self.app.get_current_xml_display_name()
        self._build_generator_from_xml_text(xml_text, source_name)
        self.set_status("Generator built from the currently open XML.")

    def browse_xml(self):
        file_path = self._safe_askopenfilename(
            title="Open XML for Generator",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                xml_text = handle.read()
        except Exception as exc:
            messagebox.showerror("Open error", f"Could not read XML file.\n\n{exc}", parent=self.window)
            return

        self._build_generator_from_xml_text(xml_text, file_path)
        self.set_status("Generator built from the selected XML file.")

    def _build_generator_from_xml_text(self, xml_text, source_name):
        try:
            root = ET.fromstring(xml_text)
        except Exception as exc:
            messagebox.showerror("Parse error", f"Could not parse XML.\n\n{exc}", parent=self.window)
            return

        fields = []
        self._collect_fields(root, f".//{root.tag}", fields)
        generator_name = os.path.splitext(os.path.basename(source_name))[0] if source_name else "XML Generator"

        self.generator_data = {
            "generator_name": generator_name,
            "source_xml_path": source_name,
            "xml_snapshot": xml_text,
            "fields": fields,
        }
        self.generator_path = None
        self.generator_name_var.set(generator_name)
        self.source_xml_var.set(f"Source XML: {source_name}")
        self.generator_var.set("Generator file: not saved")
        self.selected_field_index = None
        self._clear_editor()
        self.refresh_rows()

    def _collect_fields(self, element, path, fields):
        for attr_name, attr_value in element.attrib.items():
            fields.append({
                "label": f"{element.tag} @{attr_name}",
                "path": path,
                "attribute": attr_name,
                "type": "string",
                "value": attr_value,
            })

        children = list(element)
        text_value = (element.text or "").strip()
        if text_value:
            fields.append({
                "label": element.tag,
                "path": path,
                "attribute": "",
                "type": "string",
                "value": text_value,
            })

        same_tag_counts = {}
        for child in children:
            same_tag_counts[child.tag] = same_tag_counts.get(child.tag, 0) + 1
            child_index = same_tag_counts[child.tag]
            child_path = f"{path}/{child.tag}[{child_index}]"
            self._collect_fields(child, child_path, fields)

    def rebuild_rows_from_snapshot(self):
        xml_snapshot = (self.generator_data.get("xml_snapshot") or "").strip()
        if not xml_snapshot:
            messagebox.showwarning("No snapshot", "This generator does not contain an XML snapshot.", parent=self.window)
            return
        source_name = self.generator_data.get("source_xml_path") or "Embedded snapshot"
        self._build_generator_from_xml_text(xml_snapshot, source_name)
        self.set_status("Generator fields rebuilt from the stored XML snapshot.")

    def _field_matches_filter(self, field, filter_text):
        if not filter_text:
            return True
        blob = " ".join([
            str(field.get("label", "")),
            str(field.get("path", "")),
            str(field.get("attribute", "")),
            str(field.get("type", "")),
            str(field.get("value", "")),
        ]).lower()
        return filter_text in blob

    def refresh_rows(self, *args):
        self._push_editor_to_model_if_possible()
        self.tree.delete(*self.tree.get_children())
        self.filtered_indices = []

        filter_text = self.search_var.get().strip().lower()
        fields = self.generator_data.get("fields", [])
        for index, field in enumerate(fields):
            if not self._field_matches_filter(field, filter_text):
                continue
            self.filtered_indices.append(index)
            value_text = "" if field.get("value") is None else str(field.get("value"))
            self.tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    field.get("label", ""),
                    field.get("path", ""),
                    field.get("attribute", ""),
                    field.get("type", "string"),
                    value_text,
                ),
            )

        if self.selected_field_index is not None and str(self.selected_field_index) in self.tree.get_children():
            self.tree.selection_set(str(self.selected_field_index))
            self.tree.focus(str(self.selected_field_index))
        else:
            self.selected_field_index = None
            self._clear_editor()

        self.set_status(f"Showing {len(self.filtered_indices)} field(s).")

    def _on_tree_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            self.selected_field_index = None
            self._clear_editor()
            return
        try:
            index = int(selection[0])
        except Exception:
            return
        self._push_editor_to_model_if_possible(except_index=index)
        self.selected_field_index = index
        self._load_selected_into_editor()

    def _load_selected_into_editor(self):
        if self.selected_field_index is None:
            self._clear_editor()
            return
        fields = self.generator_data.get("fields", [])
        if self.selected_field_index < 0 or self.selected_field_index >= len(fields):
            self._clear_editor()
            return
        field = fields[self.selected_field_index]
        self.updating_editor = True
        try:
            self.label_var.set(field.get("label", ""))
            self.path_var.set(field.get("path", ""))
            self.attr_var.set(field.get("attribute", ""))
            self.type_var.set(field.get("type", "string") or "string")
            self.value_var.set("" if field.get("value") is None else str(field.get("value")))
        finally:
            self.updating_editor = False

    def _clear_editor(self):
        self.updating_editor = True
        try:
            self.label_var.set("")
            self.path_var.set("")
            self.attr_var.set("")
            self.type_var.set("string")
            self.value_var.set("")
        finally:
            self.updating_editor = False

    def _push_editor_to_model_if_possible(self, except_index=None):
        if self.updating_editor or self.selected_field_index is None:
            return
        if self.selected_field_index == except_index:
            return
        self._update_field_from_editor(self.selected_field_index)

    def _update_field_from_editor(self, index):
        fields = self.generator_data.get("fields", [])
        if index < 0 or index >= len(fields):
            return
        field_type = (self.type_var.get() or "string").strip().lower()
        raw_value = self.value_var.get()
        if field_type in ("", "string", "auto"):
            stored_value = raw_value
            stored_type = "string" if field_type in ("", "auto") else field_type
        else:
            stored_value = parse_typed_value(raw_value, field_type)
            stored_type = field_type
        fields[index] = {
            "label": self.label_var.get().strip(),
            "path": self.path_var.get().strip(),
            "attribute": self.attr_var.get().strip(),
            "type": stored_type,
            "value": stored_value,
        }

    def apply_selected_field(self):
        if self.selected_field_index is None:
            messagebox.showwarning("No field", "Select a field first.", parent=self.window)
            return
        self._update_field_from_editor(self.selected_field_index)
        self.refresh_rows()
        self.tree.selection_set(str(self.selected_field_index))
        self.tree.focus(str(self.selected_field_index))
        self.set_status("Field updated.")

    def add_blank_field(self):
        self._push_editor_to_model_if_possible()
        self.generator_data.setdefault("fields", []).append({
            "label": "New Field",
            "path": "",
            "attribute": "",
            "type": "string",
            "value": "",
        })
        self.refresh_rows()
        new_index = len(self.generator_data["fields"]) - 1
        self.selected_field_index = new_index
        if str(new_index) in self.tree.get_children():
            self.tree.selection_set(str(new_index))
            self.tree.focus(str(new_index))
            self._load_selected_into_editor()
        self.set_status("Blank field added.")

    def add_from_current_selection(self):
        selected = getattr(self.app, "selected_xml_target", None)
        if not selected:
            messagebox.showwarning("No XML selection", "Select a field in the main XML editor first.", parent=self.window)
            return
        self._push_editor_to_model_if_possible()
        attribute = selected.get("attribute") or ""
        label = selected.get("label") or selected.get("path") or "Selected Field"
        self.generator_data.setdefault("fields", []).append({
            "label": label,
            "path": selected.get("path") or "",
            "attribute": attribute,
            "type": "string",
            "value": selected.get("value") or "",
        })
        self.refresh_rows()
        new_index = len(self.generator_data["fields"]) - 1
        self.selected_field_index = new_index
        if str(new_index) in self.tree.get_children():
            self.tree.selection_set(str(new_index))
            self.tree.focus(str(new_index))
            self._load_selected_into_editor()
        self.set_status("Field added from the current XML selection.")

    def delete_selected_field(self):
        if self.selected_field_index is None:
            messagebox.showwarning("No field", "Select a field first.", parent=self.window)
            return
        fields = self.generator_data.get("fields", [])
        if self.selected_field_index < 0 or self.selected_field_index >= len(fields):
            return
        del fields[self.selected_field_index]
        self.selected_field_index = None
        self.refresh_rows()
        self.set_status("Field deleted.")

    def _normalize_generator_for_save(self):
        self._push_editor_to_model_if_possible()
        return {
            "generator_name": self.generator_name_var.get().strip() or self.generator_data.get("generator_name") or "XML Generator",
            "source_xml_path": self.generator_data.get("source_xml_path", ""),
            "xml_snapshot": self.generator_data.get("xml_snapshot", ""),
            "fields": self.generator_data.get("fields", []),
        }

    def save_generator(self):
        if not (self.generator_data.get("xml_snapshot") or "").strip():
            messagebox.showwarning("Nothing to save", "Load or build a generator from XML first.", parent=self.window)
            return
        if not self.generator_path:
            self.save_generator_as()
            return
        self._save_generator_to_path(self.generator_path)

    def save_generator_as(self):
        if not (self.generator_data.get("xml_snapshot") or "").strip():
            messagebox.showwarning("Nothing to save", "Load or build a generator from XML first.", parent=self.window)
            return
        suggested_name = self._suggest_generator_filename()
        file_path = self._safe_asksaveasfilename(
            title="Save XML Generator As",
            defaultextension=".json",
            initialfile=suggested_name,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self.generator_path = file_path
        self._save_generator_to_path(file_path)

    def _save_generator_to_path(self, file_path):
        try:
            data = self._normalize_generator_for_save()
            with open(file_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
        except Exception as exc:
            messagebox.showerror("Save error", f"Could not save generator.\n\n{exc}", parent=self.window)
            return
        self.generator_path = file_path
        self.generator_data["generator_name"] = data["generator_name"]
        self.generator_name_var.set(data["generator_name"])
        self.generator_var.set(f"Generator file: {file_path}")
        self._remember_recent_generator(file_path)
        self.set_status("Generator saved successfully.")

    def load_generator(self):
        file_path = self._safe_askopenfilename(
            title="Load XML Generator",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self._load_generator_from_path(file_path)

    def load_recent_generator(self):
        file_path = self.recent_generator_var.get().strip()
        if not file_path:
            return
        self._load_generator_from_path(file_path)

    def _load_generator_from_path(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load generator.\n\n{exc}", parent=self.window)
            return

        if not isinstance(data, dict):
            messagebox.showwarning("Invalid generator", "Generator file must contain a JSON object.", parent=self.window)
            return

        data.setdefault("generator_name", os.path.splitext(os.path.basename(file_path))[0])
        data.setdefault("source_xml_path", "")
        data.setdefault("xml_snapshot", "")
        data.setdefault("fields", [])
        if not isinstance(data["fields"], list):
            data["fields"] = []

        normalized_fields = []
        for field in data["fields"]:
            if not isinstance(field, dict):
                continue
            normalized_fields.append({
                "label": str(field.get("label", "")),
                "path": str(field.get("path", "")),
                "attribute": str(field.get("attribute", "")),
                "type": str(field.get("type", "string") or "string").lower(),
                "value": field.get("value", ""),
            })
        data["fields"] = normalized_fields

        self.generator_data = data
        self.generator_path = file_path
        self.generator_name_var.set(data.get("generator_name") or "")
        self.source_xml_var.set(f"Source XML: {data.get('source_xml_path') or 'Embedded snapshot'}")
        self.generator_var.set(f"Generator file: {file_path}")
        self.selected_field_index = None
        self._clear_editor()
        self._remember_recent_generator(file_path)
        self.refresh_rows()
        self.set_status("Generator loaded successfully.")

    def _suggest_generator_filename(self):
        base_name = (self.generator_name_var.get() or self.generator_data.get("generator_name") or "xml_generator").strip()
        safe = self._sanitize_filename(base_name) or "xml_generator"
        return f"{safe}.json"

    def _suggest_output_filename(self):
        source_path = (self.generator_data.get("source_xml_path") or "").strip()
        generator_name = (self.generator_name_var.get() or self.generator_data.get("generator_name") or "generated_xml").strip()
        if source_path:
            base = os.path.splitext(os.path.basename(source_path))[0]
        else:
            base = generator_name or "generated_xml"
        safe = self._sanitize_filename(base) or "generated_xml"
        return f"{safe}_generated.xml"

    def _sanitize_filename(self, text):
        invalid_chars = set('<>:"/\\|?*')
        return "".join(ch if ch not in invalid_chars else "_" for ch in text).strip()

    def _apply_generator_fields_to_root(self, root):
        for field in self.generator_data.get("fields", []):
            path = (field.get("path") or "").strip()
            attribute = (field.get("attribute") or "").strip()
            value_type = (field.get("type") or "string").strip().lower()
            raw_value = field.get("value")
            if not path:
                continue

            targets = []
            for candidate in normalize_config_paths(root, path):
                try:
                    targets = root.findall(candidate)
                except Exception:
                    continue
                if targets:
                    break
            if not targets:
                continue

            if value_type in ("", "string", "auto"):
                text_value = "" if raw_value is None else str(raw_value)
            else:
                parsed_value = parse_typed_value(raw_value, value_type)
                text_value = typed_value_to_xml_text(parsed_value)

            for target in targets:
                if attribute:
                    target.attrib[attribute] = text_value
                else:
                    target.text = text_value

    def generate_xml(self):
        self.generate_xml_as()

    def generate_xml_as(self):
        if not (self.generator_data.get("xml_snapshot") or "").strip():
            messagebox.showwarning("No generator", "Load or build a generator first.", parent=self.window)
            return
        default_name = self._suggest_output_filename()
        file_path = self._safe_asksaveasfilename(
            title="Generate XML As",
            defaultextension=".xml",
            initialfile=default_name,
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self._generate_xml_to_path(file_path)

    def _generate_xml_to_path(self, file_path):
        xml_snapshot = (self.generator_data.get("xml_snapshot") or "").strip()
        if not xml_snapshot:
            messagebox.showwarning("No generator", "This generator does not contain XML structure to generate from.", parent=self.window)
            return

        self._push_editor_to_model_if_possible()

        try:
            root = ET.fromstring(xml_snapshot)
            self._apply_generator_fields_to_root(root)
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding="utf-8", xml_declaration=True)
        except Exception as exc:
            messagebox.showerror("Generate error", f"Could not generate XML.\n\n{exc}", parent=self.window)
            return

        self.set_status(f"Generated XML written to: {file_path}")
        messagebox.showinfo("XML Generated", f"Generated XML saved to:\n{file_path}", parent=self.window)



def launch(app):
    return XmlGeneratorToolWindow(app)
