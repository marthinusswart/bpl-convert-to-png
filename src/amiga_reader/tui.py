#!/usr/bin/env python3
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Label,
    Input,
    Checkbox,
    Select,
    Button,
    RichLog,
    ListView,
    ListItem,
)
from textual.binding import Binding

from amiga_reader.amiga_file_analyzer import AmigaFileAnalyzer
from amiga_reader.amiga_bitplane_reader import AmigaBitplaneReader


class AmigaTUIApp(App):
    """A premium Textual TUI for Amiga BPL/PAL to PNG Converter."""

    TITLE = "Amiga BPL Converter TUI"
    SUBTITLE = "Select, Configure, and Convert interactively"

    CSS = """
    Screen {
        background: #0f111a;
        color: #a6accd;
    }

    #main-layout {
        layout: horizontal;
        height: 1fr;
    }

    #sidebar {
        width: 36;
        background: #141622;
        border-right: tall #23263b;
        padding: 1;
    }

    #content {
        width: 1fr;
        background: #0f111a;
        padding: 1;
    }

    #columns-container {
        layout: horizontal;
        height: 1fr;
        min-height: 42;
        margin-bottom: 1;
    }


    .column {
        width: 1fr;
        height: 100%;
        padding-right: 1;
    }

    #col1, #col2 {
        width: 60;
    }

    #col1 .form-group {
        max-height: 12;
    }


    #col2 .form-group {
        max-height: 20;
    }








    #logs-container {
        height: 14;
        border-top: tall #23263b;
        background: #0a0b10;
        padding: 0 1;
    }

    .section-title {
        text-style: bold;
        color: #00f0ff;
        margin-bottom: 1;
        background: #1b1e2e;
        padding: 0 1;
        height: 1;
    }

    .form-group {
        background: #151825;
        border: round #23263b;
        padding: 1;
        margin-bottom: 1;
    }

    .form-row {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
        content-align: left middle;
    }

    .form-label {
        width: 18;
        color: #828bb8;
        content-align: left middle;
    }

    .form-input {
        width: 1fr;
    }

    .form-checkbox {
        width: 1fr;
    }

    ListView {
        background: #0a0b10;
        border: round #23263b;
        height: 8;
        margin-bottom: 1;
    }

    #bpl-list {
        height: 16;
    }


    ListItem {
        padding: 0 1;
        color: #a6accd;
    }

    ListItem:hover {
        background: #1c1e30;
    }

    ListItem.--highlight {
        background: #00f0ff;
        color: #0f111a;
        text-style: bold;
    }

    #info-panel {
        background: #0d0f18;
        border: round #1e2133;
        padding: 1;
        height: 1fr;
        color: #717cbe;
    }

    Button {
        width: 1fr;
        height: 3;
        border: none;
        text-style: bold;
        margin-top: 1;
    }

    #buttons-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        margin-bottom: 1;
    }


    #buttons-row Button {
        width: 1fr;
        margin-top: 0;
    }

    #btn-convert {
        background: #00f0ff;
        color: #0f111a;
    }

    #btn-convert:hover {
        background: #00c8d6;
        color: #0f111a;
    }

    #btn-display {
        background: #10b981;
        color: white;
        margin-right: 1;
    }

    #btn-display:hover {
        background: #059669;
    }



    #analysis-log {
        background: #0a0b10;
        border: round #23263b;
        height: 1fr;
        margin-top: 1;
        margin-bottom: 1;
    }


    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "convert", "Convert to PNG", show=True),
        Binding("d", "display", "Analyze File", show=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bpl_files = []
        self.pal_files = []
        self.scan_files()

    def scan_files(self):
        """Scan the bpl directory for BPL and PAL files."""
        bpl_dir = Path("bpl")
        if not bpl_dir.exists():
            return

        # Case-insensitive scan
        for f in bpl_dir.iterdir():
            if f.is_file():
                suffix = f.suffix.lower()
                if suffix == ".bpl":
                    self.bpl_files.append(f)
                elif suffix == ".pal":
                    self.pal_files.append(f)

        self.bpl_files.sort(key=lambda p: p.name.lower())
        self.pal_files.sort(key=lambda p: p.name.lower())

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-layout"):
            # Left Sidebar: file selection & file preview
            with Vertical(id="sidebar"):
                yield Label(" BPL Files", classes="section-title")
                
                # File List
                self.file_list = ListView(*[
                    ListItem(Label(f.name), id=f"bpl_{i}")
                    for i, f in enumerate(self.bpl_files)
                ], id="bpl-list")
                yield self.file_list

                yield Label(" PAL Files", classes="section-title")
                
                # PAL List
                self.pal_list = ListView(*[
                    ListItem(Label(f.name), id=f"pal_{i}")
                    for i, f in enumerate(self.pal_files)
                ])
                yield self.pal_list

                # Info/Details Panel
                yield Label(" File Details", classes="section-title")
                self.info_label = Label(
                    "[dim]Select a BPL file from the list above to view details and auto-fill conversion options.[/dim]",
                    id="info-panel"
                )
                yield self.info_label

            # Right Panel: options form
            with VerticalScroll(id="content"):
                yield Label(" Conversion Options", classes="section-title")

                with Horizontal(id="columns-container"):
                    # Left Column: Basic, Dimensions, and Output
                    with Vertical(id="col1", classes="column"):
                        # Basic Info Block
                        with Vertical(classes="form-group"):
                            with Horizontal(classes="form-row"):
                                yield Label("Selected BPL:", classes="form-label")
                                self.input_bpl = Input(placeholder="No BPL file selected", disabled=True, classes="form-input")
                                yield self.input_bpl

                            with Horizontal(classes="form-row"):
                                yield Label("Select PAL:", classes="form-label")
                                pal_options = [("None", "none")] + [(pf.name, str(pf)) for pf in self.pal_files]
                                self.select_pal = Select(pal_options, value="none", classes="form-input")
                                yield self.select_pal

                        # Dimensions Form Block
                        with Vertical(classes="form-group"):
                            with Horizontal(classes="form-row"):
                                yield Label("Image Width:", classes="form-label")
                                self.input_width = Input(placeholder="e.g. 320 (must be multiple of 16)", classes="form-input")
                                yield self.input_width

                            with Horizontal(classes="form-row"):
                                yield Label("Image Height:", classes="form-label")
                                self.input_height = Input(placeholder="e.g. 320", classes="form-input")
                                yield self.input_height

                        # Output Block
                        with Vertical(classes="form-group"):
                            with Horizontal(classes="form-row"):
                                yield Label("Output Folder:", classes="form-label")
                                self.input_output_dir = Input(value="converted", placeholder="e.g. converted", classes="form-input")
                                yield self.input_output_dir

                            with Horizontal(classes="form-row"):
                                yield Label("Mask PNG:", classes="form-label")
                                self.cb_gen_mask = Checkbox("Also Generate Separate Mask PNG", value=False, classes="form-checkbox")
                                yield self.cb_gen_mask

                    # Right Column: Format, Scaling, and Grid Overlay
                    with Vertical(id="col2", classes="column"):
                        # Format & Bits Block
                        with Vertical(classes="form-group"):
                            with Horizontal(classes="form-row"):
                                yield Label("Color Bits/Planes:", classes="form-label")
                                self.select_bits = Select([(str(i), i) for i in range(1, 9)], value=5, classes="form-input")
                                yield self.select_bits

                            with Horizontal(classes="form-row"):
                                yield Label("Palette Bits:", classes="form-label")
                                self.select_pal_bits = Select([("12-bit (Standard Amiga)", 12), ("24-bit", 24)], value=12, classes="form-input")
                                yield self.select_pal_bits

                            with Horizontal(classes="form-row"):
                                yield Label("Format Settings:", classes="form-label")
                                self.cb_interleaved = Checkbox("Interleaved Layout", value=True, classes="form-checkbox")
                                yield self.cb_interleaved

                            with Horizontal(classes="form-row"):
                                yield Label("", classes="form-label")
                                self.cb_mask = Checkbox("Has Mask Plane", value=False, classes="form-checkbox")
                                yield self.cb_mask

                        # Scaling & Grid Block
                        with Vertical(classes="form-group"):
                            with Horizontal(classes="form-row"):
                                yield Label("PNG Scale:", classes="form-label")
                                self.select_scale = Select([("1x", 1), ("2x", 2), ("3x", 3), ("4x", 4)], value=3, classes="form-input")
                                yield self.select_scale

                            with Horizontal(classes="form-row"):
                                yield Label("Overlay Grid:", classes="form-label")
                                self.cb_overlay = Checkbox("Draw Tile Grid Labels", value=False, classes="form-checkbox")
                                yield self.cb_overlay

                            with Horizontal(classes="form-row"):
                                yield Label("Sprite Width:", classes="form-label")
                                self.input_sprite_w = Input(value="16", placeholder="e.g. 16", classes="form-input")
                                yield self.input_sprite_w

                            with Horizontal(classes="form-row"):
                                yield Label("Sprite Height:", classes="form-label")
                                self.input_sprite_h = Input(value="16", placeholder="e.g. 16", classes="form-input")
                                yield self.input_sprite_h

                    # Third Column: Actions
                    with Vertical(id="col3", classes="column"):
                        with Horizontal(id="buttons-row"):
                            yield Button("Analyze (D)", id="btn-display")
                            yield Button("Convert (C)", id="btn-convert")


                        yield Label(" Analysis Details", classes="section-title")
                        self.analysis_log = RichLog(highlight=True, markup=True, id="analysis-log")
                        yield self.analysis_log


        # Bottom section: interactive logs
        with Vertical(id="logs-container"):
            yield Label(" Execution Logs", classes="section-title")
            self.execution_log = RichLog(highlight=True, markup=True)
            yield self.execution_log

        yield Footer()

    def on_mount(self) -> None:
        self.execution_log.write("[bold green]TUI Initialized successfully.[/bold green] Welcome to Amiga BPL Converter TUI.")
        self.execution_log.write("Select a file from the sidebar to begin.")

        self.analysis_log.write("[bold cyan]No analysis run yet.[/bold cyan]")
        self.analysis_log.write("Detailed file structures, dimensions, and color palettes will be displayed here.")
        self.analysis_log.write("Select a BPL file and click [bold green]Analyze (D)[/bold green] to begin.")

        # Focus the list view
        self.file_list.focus()

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """Fires when a BPL or PAL file is selected via click or Enter."""
        self.handle_list_selection(message)

    def on_list_view_highlighted(self, message: ListView.Highlighted) -> None:
        """Fires when the highlighted item changes via keyboard arrows or mouse hover."""
        self.handle_list_selection(message)

    def handle_list_selection(self, message) -> None:
        """Helper to process both selection and highlighting changes dynamically."""
        if not message.item:
            return

        if message.list_view == self.file_list:
            # BPL file selected or highlighted
            idx = int(message.item.id.split("_")[1])
            selected_file = self.bpl_files[idx]

            # Avoid duplicate work if it's already the active selection
            if self.input_bpl.value == str(selected_file):
                return

            # Update selected BPL input
            self.input_bpl.value = str(selected_file)

            # Attempt auto-detection & palette matching
            self.execution_log.write(f"Analyzing [bold cyan]{selected_file.name}[/bold cyan] for auto-configuration...")
            self.auto_configure(selected_file)

        elif message.list_view == self.pal_list:
            # PAL file selected or highlighted
            idx = int(message.item.id.split("_")[1])
            selected_pal = self.pal_files[idx]
            
            # Avoid duplicate work if it's already the active selection
            if self.select_pal.value == str(selected_pal):
                return

            # Update select dropdown value in the form
            self.select_pal.value = str(selected_pal)
            self.execution_log.write(f"Selected palette via sidebar list: [green]{selected_pal.name}[/green]")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Watch for changes in the select palette dropdown and sync with PAL list."""
        if event.select == self.select_pal:
            val = event.value
            if val == "none" or val is None:
                self.pal_list.index = None
            else:
                try:
                    matching_pal = Path(val)
                    idx = self.pal_files.index(matching_pal)
                    self.pal_list.index = idx
                except ValueError:
                    self.pal_list.index = None

    def auto_configure(self, bpl_path: Path):
        """Automatically detect BPL specs and matching PAL file."""
        # 1. Matching PAL File
        matching_pal = None
        stem_clean = bpl_path.stem.lower()
        if "_mask" in stem_clean:
            base_stem = stem_clean[:-5]  # remove '_mask'
        else:
            base_stem = stem_clean

        # Search in scanned palette files case-insensitively
        for pf in self.pal_files:
            if pf.stem.lower() == base_stem:
                matching_pal = pf
                break

        if matching_pal:
            self.select_pal.value = str(matching_pal)
            self.execution_log.write(f"  ↳ Found matching palette: [green]{matching_pal.name}[/green]")
            # Highlight matching palette in the sidebar list
            try:
                idx = self.pal_files.index(matching_pal)
                self.pal_list.index = idx
            except ValueError:
                self.pal_list.index = None
        else:
            self.select_pal.value = "none"
            self.pal_list.index = None

        # 2. File size and mask guess
        file_size = bpl_path.stat().st_size
        stem_clean = bpl_path.stem.lower()

        # Mask detection: if filename has 'mask' in it
        is_mask_file = "mask" in stem_clean
        self.cb_mask.value = is_mask_file

        # Number of bits: masks usually have 1 bit
        if is_mask_file:
            self.select_bits.value = 1
        else:
            # Default to 5 bits
            self.select_bits.value = 5

        # Interleaved vs non-interleaved guess
        if "pacman-sprite" in stem_clean:
            self.cb_interleaved.value = True
        else:
            self.cb_interleaved.value = False

        # 3. Size and Dimensions Auto-detect heuristic
        width = None
        height = None

        if "pacman_tiles" in stem_clean:
            width, height = 320, 320
            self.cb_overlay.value = True
            self.input_sprite_w.value = "16"
            self.input_sprite_h.value = "16"
        elif "plowman_tiles" in stem_clean:
            width, height = 320, 320
            self.cb_overlay.value = True
            self.input_sprite_w.value = "16"
            self.input_sprite_h.value = "16"
        elif "alphanumeric" in stem_clean:
            width, height = 160, 160
            self.cb_overlay.value = True
            self.input_sprite_w.value = "8"
            self.input_sprite_h.value = "8"
        elif "pacman-sprite" in stem_clean:
            if "0001" in stem_clean or "0004" in stem_clean:
                width, height = 16, 16
                self.cb_overlay.value = True
                self.input_sprite_w.value = "16"
                self.input_sprite_h.value = "16"
            else:
                width, height = 32, 256
                self.cb_overlay.value = True
                self.input_sprite_w.value = "32"
                self.input_sprite_h.value = "16"

        # Fallback to reader dimension auto-detection
        if width is None or height is None:
            try:
                temp_reader = AmigaBitplaneReader(
                    filepath=bpl_path,
                    width=None,
                    height=None,
                    bits=self.select_bits.value,
                    has_mask=self.cb_mask.value,
                    interleaved=self.cb_interleaved.value,
                )
                if temp_reader.width and temp_reader.height:
                    width = temp_reader.width
                    height = temp_reader.height
                    self.execution_log.write(f"  ↳ Auto-detected dimensions: [green]{width} x {height}[/green]")
            except Exception as e:
                self.execution_log.write(f"  ↳ Dimension auto-detection failed: {e}")

        # Update input fields
        self.input_width.value = str(width) if width else ""
        self.input_height.value = str(height) if height else ""

        # Update file info panel
        self.update_info_panel(bpl_path, file_size, width, height, matching_pal)

        # Update analysis panel with prompt
        self.analysis_log.clear()
        self.analysis_log.write(f"[bold cyan]Selected BPL: {bpl_path.name}[/bold cyan]")
        self.analysis_log.write("-" * 40)
        self.analysis_log.write("Click [bold green]Analyze (D)[/bold green] or press the [bold cyan]D[/bold cyan] key to view detailed file info, dimensions, and color palette grids here.")

    def update_info_panel(self, bpl_path: Path, file_size: int, width: int, height: int, matching_pal: Path):
        """Draw info summary in left sidebar panel."""
        info = f"[bold white]{bpl_path.name}[/bold white]\n"
        info += f"  Size: {file_size:,} bytes\n"
        if width and height:
            info += f"  Dims: {width} x {height} px\n"
        else:
            info += "  Dims: Unknown (Enter manually)\n"
        
        info += f"  Mask File: {'Yes' if self.cb_mask.value else 'No'}\n"
        info += f"  Layout: {'Interleaved' if self.cb_interleaved.value else 'Non-interleaved'}\n"
        
        if matching_pal:
            info += f"  Palette: [green]{matching_pal.name}[/green]\n"
        else:
            info += "  Palette: [yellow]None matched[/yellow]\n"

        info += "\n[dim cyan]Press 'C' to convert\nPress 'D' to analyze[/dim cyan]"
        
        self.info_label.update(info)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-convert":
            self.action_convert()
        elif event.button.id == "btn-display":
            self.action_display()

    def get_form_values(self):
        """Extract and validate all settings from the form."""
        bpl_file = self.input_bpl.value
        if not bpl_file:
            self.execution_log.write("[bold red]Error: No BPL file selected![/bold red]")
            return None

        pal_val = self.select_pal.value
        pal_file = None if pal_val == "none" else pal_val

        # Width / Height
        try:
            width = int(self.input_width.value)
            height = int(self.input_height.value)
        except ValueError:
            self.execution_log.write("[bold red]Error: Width and Height must be integers![/bold red]")
            return None

        # Bits
        bits = self.select_bits.value

        # Mask & Interleaved
        has_mask = self.cb_mask.value
        interleaved = self.cb_interleaved.value

        # Palette Bits
        pal_bits = self.select_pal_bits.value

        # Scale
        scale = self.select_scale.value

        # Overlay Grid
        sprite_width = None
        sprite_height = None
        if self.cb_overlay.value:
            try:
                sprite_width = int(self.input_sprite_w.value)
                sprite_height = int(self.input_sprite_h.value)
            except ValueError:
                self.execution_log.write("[bold yellow]Warning: Sprite dims invalid, ignoring overlay grid.[/bold yellow]")

        # Gen Mask PNG
        gen_mask = self.cb_gen_mask.value

        # Output Dir
        output_dir = self.input_output_dir.value or "converted"

        return {
            "bpl_file": bpl_file,
            "pal_file": pal_file,
            "width": width,
            "height": height,
            "bits": bits,
            "has_mask": has_mask,
            "interleaved": interleaved,
            "pal_bits": pal_bits,
            "scale": scale,
            "sprite_width": sprite_width,
            "sprite_height": sprite_height,
            "gen_mask": gen_mask,
            "output_dir": output_dir,
        }

    def action_convert(self) -> None:
        """Run the PNG conversion."""
        values = self.get_form_values()
        if not values:
            return

        self.execution_log.write("-" * 50)
        self.execution_log.write(f"[bold green]Starting conversion for {Path(values['bpl_file']).name}...[/bold green]")

        try:
            # Set up analyzer
            analyzer = AmigaFileAnalyzer(
                bpl_file=values["bpl_file"],
                pal_file=values["pal_file"],
                mode="generate",
                width=values["width"],
                height=values["height"],
                bits=values["bits"],
                has_mask=values["has_mask"],
                interleaved=values["interleaved"],
                pal_bits=values["pal_bits"],
                sprite_width=values["sprite_width"],
                sprite_height=values["sprite_height"],
                gen_mask=values["gen_mask"],
                scale=values["scale"],
                output_dir=values["output_dir"],
            )

            # Redirect analyzer print statements to TUI log
            def log_print(*args, **kwargs):
                message = " ".join(str(arg) for arg in args)
                self.execution_log.write(message)

            analyzer.console.print = log_print

            # Run PNG generation
            result_path = analyzer.generate_png()
            if result_path:
                self.execution_log.write(f"[bold green]🎉 SUCCESS! PNG generated at:[/bold green] [white underline]{result_path}[/white underline]")
            else:
                self.execution_log.write("[bold yellow]Conversion completed but no file was written (possibly missing palette).[/bold yellow]")

        except Exception as e:
            self.execution_log.write(f"[bold red]CRITICAL ERROR during conversion: {e}[/bold red]")
            import traceback
            for line in traceback.format_exc().splitlines():
                self.execution_log.write(f"[red]{line}[/red]")

    def action_display(self) -> None:
        """Display details & analysis of the selected BPL/PAL files."""
        values = self.get_form_values()
        if not values:
            return

        self.execution_log.write("-" * 50)
        self.execution_log.write(f"[bold yellow]Analyzing: {Path(values['bpl_file']).name}[/bold yellow]")
        self.execution_log.write("Detailed results displayed in the [bold cyan]Analysis Details[/bold cyan] panel in Column 3.")

        self.analysis_log.clear()
        self.analysis_log.write(f"[bold yellow]Analyzing: {Path(values['bpl_file']).name}[/bold yellow]")
        self.analysis_log.write("-" * 40)

        try:
            analyzer = AmigaFileAnalyzer(
                bpl_file=values["bpl_file"],
                pal_file=values["pal_file"],
                mode="display",
                width=values["width"],
                height=values["height"],
                bits=values["bits"],
                has_mask=values["has_mask"],
                interleaved=values["interleaved"],
                pal_bits=values["pal_bits"],
                sprite_width=values["sprite_width"],
                sprite_height=values["sprite_height"],
                gen_mask=values["gen_mask"],
                scale=values["scale"],
                output_dir=values["output_dir"],
            )

            def log_print(*args, **kwargs):
                if not args:
                    self.analysis_log.write("")
                else:
                    for arg in args:
                        self.analysis_log.write(arg)

            analyzer.console.print = log_print
            analyzer.display_summary()
            self.analysis_log.write("-" * 40)
            self.analysis_log.write("[bold green]Analysis complete.[/bold green]")
            self.execution_log.write("[bold green]Analysis complete.[/bold green]")

        except Exception as e:
            self.analysis_log.write(f"[bold red]CRITICAL ERROR: {e}[/bold red]")
            self.execution_log.write(f"[bold red]CRITICAL ERROR during analysis: {e}[/bold red]")


def main():
    app = AmigaTUIApp()
    app.run()


if __name__ == "__main__":
    main()
