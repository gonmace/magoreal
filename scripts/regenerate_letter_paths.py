"""
Regenerate letter paths with more points for smoother shapes.
Usage: python scripts/regenerate_letter_paths.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen
import numpy as np

# Configuration
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts', 'Inter-ExtraBold.woff2')
TARGET_POINTS = 100  # Increased from 50 for smoother shapes
SCALE_K = 0.0288
LETTER_HEIGHT = 59
VIEWBOX_PADDING = 20


class PointPen(BasePen):
    """Extract points from glyph."""
    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.points = []
        self.commands = []

    def _moveTo(self, pt):
        self.points.append(('M', pt))
        self.commands.append(('M', pt))

    def _lineTo(self, pt):
        self.points.append(('L', pt))
        self.commands.append(('L', pt))

    def _curveToOne(self, pt1, pt2, pt3):
        # Convert cubic bezier to points
        self.points.append(('C', pt1, pt2, pt3))
        self.commands.append(('C', pt1, pt2, pt3))

    def _closePath(self):
        self.points.append(('Z',))
        self.commands.append(('Z',))

    def _endPath(self):
        pass


def bezier_point(p0, p1, p2, p3, t):
    """Calculate point on cubic bezier curve at t."""
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1],
    )


def interpolate_curve(p0, p1, p2, p3, num_points):
    """Sample points along a cubic bezier curve."""
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        points.append(bezier_point(p0, p1, p2, p3, t))
    return points


def resample_path(commands, target_points):
    """Convert commands to uniformly spaced points along the path."""
    all_points = []
    current_pos = (0, 0)
    start_pos = None

    for cmd in commands:
        if cmd[0] == 'M':
            current_pos = cmd[1]
            start_pos = current_pos
            all_points.append(current_pos)
        elif cmd[0] == 'L':
            current_pos = cmd[1]
            all_points.append(current_pos)
        elif cmd[0] == 'C':
            # Sample bezier curve
            p0 = current_pos
            p1, p2, p3 = cmd[1], cmd[2], cmd[3]
            num_samples = max(10, target_points // len(commands))
            curve_points = interpolate_curve(p0, p1, p2, p3, num_samples)
            all_points.extend(curve_points[1:])  # Skip first point (same as current)
            current_pos = p3
        elif cmd[0] == 'Z':
            if start_pos and all_points and all_points[-1] != start_pos:
                all_points.append(start_pos)

    if len(all_points) < 2:
        return all_points

    # Calculate path length
    lengths = [0]
    for i in range(1, len(all_points)):
        dx = all_points[i][0] - all_points[i-1][0]
        dy = all_points[i][1] - all_points[i-1][1]
        lengths.append(lengths[-1] + np.sqrt(dx*dx + dy*dy))

    total_length = lengths[-1]
    if total_length == 0:
        return all_points[:target_points]

    # Sample at uniform intervals
    resampled = []
    for i in range(target_points):
        target_length = (i / (target_points - 1)) * total_length
        # Find segment containing target_length
        for j in range(1, len(lengths)):
            if lengths[j] >= target_length:
                if lengths[j] == lengths[j-1]:
                    resampled.append(all_points[j-1])
                else:
                    t = (target_length - lengths[j-1]) / (lengths[j] - lengths[j-1])
                    x = all_points[j-1][0] + t * (all_points[j][0] - all_points[j-1][0])
                    y = all_points[j-1][1] + t * (all_points[j][1] - all_points[j-1][1])
                    resampled.append((x, y))
                break

    return resampled


def path_to_d_string(points, y_offset=LETTER_HEIGHT):
    """Convert points to SVG path string with Y flipped."""
    if not points:
        return ""
    parts = [f"M {points[0][0]:.3f} {y_offset - points[0][1]:.3f}"]
    for x, y in points[1:]:
        parts.append(f"L {x:.3f} {y_offset - y:.3f}")
    parts.append("Z")
    return " ".join(parts)


def extract_letter_paths():
    """Extract letter paths from font file."""
    font = TTFont(FONT_PATH)
    glyph_set = font.getGlyphSet()
    
    # Get character to glyph mapping
    cmap = font.getBestCmap()
    
    letters = {}
    
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ord(char) not in cmap:
            print(f"Warning: {char} not found in font")
            continue
            
        glyph_name = cmap[ord(char)]
        if glyph_name not in glyph_set:
            print(f"Warning: glyph {glyph_name} not found")
            continue
            
        pen = PointPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        
        # Resample to target points
        points = resample_path(pen.commands, TARGET_POINTS)
        
        # Calculate width (bounding box)
        if points:
            xs = [p[0] for p in points]
            width = (max(xs) - min(xs)) * SCALE_K
        else:
            width = 50
        
        # Scale points and convert to path string
        scaled_points = [(x * SCALE_K, y * SCALE_K) for x, y in points]
        path_d = path_to_d_string(scaled_points, LETTER_HEIGHT)
        
        letters[char] = {
            'width': round(width, 1),
            'path': path_d
        }
        
        print(f"Extracted {char}: {len(points)} points, width={width:.1f}")
    
    return letters


def generate_python_code(letters):
    """Generate Python code for letter paths."""
    lines = [
        '"""',
        'Pre-computed SVG paths for all A-Z letters.',
        f'All paths have {TARGET_POINTS} points for consistent KUTE.js morphing.',
        'Paths are scaled and positioned for viewBox with positive Y coordinates.',
        '"""',
        '',
        f'TARGET_POINTS = {TARGET_POINTS}',
        f'SCALE_K = {SCALE_K}',
        f'LETTER_HEIGHT = {LETTER_HEIGHT}',
        f'VIEWBOX_PADDING = {VIEWBOX_PADDING}',
        '',
        'LETTER_PATHS = {',
    ]
    
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if char in letters:
            data = letters[char]
            lines.append(f"    '{char}': {{")
            lines.append(f"        'width': {data['width']},")
            lines.append(f"        'path': \"{data['path']}\",")
            lines.append("    },")
    
    lines.append('}')
    lines.append('')
    
    return '\n'.join(lines)


if __name__ == '__main__':
    print(f"Extracting letter paths from {FONT_PATH}")
    print(f"Target points per letter: {TARGET_POINTS}")
    print()
    
    letters = extract_letter_paths()
    
    # Generate output
    code = generate_python_code(letters)
    
    # Save to file
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               'landing', 'morph_banner', 'letter_paths_new.py')
    
    with open(output_path, 'w') as f:
        f.write(code)
    
    print(f"\nSaved to: {output_path}")
    print("Replace the LETTER_PATHS in letter_paths.py with the new paths")
