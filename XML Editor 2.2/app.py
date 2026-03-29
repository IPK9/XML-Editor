import json
import tkinter as tk
from tkinter import filedialog, messagebox
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
    FONT_SECTION,
)
from xml_utils import (
    normalize_config_paths,
    group_children,
    build_child_path,
    matches_filter,
    element_or_descendant_matches,
)
from json_utils import parse_typed_value, typed_value_to_xml_text
from json_editor import JsonEditorWindow


class XMLGuiEditor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("XML Editor")
        self.root.geometry("1300x820")
        self.root.configure(bg=BG)

        self.current_file = None
        self.tree = None
        self.xml_root = None

        self.loaded_config = {"replacements": []}
        self.loaded_config_path = None
        self.recent_config_paths = []

        self.selected_xml_target = None
        self.selected_json_rule = None

        self.bound_widgets = []
        self.collapsible_sections = []
        self.json_editor = None

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.refresh_view)
        self.xml_status_var = tk.StringVar(value="Open an XML file to begin.")

        self._build_window()

    # =========================
    # SCROLL
    # =========================
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    # =========================
    # UI SETUP
    # =========================
    def _build_window(self):
        self._build_top_bar()
        self._build_scroll_area()
        self._build_status_bar()

    def _build_top_bar(self):
        top_bar = tk.Frame(self.root, bg=BG)
        top_bar.pack(fill="x", padx=12, pady=12)

        tk.Label(
            top_bar,
            text="XML Editor",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG,
        ).pack(side="left")

        right_bar = tk.Frame(top_bar, bg=BG)
        right_bar.pack(side="right")

        tk.Entry(
            right_bar,
            textvariable=self.search_var,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            width=24,
            font=FONT,
        ).pack(side="left", padx=(0, 8), ipady=4)

        button_specs = [
            ("Expand All", self.expand_all),
            ("Collapse All", self.collapse_all),
            ("Open XML", self.open_xml),
            ("JSON Editor", self.open_json_editor),
            ("Load Config", self.load_config),
            ("Auto Replace", self.auto_replace_from_config),
            ("Save XML", self.save_xml),
            ("Save XML As", self.save_xml_as),
        ]

        for index, (text, cmd) in enumerate(button_specs):
            tk.Button(
                right_bar,
                text=text,
                command=cmd,
                bg=ACCENT,
                fg=BUTTON_FG,
                relief="flat",
                padx=12,
                pady=6,
                font=FONT_BOLD,
            ).pack(side="left", padx=(0, 8 if index < len(button_specs) - 1 else 0))

        self.file_label = tk.Label(
            self.root,
            text="No XML file loaded",
            font=FONT,
            fg=MUTED,
            bg=BG,
            anchor="w",
        )
        self.file_label.pack(fill="x", padx=14, pady=(0, 8))

    def _build_scroll_area(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        self.v_scroll = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(outer, orient="horizontal", command=self.canvas.xview)

        self.content_frame = tk.Frame(self.canvas, bg=BG)
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
        )

        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mouse_wheel)

    def _build_status_bar(self):
        status_frame = tk.Frame(self.root, bg=PANEL_BG)
        status_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(
            status_frame,
            textvariable=self.xml_status_var,
            font=FONT,
            fg=MUTED,
            bg=PANEL_BG,
            anchor="w",
            padx=10,
            pady=8,
        ).pack(fill="x")

    # =========================
    # FILE ACTIONS
    # =========================
    def open_xml(self):
        file_path = filedialog.askopenfilename(
            title="Open XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            tree = ET.parse(file_path)
            xml_root = tree.getroot()
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open XML file.\n\n{exc}")
            return

        self.current_file = file_path
        self.tree = tree
        self.xml_root = xml_root
        self.file_label.config(text=file_path)
        self.refresh_view()
        self._set_xml_status(f"Loaded XML root: <{self.xml_root.tag}>")

    def save_xml(self):
        if self.tree is None or self.xml_root is None:
            messagebox.showwarning("No file", "Open an XML file first.")
            return

        if not self.current_file:
            self.save_xml_as()
            return

        self._save_xml_to_path(self.current_file)

    def save_xml_as(self):
        if self.tree is None or self.xml_root is None:
            messagebox.showwarning("No file", "Open an XML file first.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save XML As",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not file_path:
            return

        self.current_file = file_path
        self.file_label.config(text=file_path)
        self._save_xml_to_path(file_path)

    def _save_xml_to_path(self, file_path):
        try:
            self._write_widgets_back_to_xml()
            self.tree.write(file_path, encoding="utf-8", xml_declaration=True)
            messagebox.showinfo("Saved", f"Changes saved to:\n{file_path}")
        except Exception as exc:
            messagebox.showerror("Save error", f"Could not save XML.\n\n{exc}")

    def load_config(self):
        file_path = filedialog.askopenfilename(
            title="Load JSON Config",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return
        self._load_config_from_path(file_path)

    def _load_config_from_path(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            messagebox.showerror("Config error", f"Could not load config.\n\n{exc}")
            return False

        if not isinstance(data, dict):
            messagebox.showwarning("Invalid config", "JSON config must be an object at the top level.")
            return False

        if "replacements" not in data or not isinstance(data["replacements"], list):
            data["replacements"] = []

        self.loaded_config = data
        self.loaded_config_path = file_path
        self._remember_recent_config(file_path)

        if self.json_editor is not None and self.json_editor.window.winfo_exists():
            self.json_editor.refresh_rows()

        messagebox.showinfo("Config loaded", f"Loaded config:\n{file_path}")
        return True

    def _save_json_to_path(self, file_path):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.loaded_config, f, indent=2)
            messagebox.showinfo("JSON saved", f"Saved JSON config.\n\n{file_path}")
        except Exception as exc:
            messagebox.showerror("JSON save error", f"Could not save JSON config.\n\n{exc}")

    def _remember_recent_config(self, file_path):
        if file_path in self.recent_config_paths:
            self.recent_config_paths.remove(file_path)
        self.recent_config_paths.insert(0, file_path)
        self.recent_config_paths = self.recent_config_paths[:10]

    def open_json_editor(self):
        if self.json_editor is not None and self.json_editor.window.winfo_exists():
            self.json_editor.window.lift()
            return
        self.json_editor = JsonEditorWindow(self)

    # =========================
    # DIFF PREVIEW
    # =========================
    def generate_diff_preview(self):
        if self.xml_root is None:
            return []

        diffs = []

        for rule in self.loaded_config.get("replacements", []):
            if not isinstance(rule, dict):
                continue

            raw_path = (rule.get("path") or "").strip()
            raw_value = rule.get("value")
            value_type = (rule.get("type") or "auto").strip().lower()
            attribute = (rule.get("attribute") or "").strip()

            if not raw_path:
                continue

            new_value = parse_typed_value(raw_value, value_type)
            new_text = "" if new_value is None else typed_value_to_xml_text(new_value)

            for path in normalize_config_paths(self.xml_root, raw_path):
                try:
                    elements = self.xml_root.findall(path)
                except Exception:
                    continue

                for element in elements:
                    if attribute:
                        old = element.attrib.get(attribute, "")
                        if old != new_text:
                            diffs.append({
                                "path": path,
                                "type": "attribute",
                                "attribute": attribute,
                                "old": old,
                                "new": new_text,
                            })
                    else:
                        old = element.text or ""
                        if old != new_text:
                            diffs.append({
                                "path": path,
                                "type": "text",
                                "old": old,
                                "new": new_text,
                            })

                if elements:
                    break

        return diffs

    def show_diff_preview(self, diffs):
        if not diffs:
            messagebox.showinfo("No Changes", "No differences found.")
            return False

        preview_window = tk.Toplevel(self.root)
        preview_window.title("Preview Changes")
        preview_window.geometry("800x600")
        preview_window.configure(bg=BG)

        text = tk.Text(
            preview_window,
            bg=ENTRY_BG,
            fg=TEXT,
            wrap="word",
            insertbackground=TEXT,
        )
        text.pack(fill="both", expand=True, padx=10, pady=10)

        for d in diffs:
            if d["type"] == "attribute":
                line = f'{d["path"]} @{d["attribute"]}\n{d["old"]} → {d["new"]}\n\n'
            else:
                line = f'{d["path"]}\n{d["old"]} → {d["new"]}\n\n'
            text.insert("end", line)

        text.config(state="disabled")

        result = {"apply": False}

        def apply_changes():
            result["apply"] = True
            preview_window.destroy()

        def cancel():
            preview_window.destroy()

        btn_frame = tk.Frame(preview_window, bg=BG)
        btn_frame.pack(fill="x", pady=10)

        tk.Button(
            btn_frame,
            text="Apply",
            command=apply_changes,
            bg=ACCENT,
            fg=BUTTON_FG,
            relief="flat",
            padx=12,
            pady=6,
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=cancel,
            bg=ACCENT,
            fg=BUTTON_FG,
            relief="flat",
            padx=12,
            pady=6,
        ).pack(side="right", padx=10)

        preview_window.wait_window()
        return result["apply"]

    def auto_replace_from_config(self):
        if self.xml_root is None:
            messagebox.showwarning("No XML", "Open an XML file first.")
            return

        replacements = self.loaded_config.get("replacements", [])
        if not isinstance(replacements, list) or not replacements:
            messagebox.showwarning("No config", "Load or create a JSON config with at least one replacement.")
            return

        diffs = self.generate_diff_preview()
        if not self.show_diff_preview(diffs):
            return

        changed = 0
        for rule in replacements:
            if not isinstance(rule, dict):
                continue

            raw_path = (rule.get("path") or "").strip()
            raw_value = rule.get("value")
            value_type = (rule.get("type") or "auto").strip().lower()
            attribute = (rule.get("attribute") or "").strip()

            if not raw_path:
                continue

            value = parse_typed_value(raw_value, value_type)
            normalized_paths = normalize_config_paths(self.xml_root, raw_path)

            for path in normalized_paths:
                try:
                    elements = self.xml_root.findall(path)
                except Exception:
                    continue

                if not elements:
                    continue

                for element in elements:
                    value_as_text = "" if value is None else typed_value_to_xml_text(value)
                    if attribute:
                        element.attrib[attribute] = value_as_text
                    else:
                        element.text = value_as_text
                    changed += 1
                break

        self.refresh_view()
        messagebox.showinfo("Auto Replace", f"Updated {changed} value(s) from config.")

    # =========================
    # VIEW RENDERING
    # =========================
    def refresh_view(self, *args):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.bound_widgets.clear()
        self.collapsible_sections.clear()
        self.selected_xml_target = None

        if self.xml_root is None:
            tk.Label(
                self.content_frame,
                text="Open an XML file to begin",
                font=FONT_SECTION,
                fg=MUTED,
                bg=BG,
                pady=40,
            ).pack()
            self.canvas.yview_moveto(0)
            self.canvas.xview_moveto(0)
            return

        filter_text = self.search_var.get().strip().lower()

        root_card = tk.Frame(
            self.content_frame,
            bg=PANEL_BG,
            bd=1,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        root_card.pack(fill="x", padx=8, pady=8)

        title_text = f"<{self.xml_root.tag}>"
        if self.xml_root.attrib:
            title_text += "  (root has attributes)"

        tk.Label(
            root_card,
            text=title_text,
            font=FONT_SECTION,
            fg=ACCENT,
            bg=PANEL_BG,
            anchor="w",
            padx=12,
            pady=10,
        ).pack(fill="x")

        body = tk.Frame(root_card, bg=PANEL_BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._render_element_content(
            body,
            self.xml_root,
            f".//{self.xml_root.tag}",
            0,
            filter_text,
            PANEL_BG,
            True,
        )

        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)

        if self.selected_json_rule is not None:
            self.highlight_matches_for_json_row(self.selected_json_rule)

    # =========================
    # XML -> GUI
    # =========================
    def _render_element_content(self, parent, element, path, depth, filter_text, bg_for_children, force_expand_groups=False):
        children = list(element)
        has_children = len(children) > 0
        has_attributes = len(element.attrib) > 0
        text_value = (element.text or "").strip()
        has_text = text_value != ""

        if has_attributes:
            attrs_frame = tk.Frame(parent, bg=bg_for_children)
            attrs_frame.pack(fill="x", pady=(0, 8))

            tk.Label(
                attrs_frame,
                text="Attributes",
                font=FONT_BOLD,
                fg=ACCENT,
                bg=bg_for_children,
                anchor="w",
            ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

            row = 1
            for attr_name, attr_value in element.attrib.items():
                if filter_text and not matches_filter(attr_name, attr_value, path, filter_text):
                    continue
                self._make_value_widget(
                    attrs_frame,
                    row,
                    f"@{attr_name}",
                    attr_value,
                    element,
                    "attribute",
                    attr_name,
                    bg_for_children,
                    path,
                )
                row += 1

            attrs_frame.grid_columnconfigure(1, weight=1)

        if has_text and has_children:
            if not filter_text or matches_filter(element.tag, text_value, path, filter_text):
                text_frame = tk.Frame(parent, bg=bg_for_children)
                text_frame.pack(fill="x", pady=(0, 8))
                self._make_value_widget(
                    text_frame,
                    0,
                    "#text",
                    text_value,
                    element,
                    "text",
                    None,
                    bg_for_children,
                    path,
                )
                text_frame.grid_columnconfigure(1, weight=1)

        if not has_children:
            if has_text or has_attributes:
                leaf_frame = tk.Frame(parent, bg=bg_for_children)
                leaf_frame.pack(fill="x")
                if has_text and (not filter_text or matches_filter(element.tag, text_value, path, filter_text)):
                    self._make_value_widget(
                        leaf_frame,
                        0,
                        element.tag,
                        text_value,
                        element,
                        "text",
                        None,
                        bg_for_children,
                        path,
                    )
                    leaf_frame.grid_columnconfigure(1, weight=1)
            return

        grouped = group_children(children)

        for tag_name, items in grouped:
            if len(items) == 1:
                child = items[0]
                child_has_children = len(list(child)) > 0
                child_has_attrs = len(child.attrib) > 0
                child_text = (child.text or "").strip()
                child_path = build_child_path(element, path, child)

                if not child_has_children:
                    child_matches = (not filter_text) or element_or_descendant_matches(child, child_path, filter_text)
                    if not child_matches:
                        continue

                    row_holder = tk.Frame(parent, bg=bg_for_children)
                    row_holder.pack(fill="x", pady=(0, 6))
                    self._make_value_widget(
                        row_holder,
                        0,
                        child.tag,
                        child_text,
                        child,
                        "text",
                        None,
                        bg_for_children,
                        child_path,
                    )
                    row_holder.grid_columnconfigure(1, weight=1)

                    if child_has_attrs:
                        _, attrs_body, attrs_info = self._make_collapsible_card(
                            parent,
                            f"{child.tag} attributes",
                            depth + 1,
                            ACCENT,
                            bg_for_children,
                            outer_padx=20,
                            inner_padx=8,
                            inner_pady=8,
                            expanded=False if not filter_text else True,
                        )

                        def build_attrs(body_frame=attrs_body, elem=child, elem_path=child_path, bg=bg_for_children):
                            sub_row = 0
                            for attr_name, attr_value in elem.attrib.items():
                                if filter_text and not matches_filter(attr_name, attr_value, elem_path, filter_text):
                                    continue
                                self._make_value_widget(
                                    body_frame,
                                    sub_row,
                                    f"@{attr_name}",
                                    attr_value,
                                    elem,
                                    "attribute",
                                    attr_name,
                                    bg,
                                    elem_path,
                                )
                                sub_row += 1
                            body_frame.grid_columnconfigure(1, weight=1)

                        attrs_info["builder"] = build_attrs
                        if attrs_info["expanded"]:
                            self._build_section_if_needed(attrs_info)
                else:
                    if filter_text and not element_or_descendant_matches(child, child_path, filter_text):
                        continue
                    expanded = True if filter_text else False
                    self._make_lazy_element_card(parent, f"<{child.tag}>", child, child_path, depth + 1, filter_text, TEXT, CARD_BG, expanded)
            else:
                matching_items = []
                for item in items:
                    item_path = build_child_path(element, path, item)
                    if (not filter_text) or element_or_descendant_matches(item, item_path, filter_text):
                        matching_items.append((item, item_path))

                if not matching_items:
                    continue

                _, group_body, group_info = self._make_collapsible_card(
                    parent,
                    f"{tag_name} ({len(matching_items)})",
                    depth + 1,
                    ACCENT,
                    bg_for_children,
                    expanded=True if (filter_text or force_expand_groups) else False,
                )

                def build_group(body_frame=group_body, matches=matching_items, f=filter_text, name=tag_name):
                    for index, (item, item_path) in enumerate(matches, start=1):
                        expanded = True if f else False
                        self._make_lazy_element_card(body_frame, f"{name} #{index}", item, item_path, 0, f, TEXT, CARD_BG, expanded, 0)

                group_info["builder"] = build_group
                if group_info["expanded"]:
                    self._build_section_if_needed(group_info)

    def _make_lazy_element_card(self, parent, title, element, path, depth, filter_text, title_fg, card_bg, expanded=False, outer_padx=None):
        _, body, section_info = self._make_collapsible_card(parent, title, depth, title_fg, card_bg, outer_padx, expanded=expanded)

        def build_element(body_frame=body, xml_element=element, xml_path=path, d=depth, f=filter_text, bg=card_bg):
            self._render_element_content(body_frame, xml_element, xml_path, d, f, bg)

        section_info["builder"] = build_element
        if section_info["expanded"]:
            self._build_section_if_needed(section_info)

    def _make_collapsible_card(self, parent, title, depth, title_fg, card_bg, outer_padx=None, inner_padx=10, inner_pady=10, expanded=True):
        if outer_padx is None:
            outer_padx = 8 + (depth * 10)

        outer = tk.Frame(parent, bg=card_bg, bd=1, highlightbackground=BORDER, highlightthickness=1)
        outer.pack(fill="x", padx=outer_padx, pady=6)

        header = tk.Frame(outer, bg=card_bg)
        header.pack(fill="x")

        toggle_btn = tk.Button(
            header,
            text="▼" if expanded else "▶",
            width=2,
            bg=card_bg,
            fg=title_fg,
            relief="flat",
            activebackground=card_bg,
            activeforeground=title_fg,
            bd=0,
            highlightthickness=0,
            font=FONT_BOLD,
            padx=2,
            pady=6,
        )
        toggle_btn.pack(side="left", padx=(6, 2))

        tk.Label(
            header,
            text=title,
            font=FONT_BOLD,
            fg=title_fg,
            bg=card_bg,
            anchor="w",
            pady=8,
        ).pack(side="left", fill="x", expand=True)

        body = tk.Frame(outer, bg=card_bg)
        if expanded:
            body.pack(fill="x", padx=inner_padx, pady=(0, inner_pady))

        section_info = {
            "button": toggle_btn,
            "body": body,
            "expanded": expanded,
            "built": False,
            "builder": None,
            "pack_args": {"fill": "x", "padx": inner_padx, "pady": (0, inner_pady)},
        }
        self.collapsible_sections.append(section_info)
        toggle_btn.configure(command=lambda s=section_info: self._toggle_section(s))
        return outer, body, section_info

    def _toggle_section(self, section_info, force=None):
        new_state = (not section_info["expanded"]) if force is None else force
        if section_info["expanded"] == new_state:
            return

        section_info["expanded"] = new_state
        if new_state:
            self._build_section_if_needed(section_info)
            section_info["body"].pack(**section_info["pack_args"])
            section_info["button"].configure(text="▼")
        else:
            section_info["body"].pack_forget()
            section_info["button"].configure(text="▶")

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _build_section_if_needed(self, section_info):
        if section_info["built"]:
            return
        builder = section_info.get("builder")
        if builder is not None:
            builder()
            section_info["built"] = True

    def expand_all(self):
        for section_info in self.collapsible_sections:
            self._toggle_section(section_info, force=True)

    def collapse_all(self):
        for section_info in reversed(self.collapsible_sections):
            self._toggle_section(section_info, force=False)

    def _make_value_widget(self, parent, row, label_text, value, owner, kind, key, bg, path):
        label = tk.Label(parent, text=label_text, font=FONT, fg=MUTED, bg=bg, anchor="w", width=22)
        label.grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=4)

        multiline = "\n" in value or len(value) > 90
        if multiline:
            widget = tk.Text(
                parent,
                height=max(3, min(8, value.count("\n") + 2)),
                wrap="word",
                bg=ENTRY_BG,
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                font=FONT,
                highlightthickness=1,
                highlightbackground=BORDER,
            )
            widget.insert("1.0", value)
            widget.grid(row=row, column=1, sticky="ew", pady=4)
        else:
            widget = tk.Entry(
                parent,
                bg=ENTRY_BG,
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                font=FONT,
                highlightthickness=1,
                highlightbackground=BORDER,
            )
            widget.insert(0, value)
            widget.grid(row=row, column=1, sticky="ew", pady=4, ipady=4)

        info = {
            "owner": owner,
            "kind": kind,
            "key": key,
            "label_text": label_text,
            "widget": widget,
            "path": path,
        }
        label.bind("<Button-1>", lambda event, i=info: self._select_xml_target(i))
        widget.bind("<Button-1>", lambda event, i=info: self._select_xml_target(i))

        self.bound_widgets.append({
            "owner": owner,
            "kind": kind,
            "key": key,
            "widget": widget,
            "label": label,
        })

    # =========================
    # SAVE / HIGHLIGHT SUPPORT
    # =========================
    def _write_widgets_back_to_xml(self):
        for item in self.bound_widgets:
            owner = item["owner"]
            kind = item["kind"]
            key = item["key"]
            widget = item["widget"]
            value = widget.get("1.0", "end-1c") if isinstance(widget, tk.Text) else widget.get()

            if kind == "attribute":
                owner.attrib[key] = value
            elif kind == "text":
                owner.text = value

    def _select_xml_target(self, info):
        kind = info["kind"]
        key = info["key"]
        widget = info["widget"]
        path = info["path"]
        value = widget.get("1.0", "end-1c") if isinstance(widget, tk.Text) else widget.get()

        self.selected_xml_target = {
            "path": path,
            "attribute": key if kind == "attribute" else None,
            "value": value,
            "label": info["label_text"],
            "kind": kind,
        }

        self.reset_xml_match_highlights()
        for item in self.bound_widgets:
            if item["widget"] is widget:
                self._apply_widget_highlight(item, "selected")

        preview = value.replace("\n", " ")
        if len(preview) > 80:
            preview = preview[:77] + "..."

        field_type = f"attribute @{key}" if kind == "attribute" and key else "text"
        self._set_xml_status(f"Selected: {path} | Type: {field_type} | Value: {preview}")

        if self.json_editor is not None:
            self.json_editor.set_status(
                f"Selected XML field: {path}" + (f" @{key}" if kind == "attribute" and key else "")
            )

        if self.selected_json_rule is not None:
            self.highlight_matches_for_json_row(self.selected_json_rule)

    def _apply_widget_highlight(self, item, mode):
        if mode == "selected":
            item["label"].configure(fg=TEXT, bg=HIGHLIGHT_ROW)
            item["widget"].configure(highlightbackground=ACCENT, highlightcolor=ACCENT)
        elif mode == "match":
            item["label"].configure(fg=ACCENT, bg=item["label"].master.cget("bg"))
            item["widget"].configure(highlightbackground=ACCENT, highlightcolor=ACCENT)
        else:
            item["label"].configure(fg=MUTED, bg=item["label"].master.cget("bg"))
            item["widget"].configure(highlightbackground=BORDER, highlightcolor=ACCENT)

    def reset_xml_match_highlights(self):
        for item in self.bound_widgets:
            self._apply_widget_highlight(item, "normal")

    def highlight_matches_for_json_row(self, row_data):
        self.reset_xml_match_highlights()

        if self.xml_root is None:
            row_data["match_var"].set("Matches: 0")
            return

        raw_path = row_data["path_var"].get().strip()
        attribute = row_data["attr_var"].get().strip()
        if not raw_path:
            row_data["match_var"].set("Matches: 0")
            return

        matches = []
        for normalized in normalize_config_paths(self.xml_root, raw_path):
            try:
                elements = self.xml_root.findall(normalized)
            except Exception:
                continue
            if elements:
                matches = elements
                break

        count = 0
        for item in self.bound_widgets:
            owner_match = item["owner"] in matches
            kind_match = (item["kind"] == "attribute" and item["key"] == attribute) if attribute else item["kind"] == "text"
            if owner_match and kind_match:
                self._apply_widget_highlight(item, "match")
                count += 1

        row_data["match_var"].set(f"Matches: {count}")
        if self.json_editor is not None:
            self.json_editor.set_status(f"JSON rule matches {count} XML field(s).")

    def _set_xml_status(self, text):
        self.xml_status_var.set(text)

    # =========================
    # SCROLL / RESIZE
    # =========================
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_shift_mouse_wheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")