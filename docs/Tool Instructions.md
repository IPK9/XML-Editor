### JSON Editor – Instructions

Purpose

The JSON Editor is used to create, edit, save, and load JSON replacement configurations for the XML Editor. These replacement rules can then be applied to the currently open XML file through the Auto Replace function.



How to open it

1\. Open the main XML Editor.

2\. Click the “JSON Editor” button on the top bar.



What the JSON Editor does

The JSON Editor allows you to build a list of replacement rules.

Each rule can contain:

\- Path: the XML path to target

\- Attribute: optional, if you want to replace an attribute instead of text

\- Type: the value type to use

\- Value: the replacement value



Available value types

\- auto

\- string

\- int

\- float

\- bool

\- null



Main buttons

\- Load JSON: opens an existing JSON config file

\- Save JSON: saves the current config to the current file

\- Save JSON As: saves the current config to a new file

\- New Element: adds a new replacement row

\- Delete Element: removes the currently selected replacement row

\- Load Recent: loads a recently used config from the Recent configs dropdown

\- Use Selected XML Path: inserts the currently selected XML path into the selected JSON row

\- Pull XML Value: inserts the currently selected XML path and current XML value into the selected JSON row



How to create a replacement rule manually

1\. Click “New Element”.

2\. Select the new row.

3\. Enter the XML path in the Path field.

4\. If needed, enter an attribute name in the Attribute field.

5\. Choose the Type.

6\. Enter the replacement Value.

7\. Repeat for any additional rules.

8\. Click “Save JSON” or “Save JSON As”.



How to build rules from the XML Editor

1\. Open an XML file in the main XML Editor.

2\. In the XML Editor, click the field or attribute you want to target.

3\. Open the JSON Editor and select the row you want to fill.

4\. Click:

&#x20;  - “Use Selected XML Path” to insert only the path

&#x20;  - “Pull XML Value” to insert the path and the current value

5\. Adjust the type or value if needed.



How matching works

When you select a row in the JSON Editor, the XML Editor highlights matching XML fields and shows how many matches were found for that rule.



How to use the config

1\. Create or load a JSON config in the JSON Editor.

2\. Save it if needed.

3\. Return to the main XML Editor.

4\. Click “Auto Replace”.

5\. Review the preview of changes.

6\. Apply the changes if they are correct.



Recent configs

The JSON Editor keeps a list of recent config file paths.

Use the Recent configs dropdown and click “Load Recent” to reopen one quickly.



Important notes

\- A rule without a Path will be ignored when saving.

\- If Attribute is blank, the rule targets element text.

\- If Attribute is filled in, the rule targets that attribute on the matched element.

\- “Save JSON” saves to the currently loaded config path. If none exists yet, it behaves like “Save JSON As”.

\- The JSON config is stored as a top-level object containing a “replacements” list.



Typical workflow

1\. Open XML in the XML Editor

2\. Select the XML field you want

3\. Open JSON Editor

4\. Add or select a rule

5\. Pull the XML path/value into the rule

6\. Save the JSON config

7\. Run Auto Replace from the main XML Editor



### 

### XML Comparison – Instructions

Purpose

XML Comparison is used to compare two XML files side by side.

It is designed to help identify:

\- changed values

\- missing nodes

\- added nodes

\- structurally similar nodes

\- likely equivalent nodes when XML structure differs



How to open it

1\. Open the main XML Editor.

2\. Click the “Tools” button.

3\. Select “XML Comparison”.



What the tool does

The tool compares two XML files:

\- Left XML

\- Right XML



It can compare them using:

\- exact path matching

\- heuristic remapping for likely equivalent nodes



This makes it useful both for:

\- strict side-by-side XML validation

\- comparing XMLs where the structure has shifted slightly



Main buttons

\- Use Current XML as Left: uses the XML currently open in the main XML Editor as the left-hand file

\- Browse Left XML: choose the left XML file manually

\- Browse Right XML: choose the right XML file manually

\- Compare: runs the comparison



Main options

\- Heuristic remapping:

&#x20; When enabled, the tool tries to find likely equivalent nodes even if the exact XML path is different



\- Filter:

&#x20; Controls which result types are shown



Available filters typically include:

\- All results

\- Changed only

\- Heuristic only

\- Missing only

\- Same only



Result types

The comparison tool may show results such as:

\- Same

\- Changed

\- Changed (Heuristic)

\- Heuristic Match

\- Only in Left

\- Only in Right



What those mean

\- Same:

&#x20; The node exists in both XML files and matches



\- Changed:

&#x20; The node exists in both XML files at the same logical location, but the value differs



\- Changed (Heuristic):

&#x20; The tool believes two nodes are equivalent even though they are not matched purely by exact path, and their values differ



\- Heuristic Match:

&#x20; The tool believes two nodes are equivalent even though their paths or surrounding structure differ



\- Only in Left:

&#x20; The node exists only in the left XML



\- Only in Right:

&#x20; The node exists only in the right XML



Confidence

When heuristic remapping is used, the tool may show a Confidence value.

This indicates how strongly the tool believes two nodes correspond to one another.



