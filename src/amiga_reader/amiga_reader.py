#!/usr/bin/env python3
"""
Amiga BPL and PAL File Reader
Reads and analyzes Amiga format files created by kingcon.exe

Kingcon.exe parameters explanation:
-interleaved: Bitplanes are interleaved (all planes for line 0, then line 1, etc.)
-format=N: Number of COLOR bitplanes (N). -Mask is a separate flag that adds mask plane(s).
            Non-interleaved+mask: appends 1 mask plane  → total file slots = N+1
            Interleaved+mask: mask duplicated per color plane → total file slots = N*2
-RawPalette: Output raw 12-bit palette data (2 bytes/color)
-RawPalette24: Output raw 24-bit palette data (4 bytes/color)
-Mask: Add mask plane(s); for interleaved, mask is duplicated after each color plane
"""

from pathlib import Path

from rich.console import Console

from amiga_reader.amiga_palette_reader import AmigaPaletteReader
from amiga_reader.amiga_bitplane_reader import AmigaBitplaneReader
from amiga_reader.amiga_file_analyzer import AmigaFileAnalyzer


def print_usage(console):
    """Print command-line help/usage details."""
    console.print(
        "[yellow]Usage: amiga-reader <mode> <base_name|file_options> [options][/yellow]"
    )
    console.print()
    console.print("[bold cyan]Modes:[/bold cyan]")
    console.print(
        "  [green]--display_details[/green]  - Display file details and analysis."
    )
    console.print(
        "  [green]--generate_png[/green]     - Generate PNG from BPL and PAL files."
    )
    console.print(
        "  [green]cov, coverage[/green]       - Show beautiful test coverage report."
    )
    console.print()
    console.print("[bold cyan]File Input (provide one of the following):[/bold cyan]")
    console.print(
        "  [green]<base_name>[/green]          - Base name for .bpl/.pal files (e.g., 'assets/image')."
    )
    console.print(
        "  [green]--bpl FILE --pal FILE[/green] - Explicit paths to .bpl and .pal files (--pal or --palette)."
    )
    console.print()
    console.print("[bold cyan]Required for BPL decoding:[/bold cyan]")
    console.print(
        "  [green]--width N, --height N[/green]  - Image dimensions. Required for PNG generation."
    )
    console.print(
        "                         [dim](Optional for --display_details; will attempt auto-detection)[/dim]"
    )
    console.print()
    console.print("[bold cyan]BPL/PAL Options:[/bold cyan]")
    console.print(
        "  [green]--bits N[/green]           - Number of color bitplanes (default: 5 → 32 colors)."
    )
    console.print(
        "  [green]--mask[/green]             - BPL has a mask plane (default: off)."
    )
    console.print(
        "  [green]--no-interleaved[/green]   - BPL is non-interleaved (default: is interleaved)."
    )
    console.print(
        "  [green]--pal-bits 12|24[/green]   - Bit depth of the .pal file: 12 (default) or 24."
    )
    console.print()
    console.print("[bold cyan]PNG Output Options:[/bold cyan]")
    console.print(
        "  [green]--output DIR[/green]         - Optional output directory for generated PNGs."
    )
    console.print(
        "  [green]--gen_mask[/green]         - Also create a 2-color PNG of the mask."
    )
    console.print(
        "  [green]--scale N[/green]          - Scale output PNG by 2, 3, or 4."
    )
    console.print(
        "  [green]--sprite_width N[/green]   - Draw tile grid overlay with this tile width."
    )
    console.print(
        "  [green]--sprite_height N[/green]  - Draw tile grid overlay with this tile height."
    )
    console.print()
    console.print("[bold cyan]Examples:[/bold cyan]")
    console.print(
        "[dim]  # Display details, auto-detecting dimensions for a sprite[/dim]"
    )
    console.print(
        "[dim]  amiga-reader --display_details assets/pacman-sprite[/dim]"
    )
    console.print(
        "[dim]  # Generate a PNG with a tile grid overlay, scaled 2x, to a specific directory[/dim]"
    )
    console.print(
        "[dim]  amiga-reader --generate_png assets/pacman_tiles --width 320 --height 320 --mask --sprite_width 16 --sprite_height 16 --scale 2 --output generated/[/dim]"
    )


