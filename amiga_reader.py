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

from amiga_palette_reader import AmigaPaletteReader
from amiga_bitplane_reader import AmigaBitplaneReader
from amiga_file_analyzer import AmigaFileAnalyzer


def main():
    """Main entry point"""
    import sys

    console = Console()

    if len(sys.argv) < 2:
        console.print(
            "[yellow]Usage: python amiga_reader.py <mode> <base_name> [options][/yellow]"
        )
        console.print()
        console.print("[bold cyan]Modes:[/bold cyan]")
        console.print(
            "  [green]--display_details[/green]  - Display file details and analysis"
        )
        console.print(
            "  [green]--generate_png[/green]     - Generate PNG from BPL and PAL files"
        )
        console.print()
        console.print("[bold cyan]Required for BPL decoding:[/bold cyan]")
        console.print(
            "  [green]--width N[/green]          - Image width in pixels (e.g. 320)"
        )
        console.print(
            "  [green]--height N[/green]         - Image height in pixels (e.g. 320)"
        )
        console.print()
        console.print("[bold cyan]Options:[/bold cyan]")
        console.print(
            "  [green]--bits N[/green]           - Number of color bitplanes (default: 5 → 32 colors)."
        )
        console.print(
            "  [green]--mask[/green]             - BPL has a mask plane (default: off)."
        )
        console.print(
            "  [green]--no-interleaved[/green]   - BPL is non-interleaved (default: interleaved)."
        )
        console.print(
            "  [green]--pal-bits 12|24[/green]   - Bit depth of the .pal file: 12 (default) or 24."
        )
        console.print()
        console.print("[bold cyan]Examples:[/bold cyan]")
        console.print(
            "[dim]  python amiga_reader.py --display_details assets/packman_tiles --width 320 --height 320[/dim]"
        )
        console.print(
            "[dim]  python amiga_reader.py --generate_png assets/packman_tiles --width 320 --height 320 --mask[/dim]"
        )
        console.print(
            "[dim]  python amiga_reader.py --generate_png --bpl file.bpl --pal file.pal --width 320 --height 320 --bits 4 --mask --output out.png[/dim]"
        )
        sys.exit(1)

    # Parse mode argument
    mode_arg = sys.argv[1]
    if mode_arg == "--display_details":
        mode = "display"
    elif mode_arg == "--generate_png":
        mode = "generate"
    else:
        console.print(
            f"[bold red]Error:[/bold red] Invalid mode '{sys.argv[1]}'", style="red"
        )
        console.print(
            "[yellow]Valid modes: --display_details or --generate_png[/yellow]"
        )
        sys.exit(1)

    bpl_file = None
    pal_file = None
    output_file = None
    width = None
    height = None
    bits = 5  # default: 5 bitplanes → 32 colors
    has_mask = False  # default: no mask
    interleaved = True  # default: interleaved
    pal_bits = 12  # default: Amiga 12-bit palette
    sprite_width = None
    sprite_height = None
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

    if "--pal" in sys.argv:
        pal_idx = sys.argv.index("--pal")
        if pal_idx + 1 < len(sys.argv):
            pal_file = sys.argv[pal_idx + 1]

    if "--output" in sys.argv:
        output_idx = sys.argv.index("--output")
        if output_idx + 1 < len(sys.argv):
            output_file = sys.argv[output_idx + 1]

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

    # Validate required args
    if width is None or height is None:
        console.print(
            "[bold red]Error:[/bold red] --width and --height are required.\n"
            "[dim]Example: --width 320 --height 320[/dim]"
        )
        sys.exit(1)

    # If no explicit file flags, assume base name (second argument after mode)
    if not bpl_file and not pal_file:
        if len(sys.argv) < 3:
            console.print(
                "[bold red]Error:[/bold red] Missing base name or file paths",
                style="red",
            )
            sys.exit(1)
        base_name = sys.argv[2]
        bpl_file = f"{base_name}.bpl"
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
            scale=scale,
        )

        if mode == "display":
            analyzer.display_summary()
        elif mode == "generate":
            analyzer.generate_png(output_path=output_file)

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
