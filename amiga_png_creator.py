from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console


class AmigaPngCreator:
    """Creates a PNG image from decoded Amiga bitplane and palette data."""

    def __init__(
        self, bpl_reader, pal_reader=None, sprite_width=None, sprite_height=None, scale=1
    ):
        """Args:
        bpl_reader:    An AmigaBitplaneReader instance with decoded pixel data.
        pal_reader:    An AmigaPaletteReader instance with palette colors (optional).
        sprite_width:  Tile width in pixels for label overlay (optional).
        sprite_height: Tile height in pixels for label overlay (optional).
        scale:         Output scale factor: 1 (default), 2, 3, or 4.
        """
        self.bpl_reader = bpl_reader
        self.pal_reader = pal_reader
        self.sprite_width = sprite_width
        self.sprite_height = sprite_height
        self.scale = scale
        self.console = Console()

    def generate_png(self, output_path=None):
        """Generate a PNG file from BPL and PAL data.

        Args:
            output_path: Output PNG path. If None, uses bpl filename with .png extension.

        Returns:
            Path to the generated PNG file, or None if inputs are unavailable.
        """
        if not self.bpl_reader:
            self.console.print("[bold red]Error:[/bold red] No BPL file loaded.")
            return None

        if not self.pal_reader:
            self.console.print(
                "[yellow]Skipping PNG generation — no .pal palette file available.[/yellow]"
            )
            return None

        pixels, mask = self.bpl_reader.decode_pixels()

        if pixels is None:
            raise ValueError("Failed to decode bitplane data")

        palette_colors = self.pal_reader.colors

        if output_path is None:
            output_path = self.bpl_reader.filepath.with_suffix(".png")
        else:
            output_path = Path(output_path)

        width = self.bpl_reader.width
        height = self.bpl_reader.height

        img = Image.new("RGBA", (width, height))

        # Build flat pixel list in one pass and push to PIL in a single call
        flat = []
        for y in range(height):
            for x in range(width):
                color_index = pixels[y][x]
                r, g, b = (
                    palette_colors[color_index]
                    if color_index < len(palette_colors)
                    else (0, 0, 0)
                )
                alpha = mask[y][x] if mask is not None else 255
                flat.append((r, g, b, alpha))
        img.putdata(flat)

        if self.scale > 1:
            img = img.resize((width * self.scale, height * self.scale), Image.NEAREST)

        if self.sprite_width and self.sprite_height:
            self._draw_tile_labels(img, palette_colors, width, height)

        img.save(output_path)

        out_w = width * self.scale
        out_h = height * self.scale
        self.console.print(
            f"[green]✓ PNG generated successfully:[/green] {output_path}"
        )
        self.console.print(f"[dim]  Dimensions: {out_w}x{out_h}[/dim]")
        self.console.print(f"[dim]  Colors used: {len(palette_colors)}[/dim]")
        if mask is not None:
            self.console.print(f"[dim]  Transparency: Yes (mask applied)[/dim]")
        if self.sprite_width and self.sprite_height:
            tiles_x = width // self.sprite_width
            tiles_y = height // self.sprite_height
            self.console.print(
                f"[dim]  Tile labels: {tiles_x}×{tiles_y} grid ({self.sprite_width}×{self.sprite_height} px/tile)[/dim]"
            )
        if self.scale > 1:
            self.console.print(f"[dim]  Scale: {self.scale}x[/dim]")

        return output_path

    def generate_mask_png(self, output_path=None):
        """Generates a 2-color (black/white) PNG from the mask data.

        Args:
            output_path: Output PNG path. If None, uses bpl filename with _mask.png suffix.

        Returns:
            Path to the generated PNG file, or None if inputs are unavailable.
        """
        if not self.bpl_reader:
            self.console.print("[bold red]Error:[/bold red] No BPL file loaded.")
            return None

        if not self.bpl_reader.has_mask:
            self.console.print(
                "[yellow]Skipping mask PNG generation — BPL file has no mask data.[/yellow]"
            )
            return None

        _, mask = self.bpl_reader.decode_pixels()

        if mask is None:
            self.console.print(
                "[yellow]Skipping mask PNG generation — BPL file has no mask data.[/yellow]"
            )
            return None

        if output_path is None:
            base_name = self.bpl_reader.filepath.stem
            output_path = self.bpl_reader.filepath.with_name(f"{base_name}_mask.png")
        else:
            output_path = Path(output_path)

        width = self.bpl_reader.width
        height = self.bpl_reader.height

        # Create a grayscale image ('L' mode). Mask data is 0 for transparent (black)
        # and 255 for opaque (white).
        img = Image.new("L", (width, height))
        flat_mask = [pixel for row in mask for pixel in row]
        img.putdata(flat_mask)

        if self.scale > 1:
            img = img.resize((width * self.scale, height * self.scale), Image.NEAREST)

        img.save(output_path)

        out_w = width * self.scale
        out_h = height * self.scale
        self.console.print(
            f"[green]✓ Mask PNG generated successfully:[/green] {output_path}"
        )
        self.console.print(f"[dim]  Dimensions: {out_w}x{out_h}[/dim]")
        self.console.print(f"[dim]  Format: 2-color grayscale (mask only)[/dim]")
        if self.scale > 1:
            self.console.print(f"[dim]  Scale: {self.scale}x[/dim]")

        return output_path

    def _draw_tile_labels(self, img, palette_colors, width, height):
        """Overlay row,col index labels on each sprite tile.

        Text color  = palette index 0
        Background  = palette index 1
        """
        draw = ImageDraw.Draw(img)
        font_size = 10 if self.scale > 1 else 6
        font = ImageFont.load_default(size=font_size)

        bg_rgb = palette_colors[1] if len(palette_colors) > 1 else (255, 255, 255)
        txt_rgb = palette_colors[0] if len(palette_colors) > 0 else (0, 0, 0)
        bg_color = (*bg_rgb, 255)
        txt_color = (*txt_rgb, 255)

        tiles_x = width // self.sprite_width
        tiles_y = height // self.sprite_height

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                label = f"{ty},{tx}"
                x0 = tx * self.sprite_width * self.scale
                y0 = ty * self.sprite_height * self.scale

                bbox = font.getbbox(label)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]

                draw.rectangle(
                    [x0, y0, x0 + text_w + 3, y0 + text_h + 3],
                    fill=bg_color,
                )
                draw.text((x0 + 2, y0 + 2), label, fill=txt_color, font=font)