Higher confidence means:

\- stronger structural similarity

\- stronger path similarity

\- stronger contextual similarity



How to use it

1\. Open XML Comparison from the Tools menu.

2\. Choose the files:

&#x20;  - use “Use Current XML as Left” if you already have one open

&#x20;  - browse for the right XML

&#x20;  - optionally browse both files manually

3\. Enable or disable heuristic remapping depending on how strict you want the comparison to be

4\. Click “Compare”

5\. Review the results table

6\. Use the filter dropdown to focus on the results you care about most



Typical workflow

1\. Open your source XML in the main XML Editor

2\. Open XML Comparison

3\. Use Current XML as Left

4\. Browse for a second XML as Right

5\. Run comparison

6\. Review:

&#x20;  - Changed values

&#x20;  - Left-only nodes

&#x20;  - Right-only nodes

&#x20;  - Heuristic matches



When to use heuristic remapping

Heuristic remapping is useful when:

\- the XML structure has changed

\- a value has moved deeper into a different branch

\- repeated blocks have shifted

\- the same logical data exists under a slightly different path



When to turn heuristic remapping off

Turn it off when you want:

\- strict exact-path comparison

\- very precise one-to-one validation

\- no structural interpretation



Search and filtering

Use the filter controls to reduce noise and focus on:

\- only changed fields

\- only heuristic results

\- only missing nodes

\- only identical values



Best use cases

\- comparing two versions of the same XML payload

\- validating generated XML output against a source

\- spotting differences after editing or transformation

\- checking whether equivalent values still exist after structure changes

\- investigating why two XMLs are not matching exactly



Important notes

\- The standard XML Comparison tool is for two-file comparison only

\- For comparing many XML files at once, use XML Multi-Compare instead

\- Heuristic matching is helpful, but it is still an interpretation layer and should be reviewed carefully on complex XMLs

### 

### XML Generator – Instructions

Purpose

XML Generator is used to turn an existing XML file into a reusable generator.

It lets you:

\- load an XML file

\- automatically create editable fields from that XML

\- save the generator to a JSON file

\- load the generator again later

\- generate a new XML output file from the stored structure and field values



How to open it

1\. Open the main XML Editor.

2\. Click “Tools”.

3\. Select “XML Generator”.



What the tool does

When XML is loaded into the tool, it reads the XML structure and creates generator fields from:

\- attributes

\- text values



Each generated field stores:

\- Label

\- Path

\- Attribute

\- Type

\- Value



Imported XML values are handled as strings by default unless you deliberately change the type. The generator also stores an XML snapshot internally so it can rebuild and generate later.



Main buttons

\- Use Current XML

&#x20; Uses the XML currently open in the main XML Editor as the source for the generator.



\- Browse XML

&#x20; Loads an XML file from disk and builds the generator from it.



\- Load Generator

&#x20; Opens a previously saved generator JSON file.



\- Save Generator

&#x20; Saves the current generator to its current JSON file path.



\- Save Generator As

&#x20; Saves the current generator to a new JSON file.



\- Generate XML

&#x20; Generates a new XML file by applying the current generator field values to the stored XML snapshot. In the current version, this behaves the same as Generate XML As and prompts for an output file.



\- Generate XML As

&#x20; Prompts for an output XML file path and writes a generated XML file there.



Other controls

\- Generator Name

&#x20; Lets you name the generator. This name is saved into the generator JSON.



\- Search Fields

&#x20; Filters the visible generator fields by matching text in the label, path, attribute, type, or value.



\- Recent Generators

&#x20; Lets you quickly reload recently used generator files.



\- Load Recent

&#x20; Loads the selected recent generator.



\- Add From Current XML Selection

&#x20; Adds a field using the currently selected item from the main XML Editor.



\- Add Blank Field

&#x20; Adds a new empty field manually.



Main layout

The XML Generator has:

\- a field list on the left

\- a selected field editor on the right



The field list shows:

\- Label

\- Path

\- Attribute

\- Type

\- Value



The selected field editor lets you edit:

\- Label

\- Path

\- Attribute

\- Type

\- Value



There are also buttons for:

\- Apply Changes

\- Delete Field

\- Rebuild From Snapshot



How to build a generator from XML

Option 1 – Use the current XML

1\. Open an XML file in the main XML Editor.

2\. Open XML Generator.

3\. Click “Use Current XML”.



Option 2 – Browse for XML

1\. Open XML Generator.

2\. Click “Browse XML”.

3\. Select the XML file you want to use.



The tool will then:

\- parse the XML

\- collect fields from attributes and text values

\- store the original XML as an internal snapshot

\- populate the field list automatically



How to edit fields

1\. Select a field in the left-hand list.

2\. Update the field values on the right:

&#x20;  - Label

&#x20;  - Path

&#x20;  - Attribute

&#x20;  - Type

&#x20;  - Value

3\. Click “Apply Changes”.



You can also:

\- click “Delete Field” to remove the selected field

\- click “Add Blank Field” to create a new one manually

\- click “Add From Current XML Selection” to add a field from whatever is selected in the main XML Editor



