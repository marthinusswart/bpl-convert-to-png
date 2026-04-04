from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from amiga_palette_reader import AmigaPaletteReader
from amiga_bitplane_reader import AmigaBitplaneReader
from amiga_png_creator import AmigaPngCreator


class AmigaFileAnalyzer:
    """Main analyzer class for Amiga BPL and PAL files"""

    def __init__(
        self,
        bpl_file=None,
        pal_file=None,
        mode="display",
        width=None,
        height=None,
        bits=5,
        has_mask=False,
        interleaved=True,
        pal_bits=12,
        sprite_width=None,
        sprite_height=None,
        gen_mask=False,
        scale=1,
        output_dir=None,
    ):
        """Initialize the analyzer

        Args:
            bpl_file:      Path to the .bpl bitplane file
            pal_file:      Path to the .pal palette file
            mode:          Operation mode - 'display' for details, 'generate' for PNG creation
            width:         Image width in pixels (--width).
            height:        Image height in pixels (--height).
            bits:          Number of color bitplanes, default 5 (--bits).
            has_mask:      Whether a mask plane is present (--mask).
            interleaved:   Whether the layout is interleaved (--interleaved).
            pal_bits:      Bit depth of the .pal file — 12 (default) or 24 (--pal-bits).
            sprite_width:  Tile width in pixels for label overlay (--sprite_width).
            sprite_height: Tile height in pixels for label overlay (--sprite_height).
            gen_mask:      If True, also generate a mask PNG (--gen_mask).
            output_dir:    Optional output directory for generated files.
        """
        self.console = Console()
        self.bpl_reader = None
        self.pal_reader = None
        self.mode = mode
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.gen_mask = gen_mask
        self.scale = scale
        self.output_dir = output_dir

        if pal_file:
            self.pal_reader = AmigaPaletteReader(pal_file, bits=pal_bits)

        if bpl_file:
            self.bpl_reader = AmigaBitplaneReader(
                bpl_file,
                width=width,
                height=height,
                bits=bits,
                has_mask=has_mask,
                interleaved=interleaved,
            )

    def display_summary(self):
        """Display a colorful summary of the files"""
        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]Amiga File Analyzer[/bold cyan]\n"
                "[dim]Kingcon.exe format: -interleaved -format=5 -RawPalette -Mask[/dim]",
                border_style="cyan",
            )
        )
        self.console.print()

        # Display BPL information
        if self.bpl_reader:
            self._display_bpl_info()

        # Display PAL information
        if self.pal_reader:
            self._display_pal_info()

    def _display_bpl_info(self):
        """Display bitplane file information"""
        info = self.bpl_reader.get_summary()

        # Create table for BPL info
        table = Table(
            title="[bold yellow]Bitplane (.bpl) Information[/bold yellow]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("File Path", str(self.bpl_reader.filepath))
        table.add_row("File Size", f"{info['file_size']:,} bytes")
        layout = "Interleaved" if info["interleaved"] else "Non-interleaved"
        table.add_row(
            "Format",
            f"{layout} (kingcon {'-Interleaved' if info['interleaved'] else 'no -Interleaved'})",
        )
        width, height = info["width"], info["height"]
        if width is not None and height is not None:
            dim_text = f"{width} x {height} pixels"
        else:
            dim_text = "[yellow]Undetermined (try providing --width and --height)[/yellow]"

        table.add_row("Image Dimensions", dim_text)
        table.add_row("Bytes per Scanline", f"{info['bytes_per_line']} bytes/plane")
        table.add_row(
            "Color Bitplanes", f"{info['depth']} planes (-Format={info['depth']})"
        )
        mask_desc = (
            "[green]✓ Yes — interleaved per plane (depth×2 slots)[/green]"
            if (info["has_mask"] and info["interleaved"])
            else (
                "[green]✓ Yes — appended (depth+1 slots)[/green]"
                if info["has_mask"]
                else "[red]✗ No[/red]"
            )
        )
        table.add_row("Mask Plane", mask_desc)
        table.add_row("Plane slots/scanline", f"{info['total_planes']}")
        table.add_row("Max Colors", f"{info['max_colors']} colors")

        self.console.print(table)
        self.console.print()

    def _display_pal_info(self):
        """Display palette file information"""
        info = self.pal_reader.get_summary()

        # Create table for PAL info
        table = Table(
            title="[bold yellow]Palette (.pal) Information[/bold yellow]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("File Path", str(self.pal_reader.filepath))
        table.add_row("File Size", f"{info['file_size']} bytes")
        bits = info["bits"]
        fmt_name = "-RawPalette24" if bits == 24 else "-RawPalette"
        table.add_row("Format", f"Raw Palette (kingcon {fmt_name})")
        table.add_row(
            "Bytes per Color",
            f"{bits // 8 * 2 if bits == 24 else 2} bytes (Amiga {bits}-bit RGB)",
        )
        table.add_row("Number of Colors", f"{info['num_colors']} colors")

        self.console.print(table)
        self.console.print()

        # Display color palette
        self._display_color_palette(info["colors"])

    def _display_color_palette(self, colors):
        """Display the color palette with visual representation"""
        self.console.print("[bold yellow]Color Palette:[/bold yellow]")
        self.console.print()

        # Create a table for colors
        color_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        color_table.add_column("Index", justify="right", style="cyan")
        color_table.add_column("RGB Values", style="white")
        color_table.add_column("Hex", style="white")
        color_table.add_column("Color Preview", style="white")

        for i, (r, g, b) in enumerate(colors):
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            rgb_str = f"({r:3d}, {g:3d}, {b:3d})"

            # Create a colored block for preview
            color_block = Text("████████", style=f"rgb({r},{g},{b})")

            color_table.add_row(str(i), rgb_str, hex_color, color_block)

        self.console.print(color_table)
        self.console.print()

    def generate_png(self):
        """Generate a PNG file from BPL and PAL data.

        Returns:
            Path to the generated PNG file, or None if inputs are unavailable.
        """
        creator = AmigaPngCreator(
            bpl_reader=self.bpl_reader,
            pal_reader=self.pal_reader,
            sprite_width=self.sprite_width,
            sprite_height=self.sprite_height,
            scale=self.scale,
            output_dir=self.output_dir,
        )
        result_path = creator.generate_png()

        if result_path and self.gen_mask:
            # The output path for the mask is handled by the creator, which will
            # generate a name like 'basename_mask.png'.
            creator.generate_mask_png()

        return result_path
