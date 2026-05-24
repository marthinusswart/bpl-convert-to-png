import pytest
import tempfile
import struct
import os
from pathlib import Path

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture returning the tmp_path directory as a Path object."""
    return tmp_path

@pytest.fixture
def create_mock_pal(tmp_path):
    """Factory fixture to create a mock .pal (palette) file."""
    def _create(filename="mock.pal", bits=12, colors=None):
        if colors is None:
            # Default palette: Black, White, Red, Green, Blue
            colors = [
                (0, 0, 0),        # Index 0
                (255, 255, 255),  # Index 1
                (255, 0, 0),      # Index 2
                (0, 255, 0),      # Index 3
                (0, 0, 255)       # Index 4
            ]
            
        file_path = tmp_path / filename
        with open(file_path, "wb") as f:
            for r, g, b in colors:
                if bits == 24:
                    # 24-bit: 0x00RRGGBB (4 bytes)
                    f.write(struct.pack("BBBB", 0, r, g, b))
                else:
                    # 12-bit Amiga RGB: 0x0RGB (2 bytes)
                    # Scale down 8-bit back to 4-bit (0-15)
                    r4 = min(15, r // 17)
                    g4 = min(15, g // 17)
                    b4 = min(15, b // 17)
                    word = (r4 << 8) | (g4 << 4) | b4
                    f.write(struct.pack(">H", word))
        return str(file_path), colors
    return _create

@pytest.fixture
def create_mock_bpl(tmp_path):
    """Factory fixture to create a mock .bpl (bitplane) file from a known pixel grid."""
    def _create(filename="mock.bpl", width=16, height=16, bits=5, has_mask=False, interleaved=True, fill_index=1, pattern_fn=None):
        # Determine width in bytes for one plane
        width_bytes = ((width + 15) // 16) * 2
        
        # Initialize default pixel grid
        pixels = [[fill_index & ((1 << bits) - 1) for _ in range(width)] for _ in range(height)]
        mask = [[255 for _ in range(width)] for _ in range(height)] if has_mask else None
        
        # Apply custom pattern if provided
        if pattern_fn:
            for y in range(height):
                for x in range(width):
                    val, m_val = pattern_fn(y, x)
                    pixels[y][x] = val & ((1 << bits) - 1)
                    if has_mask:
                        mask[y][x] = m_val

        # Pre-allocate plane buffers
        # plane_data[y][plane_index][x_byte]
        color_planes = [[[0 for _ in range(width_bytes)] for _ in range(bits)] for _ in range(height)]
        mask_planes = [[0 for _ in range(width_bytes)] for _ in range(height)]
        
        for y in range(height):
            for x_byte in range(width_bytes):
                # Construct color planes for this byte
                color_plane_bytes = [0] * bits
                for bit in range(8):
                    x = x_byte * 8 + bit
                    if x >= width:
                        break
                    
                    bit_flag = 0x80 >> bit
                    pixel_index = pixels[y][x]
                    
                    for j in range(bits):
                        if (pixel_index >> j) & 1:
                            color_plane_bytes[j] |= bit_flag
                
                for j in range(bits):
                    color_planes[y][j][x_byte] = color_plane_bytes[j]
                
                # Construct mask plane for this byte
                if has_mask:
                    mask_byte = 0
                    for bit in range(8):
                        x = x_byte * 8 + bit
                        if x >= width:
                            break
                        
                        bit_flag = 0x80 >> bit
                        if mask[y][x] > 0:
                            mask_byte |= bit_flag
                    mask_planes[y][x_byte] = mask_byte

        # Flatten into file bytes according to layout
        file_bytes = bytearray()
        
        if not interleaved:
            if not has_mask:
                # Non-interleaved, no mask: All scanlines for plane 0, then plane 1, etc.
                for j in range(bits):
                    for y in range(height):
                        file_bytes.extend(color_planes[y][j])
            else:
                # Non-interleaved, with mask: Color planes then mask plane
                for j in range(bits):
                    for y in range(height):
                        file_bytes.extend(color_planes[y][j])
                for y in range(height):
                    file_bytes.extend(mask_planes[y])
        else:
            if not has_mask:
                # Interleaved, no mask: Plane 0..N-1 for line 0, then line 1, etc.
                for y in range(height):
                    for j in range(bits):
                        file_bytes.extend(color_planes[y][j])
            else:
                # Interleaved, with mask: [p0][mask][p1][mask]...[pN-1][mask]
                # Total slots = bits * 2 per scanline
                for y in range(height):
                    for j in range(bits):
                        file_bytes.extend(color_planes[y][j])
                        file_bytes.extend(mask_planes[y]) # Duplicate mask after each color plane as per Amiga/Kingcon Interleaved spec

        file_path = tmp_path / filename
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        return str(file_path), pixels, mask
    return _create