How to save a generator

1\. Build or load a generator first.

2\. Enter or adjust the Generator Name if needed.

3\. Click:

&#x20;  - “Save Generator” to save to the current generator file

&#x20;  - “Save Generator As” to save to a new JSON file



The saved generator contains:

\- generator\_name

\- source\_xml\_path

\- xml\_snapshot

\- fields

How to load a generator

1\. Open XML Generator.

2\. Click “Load Generator”.

3\. Select a saved generator JSON file.



Or:

1\. Use the Recent Generators dropdown.

2\. Click “Load Recent”.



How to generate XML

1\. Load or build a generator.

2\. Edit the field values you want.

3\. Click “Generate XML” or “Generate XML As”.

4\. Choose where to save the output XML file.



The tool will:

\- load the stored XML snapshot

\- find matching paths

\- apply the current field values

\- write the generated XML file to disk



How value types work

For generation:

\- if the field type is string or auto, the value is written back as text

\- if the field type is int, float, bool, or null, the value is converted before being written



This means text formatting is preserved unless you explicitly choose a typed conversion.



Rebuild From Snapshot

“Rebuild From Snapshot” regenerates the field list from the stored XML snapshot inside the generator.

Use this if:

\- you want to restore the original auto-built field set

\- you want to discard manual field layout changes and rebuild from the stored XML structure



Typical workflow

1\. Open XML Generator

2\. Use Current XML or Browse XML

3\. Review and edit generated fields

4\. Save Generator

5\. Load the generator later if needed

6\. Generate XML to a new output file



Important notes

\- You must load or build a generator before saving it.

\- You must load or build a generator before generating XML.

\- The tool generates output from the stored XML snapshot, not from the currently open XML unless you rebuild the generator from it.

\- Blank paths are ignored during generation.

\- If a path cannot be found in the stored XML snapshot, that field is skipped.



### XML Multi-Compare – Instructions

Purpose

XML Multi-Compare is used to compare multiple XML files in one session.

It is designed to help identify:

\- differences across a group of XML files

\- missing values or paths

\- files that do not match the rest

\- baseline differences against a chosen XML



How to open it

1\. Open the main XML Editor.

2\. Click the “Tools” button.

3\. Select “XML Multi-Compare”.



What the tool does

The tool loads multiple XML files and compares them by flattened path/value pairs.



It can compare in two main ways:

\- Across all files

\- Against a selected baseline file



Main buttons

\- Use Current XML: adds the XML currently open in the main XML Editor

\- Add XML Files: browse and add one or more XML files

\- Remove Selected: removes the selected file from the loaded list

\- Clear Files: removes all loaded XML files

\- Compare: runs the comparison

\- Export CSV: exports the currently visible results to CSV



Comparison modes

\- Across all files

&#x20; Compares every loaded XML against the group as a whole



\- Against baseline

&#x20; Compares every loaded XML against the file selected in the baseline dropdown



Baseline selector

The baseline dropdown lets you choose which loaded XML file should act as the reference file when using baseline comparison mode.



Loaded file names

The tool displays XML file names rather than full file paths.

If duplicate file names are loaded, numbered suffixes are added automatically.



Result filters

The filter dropdown lets you control which result types are shown.



Available filters:

\- All results

\- Differences only

\- Missing only

\- Same only

\- Changed only

\- Summary view



Result types

Depending on the comparison mode, the tool can show results such as:

\- Same Across All

\- Different

\- Missing in Some

\- Same as Baseline

\- Different from Baseline

\- Missing vs Baseline



How to use it

1\. Open XML Multi-Compare from the Tools menu.

2\. Add XML files using:

&#x20;  - “Use Current XML”

&#x20;  - “Add XML Files”

3\. Choose the comparison mode:

&#x20;  - Across all files

&#x20;  - Against baseline

4\. If using baseline mode, select the baseline XML from the dropdown.

5\. Click “Compare”.

6\. Review the results.

7\. Use the filter dropdown if needed.

8\. Use the search box to find specific paths or values.

9\. Export the results to CSV if required.



Search

The search box filters visible results using path and value text.

This is useful for finding specific fields such as:

\- money

\- status

\- policyNumber

\- id

\- customerName



Summary view

Summary view gives a cleaner, higher-level overview of differences.

It is useful when you want to see:

\- which paths differ

\- how many files are affected

\- which files are different

without viewing every file column in full detail



Exporting

Click “Export CSV” to save the currently visible results to a CSV file.

This export follows the active filter and search view.



Typical workflow

1\. Add several XML files

2\. Run comparison

3\. Switch to “Differences only” or “Summary view”

4\. Search for important paths if needed

5\. Export to CSV if you want a report



Important notes

\- XML Multi-Compare currently uses path/value-based comparison

\- It does not yet use heuristic remapping

\- It is best for checking consistency across multiple similarly structured XML files

\- For detailed two-file comparison, use the standard XML Comparison tool instead



Best use cases

\- checking batches of generated XML files

\- validating repeated outputs

\- spotting outlier XMLs

\- confirming one XML matches the rest

\- comparing multiple versions of the same payload

