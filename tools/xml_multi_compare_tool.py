import csv
import os
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

TOOL_ID = "xml_multi_compare"
TOOL_NAME = "XML Multi-Compare"
TOOL_ORDER = 30
TOOL_DESCRIPTION = "Compare as many XML files as you want and find differences, missing values, and outliers."
SINGLE_INSTANCE = True

MISSING = object()
STATUS_SAME_ALL = "Same Across All"
STATUS_DIFFERENT = "Different"
STATUS_MISSING = "Missing in Some"
STATUS_SAME_BASELINE = "Same as Baseline"
STATUS_DIFF_BASELINE = "Different from Baseline"
STATUS_MISSING_BASELINE = "Missing vs Baseline"


def launch(app):
    return XmlMultiCompareToolWindow(app)


class XmlMultiCompareToolWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Toplevel(app.root)
        self.window.title("XML Multi-Compare")
        self.window.geometry("1680x900")
        self.window.configure(bg=BG)

        self.sources = []
        self.results = []
        self.visible_results = []
        self.value_columns = []

        self.summary_var = tk.StringVar(value="Add at least two XML files to compare.")
        self.mode_var = tk.StringVar(value="Across all files")
        self.filter_var = tk.StringVar(value="Differences only")
        self.search_var = tk.StringVar()
        self.baseline_var = tk.StringVar(value="")
        self.ignore_whitespace_var = tk.BooleanVar(value=True)
        self.include_attributes_var = tk.BooleanVar(value=True)

        self.search_job = None

        self._build()

    def _build(self):
        self._configure_styles()
        self.search_var.trace_add("write", self._schedule_refresh)

        header = tk.Frame(self.window, bg=BG)
        header.pack(fill="x", padx=12, pady=12)

        tk.Label(
            header,
            text="XML Multi-Compare",
            font=FONT_TITLE,
            fg=TEXT,
            bg=BG,
        ).pack(side="left")

        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right")

        action_specs = [
            ("Use Current XML", self.use_current_xml),
            ("Add XML Files", self.add_xml_files),
            ("Remove Selected", self.remove_selected_source),
            ("Clear Files", self.clear_sources),
            ("Compare", self.compare_xmls),
            ("Export CSV", self.export_results),
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

        controls = tk.Frame(self.window, bg=BG)
        controls.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(controls, text="Search", font=FONT, fg=MUTED, bg=BG).pack(side="left", padx=(0, 8))
        tk.Entry(
            controls,
            textvariable=self.search_var,
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            width=34,
            font=FONT,
        ).pack(side="left", padx=(0, 12), ipady=4)

        tk.Label(controls, text="Mode", font=FONT, fg=MUTED, bg=BG).pack(side="left", padx=(0, 8))
        mode_combo = ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            state="readonly",
            values=["Across all files", "Against baseline"],
            width=18,
            style="Dark.TCombobox",
        )
        mode_combo.pack(side="left", padx=(0, 12))
        mode_combo.bind("<<ComboboxSelected>>", lambda _event: self.compare_xmls())

        tk.Label(controls, text="Baseline", font=FONT, fg=MUTED, bg=BG).pack(side="left", padx=(0, 8))
        self.baseline_combo = ttk.Combobox(
            controls,
            textvariable=self.baseline_var,
            state="readonly",
            values=[],
            width=28,
            style="Dark.TCombobox",
        )
        self.baseline_combo.pack(side="left", padx=(0, 12))
        self.baseline_combo.bind("<<ComboboxSelected>>", lambda _event: self.compare_xmls())

        tk.Label(controls, text="View", font=FONT, fg=MUTED, bg=BG).pack(side="left", padx=(0, 8))
        view_combo = ttk.Combobox(
            controls,
            textvariable=self.filter_var,
            state="readonly",
            values=[
                "Summary view",
                "Differences only",
                "All results",
                "Missing only",
                "Same only",
                "Changed only",
            ],
            width=18,
            style="Dark.TCombobox",
        )
        view_combo.pack(side="left", padx=(0, 12))
        view_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_view_changed())

        tk.Checkbutton(
            controls,
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
            controls,
            text="Compare attributes",
            variable=self.include_attributes_var,
            bg=BG,
            fg=TEXT,
            activebackground=BG,
            activeforeground=TEXT,
            selectcolor=CARD_BG,
            font=FONT,
        ).pack(side="left")

        mid = tk.Frame(self.window, bg=BG)
        mid.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        mid.grid_columnconfigure(0, weight=0)
        mid.grid_columnconfigure(1, weight=1)
        mid.grid_rowconfigure(0, weight=1)

        left_panel = tk.Frame(mid, bg=CARD_BG, bd=1, highlightbackground=BORDER, highlightthickness=1)
        left_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        left_panel.grid_rowconfigure(1, weight=1)

        tk.Label(
            left_panel,
            text="Loaded XML Files",
            font=FONT_BOLD,
            fg=TEXT,
            bg=CARD_BG,
            anchor="w",
            padx=10,
            pady=10,
        ).grid(row=0, column=0, sticky="ew")

        self.source_listbox = tk.Listbox(
            left_panel,
            width=42,
            bg=ENTRY_BG,
            fg=TEXT,
            selectbackground=HIGHLIGHT_ROW,
            selectforeground=TEXT,
            relief="flat",
            font=FONT,
            activestyle="none",
        )
        self.source_listbox.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))

        list_scroll = tk.Scrollbar(left_panel, orient="vertical", command=self.source_listbox.yview)
        list_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(0, 10))
        self.source_listbox.configure(yscrollcommand=list_scroll.set)

        right_panel = tk.Frame(mid, bg=BG)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        summary_bar = tk.Frame(right_panel, bg=PANEL_BG)
        summary_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
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

        results_outer = tk.Frame(right_panel, bg=BG)
        results_outer.grid(row=1, column=0, sticky="nsew")
        results_outer.grid_rowconfigure(0, weight=1)
        results_outer.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(results_outer, columns=("status", "path", "consensus", "different_files"), show="headings", style="Compare.Treeview")
        self.tree.heading("status", text="Status")
        self.tree.heading("path", text="Path")
        self.tree.heading("consensus", text="Consensus / Baseline")
        self.tree.heading("different_files", text="Different Files")
        self.tree.column("status", width=160, anchor="w")
        self.tree.column("path", width=360, anchor="w")
        self.tree.column("consensus", width=220, anchor="w")
        self.tree.column("different_files", width=220, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(results_outer, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(results_outer, orient="horizontal", command=self.tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self._refresh_baseline_choices()

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

    def _schedule_refresh(self, *_args):
        if self.search_job is not None:
            self.window.after_cancel(self.search_job)
        self.search_job = self.window.after(120, self._populate_results)

    def _on_view_changed(self):
        self._rebuild_result_columns()
        self._populate_results()
        if self.results:
            self._update_summary(self.mode_var.get().strip())

    def _is_summary_view(self):
        return self.filter_var.get().strip() == "Summary view"

    def use_current_xml(self):
        xml_text = self.app.get_current_xml_text()
        if not xml_text:
            messagebox.showwarning("No XML", "Open an XML file in the editor first.")
            return

        source_path = self.app.get_current_xml_display_name()
        self._add_source(
            display_name=self._make_unique_display_name(self._display_name_from_path(source_path)),
            xml_text=xml_text,
            source_path=source_path,
        )
        self.summary_var.set("Current XML added to the multi-compare list.")

    def add_xml_files(self):
        file_paths = filedialog.askopenfilenames(
            parent=self.window,
            title="Add XML Files",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
        )
        if not file_paths:
            return

        added = 0
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    xml_text = handle.read()
            except Exception as exc:
                messagebox.showerror("Open error", f"Could not read XML file.\n\n{file_path}\n\n{exc}")
                continue

            self._add_source(
                display_name=self._make_unique_display_name(self._display_name_from_path(file_path)),
                xml_text=xml_text,
                source_path=file_path,
            )
            added += 1

        if added:
            self.summary_var.set(f"Added {added} XML file(s) to the compare list.")

    def _display_name_from_path(self, source_path):
        if not source_path:
            return "XML"
        base = os.path.basename(str(source_path).strip())
        return base or str(source_path)

    def _add_source(self, display_name, xml_text, source_path):
        self.sources.append({
            "name": display_name,
            "xml_text": xml_text,
            "path": source_path,
        })
        self.source_listbox.insert("end", display_name)
        self._refresh_baseline_choices()

    def _make_unique_display_name(self, name):
        base = name or "XML"
        existing = {item["name"] for item in self.sources}
        if base not in existing:
            return base
        index = 2
        while f"{base} ({index})" in existing:
            index += 1
        return f"{base} ({index})"

    def remove_selected_source(self):
        selection = self.source_listbox.curselection()
        if not selection:
            messagebox.showwarning("No selection", "Select a file from the list first.")
            return

        index = selection[0]
        del self.sources[index]
        self.source_listbox.delete(index)
        self._refresh_baseline_choices()
        self.results = []
        self.visible_results = []
        self._rebuild_result_columns()
        self._populate_results()
        self.summary_var.set("Removed the selected XML file.")

    def clear_sources(self):
        self.sources.clear()
        self.results.clear()
        self.visible_results.clear()
        self.source_listbox.delete(0, "end")
        self._refresh_baseline_choices()
        self._rebuild_result_columns()
        self._populate_results()
        self.summary_var.set("Cleared all XML sources.")

    def _refresh_baseline_choices(self):
        names = [item["name"] for item in self.sources]
        self.baseline_combo["values"] = names
        if names:
            if self.baseline_var.get() not in names:
                self.baseline_var.set(names[0])
        else:
            self.baseline_var.set("")

    def compare_xmls(self):
        if len(self.sources) < 2:
            messagebox.showwarning("Not enough XML files", "Add at least two XML files to compare.")
            return

        parsed_maps = []
        parse_errors = []
        for source in self.sources:
            try:
                parsed_maps.append(self._xml_to_flat_map(source["xml_text"]))
            except Exception as exc:
                parse_errors.append(f"{source['name']}: {exc}")

        if parse_errors:
            messagebox.showerror("Parse error", "Some XML files could not be parsed:\n\n" + "\n".join(parse_errors))
            return

        baseline_index = self._get_baseline_index()
        mode = self.mode_var.get().strip()

        union_paths = sorted({path for mapping in parsed_maps for path in mapping.keys()}, key=self._path_sort_key)
        results = []

        for path in union_paths:
            values = [mapping.get(path, MISSING) for mapping in parsed_maps]
            normalized_values = [self._normalize_value(value) for value in values]

            if mode == "Against baseline":
                status, differing_names, consensus_text = self._classify_against_baseline(values, normalized_values, baseline_index)
            else:
                status, differing_names, consensus_text = self._classify_across_all(values, normalized_values)

            results.append({
                "status": status,
                "path": path,
                "consensus": consensus_text,
                "different_files": differing_names,
                "values": values,
            })

        self.results = results
        self._rebuild_result_columns()
        self._populate_results()
        self._update_summary(mode)

    def _xml_to_flat_map(self, xml_text):
        root = ET.fromstring(xml_text)
        result = {}

        def walk(element, path):
            if self.include_attributes_var.get():
                for attr_name, attr_value in sorted(element.attrib.items()):
                    result[f"{path}/@{attr_name}"] = attr_value

            children = list(element)
            text_value = element.text or ""

            if children:
                if text_value.strip() != "":
                    result[f"{path}/#text"] = text_value

                tag_counts = {}
                for child in children:
                    tag_counts[child.tag] = tag_counts.get(child.tag, 0) + 1

                seen = {}
                for child in children:
                    seen[child.tag] = seen.get(child.tag, 0) + 1
                    child_path = f"{path}/{child.tag}[{seen[child.tag]}]"
                    walk(child, child_path)
            else:
                result[path] = text_value

        walk(root, f"/{root.tag}[1]")
        return result

    def _normalize_value(self, value):
        if value is MISSING:
            return MISSING
        if value is None:
            value = ""
        text = str(value)
        if self.ignore_whitespace_var.get():
            return text.strip()
        return text

    def _classify_across_all(self, values, normalized_values):
        present = [value for value in normalized_values if value is not MISSING]
        if len(present) != len(values):
            differing = [self.sources[index]["name"] for index, value in enumerate(normalized_values) if value is MISSING]
            consensus = self._build_consensus_text(present)
            return STATUS_MISSING, ", ".join(differing), consensus

        first = present[0] if present else ""
        if all(value == first for value in present):
            return STATUS_SAME_ALL, "", self._safe_preview(first)

        consensus = self._build_consensus_text(present)
        outliers = self._find_outliers(normalized_values)
        return STATUS_DIFFERENT, ", ".join(outliers), consensus

    def _classify_against_baseline(self, values, normalized_values, baseline_index):
        baseline_value = normalized_values[baseline_index]
        baseline_name = self.sources[baseline_index]["name"]
        compare_names = []
        has_missing = False
        has_difference = False

        for index, value in enumerate(normalized_values):
            if index == baseline_index:
                continue
            if value is MISSING or baseline_value is MISSING:
                has_missing = True
                compare_names.append(self.sources[index]["name"])
            elif value != baseline_value:
                has_difference = True
                compare_names.append(self.sources[index]["name"])

        if has_missing:
            return STATUS_MISSING_BASELINE, ", ".join(compare_names), f"{baseline_name}: {self._safe_preview(baseline_value)}"
        if has_difference:
            return STATUS_DIFF_BASELINE, ", ".join(compare_names), f"{baseline_name}: {self._safe_preview(baseline_value)}"
        return STATUS_SAME_BASELINE, "", f"{baseline_name}: {self._safe_preview(baseline_value)}"

    def _find_outliers(self, normalized_values):
        counts = {}
        for value in normalized_values:
            counts[value] = counts.get(value, 0) + 1
        common_value = max(counts.items(), key=lambda item: item[1])[0]
        return [self.sources[index]["name"] for index, value in enumerate(normalized_values) if value != common_value]

    def _build_consensus_text(self, present_values):
        if not present_values:
            return "<missing>"
        counts = {}
        for value in present_values:
            counts[value] = counts.get(value, 0) + 1
        common_value, common_count = max(counts.items(), key=lambda item: item[1])
        if len(counts) == 1:
            return self._safe_preview(common_value)
        return f"{self._safe_preview(common_value)} ({common_count}/{len(present_values)})"

    def _get_baseline_index(self):
        baseline_name = self.baseline_var.get().strip()
        for index, source in enumerate(self.sources):
            if source["name"] == baseline_name:
                return index
        return 0

    def _rebuild_result_columns(self):
        summary_view = self._is_summary_view()
        fixed_columns = ["status", "path", "consensus", "different_files"]
        if summary_view:
            self.value_columns = []
            all_columns = fixed_columns + ["difference_count"]
        else:
            self.value_columns = [f"value_{index}" for index in range(len(self.sources))]
            all_columns = fixed_columns + self.value_columns

        self.tree.configure(columns=all_columns)

        self.tree.heading("status", text="Status")
        self.tree.heading("path", text="Path")
        self.tree.heading("consensus", text="Consensus / Baseline")
        self.tree.heading("different_files", text="Different Files")
        self.tree.column("status", width=170, anchor="w")
        self.tree.column("path", width=420, anchor="w")
        self.tree.column("consensus", width=260, anchor="w")
        self.tree.column("different_files", width=260, anchor="w")

        if summary_view:
            self.tree.heading("difference_count", text="Affected Files")
            self.tree.column("difference_count", width=120, anchor="center")
        else:
            for index, column_name in enumerate(self.value_columns):
                heading = self.sources[index]["name"]
                self.tree.heading(column_name, text=heading)
                self.tree.column(column_name, width=max(180, min(320, len(heading) * 10)), anchor="w")

    def _populate_results(self):
        self.search_job = None
        for item in self.tree.get_children():
            self.tree.delete(item)

        visible = []
        search_text = self.search_var.get().strip().lower()
        active_filter = self.filter_var.get().strip()
        summary_view = self._is_summary_view()

        for row in self.results:
            if not self._row_matches_filter(row, active_filter):
                continue
            if search_text and not self._row_matches_search(row, search_text):
                continue

            if summary_view:
                difference_count = self._difference_count(row)
                values = [
                    row["status"],
                    row["path"],
                    row["consensus"],
                    row["different_files"],
                    difference_count,
                ]
            else:
                values = [
                    row["status"],
                    row["path"],
                    row["consensus"],
                    row["different_files"],
                ] + [self._display_value(value) for value in row["values"]]
            self.tree.insert("", "end", values=values)
            visible.append(row)

        self.visible_results = visible

    def _difference_count(self, row):
        differing = [name.strip() for name in row["different_files"].split(",") if name.strip()]
        return len(differing)

    def _row_matches_filter(self, row, active_filter):
        status = row["status"]
        if active_filter == "All results":
            return True
        if active_filter == "Summary view":
            return status not in (STATUS_SAME_ALL, STATUS_SAME_BASELINE)
        if active_filter == "Differences only":
            return status not in (STATUS_SAME_ALL, STATUS_SAME_BASELINE)
        if active_filter == "Missing only":
            return status in (STATUS_MISSING, STATUS_MISSING_BASELINE)
        if active_filter == "Same only":
            return status in (STATUS_SAME_ALL, STATUS_SAME_BASELINE)
        if active_filter == "Changed only":
            return status in (STATUS_DIFFERENT, STATUS_DIFF_BASELINE)
        return True

    def _row_matches_search(self, row, search_text):
        haystack_parts = [row["status"], row["path"], row["consensus"], row["different_files"]]
        haystack_parts.extend(self._display_value(value) for value in row["values"])
        haystack = " ".join(part.lower() for part in haystack_parts)
        return search_text in haystack

    def _update_summary(self, mode):
        total = len(self.results)
        visible = len(self.visible_results) if self.visible_results else len(self.results)
        same_count = sum(1 for row in self.results if row["status"] in (STATUS_SAME_ALL, STATUS_SAME_BASELINE))
        changed_count = sum(1 for row in self.results if row["status"] in (STATUS_DIFFERENT, STATUS_DIFF_BASELINE))
        missing_count = sum(1 for row in self.results if row["status"] in (STATUS_MISSING, STATUS_MISSING_BASELINE))
        summary_rows = changed_count + missing_count
        self.summary_var.set(
            f"Mode: {mode} | Files: {len(self.sources)} | Paths: {total} | Same: {same_count} | Different: {changed_count} | Missing: {missing_count} | Summary rows: {summary_rows} | Showing: {visible}"
        )

    def export_results(self):
        if not self.visible_results:
            messagebox.showwarning("No results", "Run a comparison first and make sure there are rows to export.")
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Export Comparison Results",
            defaultextension=".csv",
            initialfile="xml_multi_compare_results.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                header = ["Status", "Path", "Consensus / Baseline", "Different Files"] + [source["name"] for source in self.sources]
                writer.writerow(header)
                for row in self.visible_results:
                    writer.writerow([
                        row["status"],
                        row["path"],
                        row["consensus"],
                        row["different_files"],
                        *[self._display_value(value) for value in row["values"]],
                    ])
        except Exception as exc:
            messagebox.showerror("Export error", f"Could not export CSV.\n\n{exc}")
            return

        messagebox.showinfo("Exported", f"Results exported to:\n{file_path}")

    def _display_value(self, value):
        if value is MISSING:
            return "<missing>"
        return self._safe_preview(value)

    def _safe_preview(self, value):
        if value is MISSING:
            return "<missing>"
        text = "" if value is None else str(value)
        text = text.replace("\n", " ").replace("\r", " ")
        text = " ".join(text.split()) if self.ignore_whitespace_var.get() else text
        if text == "":
            return "<empty>"
        if len(text) > 120:
            return text[:117] + "..."
        return text

    def _shorten_heading(self, heading):
        return heading

    def _path_sort_key(self, path):
        parts = []
        for chunk in path.replace("]", "").split("/"):
            if not chunk:
                continue
            if "[" in chunk:
                name, index = chunk.split("[", 1)
                try:
                    index_num = int(index)
                except Exception:
                    index_num = 0
                parts.append((name.lower(), index_num))
            else:
                parts.append((chunk.lower(), 0))
        return parts