def main():
    """Main entry point"""
    import sys

    console = Console()

    if len(sys.argv) < 2:
        # Launch TUI
        try:
            from amiga_reader.tui import main as launch_tui
            launch_tui()
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Error launching TUI:[/bold red] {e}", style="red")
            sys.exit(1)

    if sys.argv[1] in ("--help", "-h"):
        print_usage(console)
        sys.exit(0)

    # Parse mode argument
    mode_arg = sys.argv[1]
    if mode_arg == "--display_details":
        mode = "display"
    elif mode_arg == "--generate_png":
        mode = "generate"
    elif mode_arg in ("cov", "coverage"):
        try:
            from amiga_reader.rich_coverage import main as cov_main
            cov_main()
            sys.exit(0)
        except Exception as e:
            console.print(f"[bold red]Error showing coverage:[/bold red] {e}", style="red")
            sys.exit(1)
    else:
        console.print(
            f"[bold red]Error:[/bold red] Invalid mode '{sys.argv[1]}'", style="red"
        )
        console.print()
        print_usage(console)
        sys.exit(1)


    bpl_file = None
    pal_file = None
    output_dir = None
    width = None
    height = None
    bits = 5  # default: 5 bitplanes → 32 colors
    has_mask = False  # default: no mask
    interleaved = True  # default: interleaved
    pal_bits = 12  # default: Amiga 12-bit palette
    sprite_width = None
    sprite_height = None
    gen_mask = False
    scale = 1  # default: no scaling

    def _get_int_arg(name):
        if name in sys.argv:
            idx = sys.argv.index(name)
            if idx + 1 < len(sys.argv):
                try:
                    return int(sys.argv[idx + 1])
                except ValueError:
                    console.print(
                        f"[bold red]Error:[/bold red] {name} requires an integer, "
                        f"got '{sys.argv[idx + 1]}'"
                    )
                    sys.exit(1)
        return None

    # Parse arguments
    if "--bpl" in sys.argv:
        bpl_idx = sys.argv.index("--bpl")
        if bpl_idx + 1 < len(sys.argv):
            bpl_file = sys.argv[bpl_idx + 1]

    if "--pal" in sys.argv or "--palette" in sys.argv:
        pal_idx = sys.argv.index("--pal") if "--pal" in sys.argv else sys.argv.index("--palette")
        if pal_idx + 1 < len(sys.argv):
            pal_file = sys.argv[pal_idx + 1]

    if "--output" in sys.argv:
        output_idx = sys.argv.index("--output")
        if output_idx + 1 < len(sys.argv):
            output_dir = sys.argv[output_idx + 1]

    v = _get_int_arg("--width")
    if v is not None:
        width = v

    v = _get_int_arg("--height")
    if v is not None:
        height = v

    v = _get_int_arg("--bits")
    if v is not None:
        if v < 1 or v > 8:
            console.print("[bold red]Error:[/bold red] --bits must be between 1 and 8.")
            sys.exit(1)
        bits = v

    if "--mask" in sys.argv:
        # Support both "--mask" flag and "--mask true/false"
        mask_idx = sys.argv.index("--mask")
        if mask_idx + 1 < len(sys.argv) and sys.argv[mask_idx + 1].lower() in (
            "true",
            "1",
            "yes",
        ):
            has_mask = True
        elif mask_idx + 1 < len(sys.argv) and sys.argv[mask_idx + 1].lower() in (
            "false",
            "0",
            "no",
        ):
            has_mask = False
        else:
            has_mask = True  # bare flag means True

    if "--no-interleaved" in sys.argv:
        interleaved = False

    if "--pal-bits" in sys.argv:
        v = _get_int_arg("--pal-bits")
        if v not in (12, 24):
            console.print("[bold red]Error:[/bold red] --pal-bits must be 12 or 24.")
            sys.exit(1)
        pal_bits = v

    v = _get_int_arg("--sprite_width")
    if v is not None:
        sprite_width = v

    v = _get_int_arg("--sprite_height")
    if v is not None:
        sprite_height = v

    v = _get_int_arg("--scale")
    if v is not None:
        if v not in (2, 3, 4):
            console.print("[bold red]Error:[/bold red] --scale must be 2, 3, or 4.")
            sys.exit(1)
        scale = v

    if "--gen_mask" in sys.argv:
        gen_mask = True

    # Validate required args
    if width is None or height is None:
        if mode == "generate":
            console.print(
                "[bold red]Error:[/bold red] --width and --height are required for --generate_png mode.\n"
                "[dim]Example: --width 320 --height 320[/dim]"
            )
            sys.exit(1)
        # For display mode, if one is provided, the other must be too.
        elif width is not None or height is not None:
            console.print(
                "[bold red]Error:[/bold red] Please provide both --width and --height, or neither for auto-detection in display mode."
            )
            sys.exit(1)

    # If no explicit bpl file flag, assume base name (second argument after mode)
    if not bpl_file:
        if len(sys.argv) < 3 or sys.argv[2].startswith("--"):
            console.print(
                "[bold red]Error:[/bold red] Missing base name or --bpl file path",
                style="red",
            )
            sys.exit(1)
        base_name = sys.argv[2]
        bpl_file = f"{base_name}.bpl"
        if not pal_file:
            pal_path = Path(f"{base_name}.pal")
            pal_file = str(pal_path) if pal_path.exists() else None

    # Create analyzer and execute based on mode
    try:
        analyzer = AmigaFileAnalyzer(
            bpl_file=bpl_file,
            pal_file=pal_file,
            mode=mode,
            width=width,
            height=height,
            bits=bits,
            has_mask=has_mask,
            interleaved=interleaved,
            pal_bits=pal_bits,
            sprite_width=sprite_width,
            sprite_height=sprite_height,
            gen_mask=gen_mask,
            scale=scale,
            output_dir=output_dir,
        )

        if mode == "display":
            analyzer.display_summary()
        elif mode == "generate":
            analyzer.generate_png()

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
