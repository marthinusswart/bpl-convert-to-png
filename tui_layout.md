# Amiga TUI Layout Specifications & Element Sizing

This document outlines the current structural hierarchy of the Amiga TUI, along with the element names (IDs/classes) and their exact sizing in **character columns (widths)** and **lines (heights)**.

---

## 🗺️ TUI Visual Blueprint

Below is the layout map as rendered by Textual. Dimensions are expressed as `[Width x Height]` in character cells:

```text
+-----------------------------------------------------------------------------------------------------------------------+
|                                              HEADER (Title & Subtitle)                                                |
+-----------------------------------------------------------------------------------------------------------------------+
|                                              #main-layout [width: 100%, height: 1fr]                                  |
| +------------------------------------+------------------------------------------------------------------------------+ |
| | #sidebar                           | #content (VerticalScroll) [width: 1fr, height: 1fr]                          | |
| | [width: 36, height: 1fr]           |                                                                              | |
| |                                    |  Label(" Conversion Options")                                                | |
| |  Label(" BPL Files")               |                                                                              | |
| |  ListView (self.file_list)         |  #columns-container [width: 1fr, height: 1fr, min-height: 42]                | |
| |   - height: 16                     |  +--------------------+--------------------+-------------------------------+ | |
| |                                    |  | #col1              | #col2              | #col3                         | | |
| |  Label(" PAL Files")               |  | [width: 60, H:100%]| [width: 60, H:100%]| [width: 1fr, height: 100%]    | | |
| |  ListView (self.pal_list)          |  |                    |                    |                               || |   - height: 8                      |  | FormGroup          | FormGroup          | #buttons-row [height: 3]      | | |
| |                                    |  | (border_title)     | (border_title)     |  - Analyze & Convert Buttons  | | |
| |  Label(" File Details")            |  | - Selected BPL     | - Color Planes     |                               | | |
| |  Label (self.info_label)           |  | - Select PAL       | - Palette Bits     | Label(" Analysis Details")    | | |
| |   - height: 1fr                    |  |                    | - Interleaved      |                               | | |
| |                                    |  | FormGroup          | - Has Mask         | #analysis-log                 | | |
| |                                    |  | (border_title)     |                    | [width: 1fr, height: 1fr]     | | |
| |                                    |  | - Image Width      | FormGroup          |  (occupies remaining H)       | | |
| |                                    |  | - Image Height     | (border_title)     |                               | | |
| |                                    |  |                    | - PNG Scale        |                               | | |
| |                                    |  | FormGroup          | - Draw Grid        |                               | | |
| |                                    |  | (border_title)     | - Sprite Width     |                               | | |
| |                                    |  | - Output Folder    | - Sprite Height    |                               | | |
| |                                    |  | - Mask PNG         |                    |                               | | |
| |                                    |  +--------------------+--------------------+-------------------------------+ | |
| +------------------------------------+------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------------------------------+
|                                              #logs-container [width: 100%, height: 14]                                |
|  Label(" Execution Logs")                                                                                             |
|  RichLog (self.execution_log)                                                                                         |
+-----------------------------------------------------------------------------------------------------------------------+
|                                                       FOOTER                                                          |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

## 📊 Detailed Sizing Specifications

Textual layouts are fully text-cell based (no pixels). Here are the exact constraints:

### 1. Left Sidebar Panel
* **Container**: `Vertical(id="sidebar")`
  * **Width**: Fixed `36` character cells (`width: 36;`).
  * **Height**: `1fr` (fills the vertical space of the screen).
* **Inner Components**:
  * **BPL List (`self.file_list`, ID: `#bpl-list`)**: Height is `16` cells.
  * **PAL List (`self.pal_list`)**: Height is `8` cells.
  * **Details Panel (`self.info_label`, ID: `#info-panel`)**: Height is `1fr` and **Width is `1fr`** (occupies 100% of available sidebar width, perfectly aligning borders with BPL and PAL list views!).


---

### 2. Right Options Panel
* **Container**: `VerticalScroll(id="content")`
  * **Width**: `1fr` (takes up all remaining width left by the sidebar, which is `WindowWidth - 36`).
  * **Height**: `1fr` (fills the remaining screen height above the bottom execution log).

---

### 3. Sizing Columns in the Grid
* **Main Grid Container**: `Horizontal(id="columns-container")`
  * **Width**: `1fr` (fills `#content`).
  * **Height**: Stretches dynamically to fill the available height (`height: 1fr;`), with a minimum of `42` lines (`min-height: 42;`) so form inputs never overflow or get squished.
* **Column 1 (`#col1`) & Column 2 (`#col2`)**:
  * **Width**: **Fixed `60` cells** (`width: 60;`).
  * **Height**: Stretches to `100%` of parent height.
  * **Column 1 Details**: Features 3 form groups (`FormGroup` containers), each constrained to a **Fixed Max-Height of `12` rows** (`max-height: 12;`). Titles are natively integrated into the top border outlines (`border_title`).
  * **Column 2 Details**: Features 2 form groups (`FormGroup` containers), each constrained to a **Fixed Max-Height of `20` rows** (`max-height: 20;`). Titles are natively integrated into the top border outlines (`border_title`).
  * **Why this works beautifully**: At a fixed `60` cells, Column 1 and Column 2 remain perfectly constant and never resize horizontally. Column 3 (`#col3`) has `width: 1fr;` which receives all leftover terminal window width (`WindowWidth - 36 - 120`), and dynamically grows and shrinks when you resize the window! window!

* **Column 3 (`#col3`)**:
  * **Width**: `1fr` (receives whatever width is left over: `(WindowWidth - 36) - 120`).
  * **Height**: Stretches to `100%` of parent height.
* **Column 3 Inner Components**:
  * **Quick Actions Row (`#buttons-row`)**: Fixed `3` cells high (`height: 3;`). Contains both buttons next to one another.
  * **Analysis Panel (`#analysis-log`)**: `height: 1fr;`. It expands dynamically to occupy all remaining vertical space inside Column 3 (approx `37` lines).

---

## 🛠️ Suggested Layout Fix (For Web-scale expectations)

If you are thinking of the units as typical CSS web layout values (where `150px` to `200px` are standard sidebar widths), they translate to roughly **`45` to `60` character cells** in terminal layouts. 

To make it look perfect and highly responsive on standard terminal screens (widths of `80` to `200` character cells):
1. Set the **Column 1 and Column 2 width to a fixed `50` or `55` character cells** (`width: 55;`).
2. Set **Column 3 to `width: 1fr;`**. 

This gives Col 1 and 2 exactly enough space to present every label and input cleanly on a single line, while Column 3 gets all the leftover width to grow and shrink!
