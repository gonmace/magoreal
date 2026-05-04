"""
Regenerate letter paths with more points for smoother shapes.
Extracts A-Z, a-z, and 0-9.

Usage:
  python scripts/regenerate_all_paths.py [--font PATH.otf] [--out PATH.py]

Por defecto la fuente es morph_banner/Quadrillion Sb.otf y el salida
letter_paths_all.py (modo seguridad). Para producción usar --out hacia letter_paths.py
vía font_pipeline.py o este flag explícito.
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    from fontTools.pens.recordingPen import RecordingPen
except ImportError:
    print("ERROR: fontTools not installed. Install with: pip install fonttools")
    sys.exit(1)

import numpy as np

# Configuration
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


def split_subpaths(commands):
    """Split commands into subpaths. Each 'M' starts a new subpath."""
    subpaths = []
    current_subpath = []
    for cmd in commands:
        if cmd[0] == 'M':
            if current_subpath:
                subpaths.append(current_subpath)
            current_subpath = [cmd]
        else:
            current_subpath.append(cmd)
    if current_subpath:
        subpaths.append(current_subpath)
    return subpaths


def resample_subpath(commands, target_points):
    """Resample a single subpath to target points."""
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


def resample_path(commands, target_points):
    """Convert commands to uniformly spaced points along the path, handling multiple subpaths.
    Returns a list of lists (each sublist is a subpath of points)."""
    subpaths = split_subpaths(commands)
    if not subpaths:
        return []
    
    # If only one subpath, return a list with one subpath
    if len(subpaths) == 1:
        return [resample_subpath(subpaths[0], target_points)]
    
    # For multiple subpaths, distribute points proportionally to subpath length
    # First, compute length of each subpath
    subpath_lengths = []
    for subpath in subpaths:
        # Compute length of this subpath (approximate)
        points = []
        current_pos = (0, 0)
        start_pos = None
        for cmd in subpath:
            if cmd[0] == 'M':
                current_pos = cmd[1]
                start_pos = current_pos
                points.append(current_pos)
            elif cmd[0] == 'L':
                current_pos = cmd[1]
                points.append(current_pos)
            elif cmd[0] == 'C':
                p0 = current_pos
                p1, p2, p3 = cmd[1], cmd[2], cmd[3]
                # Sample a few points to estimate length
                num_samples = 10
                curve_points = interpolate_curve(p0, p1, p2, p3, num_samples)
                points.extend(curve_points[1:])
                current_pos = p3
            elif cmd[0] == 'Z':
                if start_pos and points and points[-1] != start_pos:
                    points.append(start_pos)
        # Compute length
        if len(points) < 2:
            subpath_lengths.append(1.0)
        else:
            length = 0.0
            for i in range(1, len(points)):
                dx = points[i][0] - points[i-1][0]
                dy = points[i][1] - points[i-1][1]
                length += np.sqrt(dx*dx + dy*dy)
            subpath_lengths.append(length)
    
    total_length = sum(subpath_lengths)
    if total_length == 0:
        # Distribute points equally
        points_per_subpath = [target_points // len(subpaths)] * len(subpaths)
        # Add remaining points to first subpaths
        for i in range(target_points % len(subpaths)):
            points_per_subpath[i] += 1
    else:
        # Distribute proportionally
        points_per_subpath = []
        for length in subpath_lengths:
            proportion = length / total_length
            points = max(10, int(proportion * target_points))
            points_per_subpath.append(points)
        # Adjust to match target_points
        total_assigned = sum(points_per_subpath)
        if total_assigned != target_points:
            # Adjust by adding/removing from largest subpaths
            diff = target_points - total_assigned
            sorted_indices = sorted(range(len(subpath_lengths)), key=lambda i: subpath_lengths[i], reverse=True)
            for idx in sorted_indices:
                if diff == 0:
                    break
                if diff > 0:
                    points_per_subpath[idx] += 1
                    diff -= 1
                else:
                    if points_per_subpath[idx] > 10:
                        points_per_subpath[idx] -= 1
                        diff += 1
    
    # Resample each subpath and return list of lists
    subpath_results = []
    for i, subpath in enumerate(subpaths):
        subpath_points = resample_subpath(subpath, points_per_subpath[i])
        subpath_results.append(subpath_points)
    
    return subpath_results


def path_to_d_string_single(points, y_offset=LETTER_HEIGHT):
    """Convert points to SVG path string with Y flipped."""
    if not points:
        return ""
    parts = [f"M {points[0][0]:.3f} {y_offset - points[0][1]:.3f}"]
    for x, y in points[1:]:
        parts.append(f"L {x:.3f} {y_offset - y:.3f}")
    parts.append("Z")
    return " ".join(parts)


def path_to_d_string(subpaths, y_offset=LETTER_HEIGHT):
    """Convert list of subpaths (each a list of points) to SVG path string."""
    if not subpaths:
        return ""
    parts = []
    for subpath in subpaths:
        if not subpath:
            continue
        parts.append(f"M {subpath[0][0]:.3f} {y_offset - subpath[0][1]:.3f}")
        for x, y in subpath[1:]:
            parts.append(f"L {x:.3f} {y_offset - y:.3f}")
        parts.append("Z")
    return " ".join(parts)


def create_dummy_counter_path(x=30, y=30, y_offset=LETTER_HEIGHT, num_points=20):
    """Create a dummy counter path (single point) for letters without counters.
    This ensures KUTE.js can morph between all letters consistently.
    Returns all points at the same location (effectively invisible)."""
    
    # All points at the same location - makes the "circle" effectively invisible
    px, py = x, y
    
    # Build path string - all points at same location
    parts = [f"M {px:.3f} {y_offset - py:.3f}"]
    for _ in range(num_points - 1):
        parts.append(f"L {px:.3f} {y_offset - py:.3f}")
    parts.append("Z")
    return " ".join(parts)


def is_likely_counter(subpath, outer_subpath):
    """Determine if a subpath is likely a counter (hole) vs structural element.
    A counter is typically:
    1. Centered horizontally within the outer path (KEY differentiator)
    2. Contained within the vertical bounds of the outer path
    3. Having a reasonable number of commands
    
    The main differentiator is horizontal centering: counters (holes) are
    centered within the letter, while structural elements (like R's diagonal leg)
    extend to the sides.
    """
    def get_bounds(cmds):
        xs, ys = [], []
        for cmd in cmds:
            if cmd[0] == 'M':
                xs.append(cmd[1][0]); ys.append(cmd[1][1])
            elif cmd[0] == 'L':
                xs.append(cmd[1][0]); ys.append(cmd[1][1])
            elif cmd[0] == 'C':
                xs.extend([cmd[1][0], cmd[2][0], cmd[3][0]])
                ys.extend([cmd[1][1], cmd[2][1], cmd[3][1]])
        if not xs:
            return None
        return {'min_x': min(xs), 'max_x': max(xs), 'min_y': min(ys), 'max_y': max(ys)}
    
    outer_bounds = get_bounds(outer_subpath)
    sub_bounds = get_bounds(subpath)
    
    if not outer_bounds or not sub_bounds:
        return False
    
    outer_width = outer_bounds['max_x'] - outer_bounds['min_x']
    outer_center_x = (outer_bounds['min_x'] + outer_bounds['max_x']) / 2
    
    sub_center_x = (sub_bounds['min_x'] + sub_bounds['max_x']) / 2
    sub_bottom = sub_bounds['max_y']
    sub_top = sub_bounds['min_y']
    
    # CRITERION 1: Horizontal center alignment (KEY differentiator!)
    # Counters should be centered horizontally within the letter
    # R's leg: center offset = 22%, O's counter: center offset = 0%
    center_offset = abs(sub_center_x - outer_center_x) / outer_width
    if center_offset > 0.15:  # Only 15% deviation from center
        return False
    
    # CRITERION 2: Not extending to extreme edges
    # Counters should not start very close to the left edge (structural elements often do)
    sub_left_ratio = (sub_bounds['min_x'] - outer_bounds['min_x']) / outer_width
    if sub_left_ratio < 0.05:  # Counter should not start at the very edge
        return False
    
    # CRITERION 3: Not too many commands (counters are simple shapes)
    if len(subpath) > 30:
        return False
    
    return True


def extract_letter_paths(font_file):
    """Extract letter paths from font file.
    Returns separate outer_path and counter_path for each letter.
    Letters without counters get a dummy point path for consistent morphing."""
    global LETTER_HEIGHT, VIEWBOX_PADDING
    font_file = os.path.abspath(font_file)
    font = TTFont(font_file)
    glyph_set = font.getGlyphSet()
    
    # Get character to glyph mapping
    cmap = font.getBestCmap()
    
    letters = {}
    
    # Characters to extract: uppercase, lowercase, digits
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    
    # First pass: collect scaled subpaths and Y points for global height calculation
    temp_data = {}
    all_y_points = []
    
    for char in chars:
        if ord(char) not in cmap:
            print(f"Warning: {char} not found in font")
            continue
            
        glyph_name = cmap[ord(char)]
        if glyph_name not in glyph_set:
            print(f"Warning: glyph {glyph_name} not found")
            continue
            
        pen = PointPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        
        # Resample to target points (returns list of subpaths)
        subpath_points_list = resample_path(pen.commands, TARGET_POINTS)
        
        # Flatten all points for bounding box calculation
        all_points = []
        for subpath in subpath_points_list:
            all_points.extend(subpath)
        
        # Calculate width (bounding box)
        if all_points:
            xs = [p[0] for p in all_points]
            width = (max(xs) - min(xs)) * SCALE_K
        else:
            width = 50
        
        # Calculate center for dummy counter path
        if all_points:
            xs = [p[0] for p in all_points]
            ys = [p[1] for p in all_points]
            center_x = ((max(xs) + min(xs)) / 2) * SCALE_K
            center_y = LETTER_HEIGHT / 2  # Will be centered vertically
        else:
            center_x = 30
            center_y = LETTER_HEIGHT / 2
        
        # Scale subpaths
        scaled_subpaths = []
        for subpath in subpath_points_list:
            scaled_subpath = [(x * SCALE_K, y * SCALE_K) for x, y in subpath]
            scaled_subpaths.append(scaled_subpath)
        
        # Store scaled subpaths and collect Y points for global height calculation
        temp_data[char] = {
            'scaled_subpaths': scaled_subpaths,
            'width': width,
            'center_x': center_x,
            'subpath_points_list': subpath_points_list,
            'original_subpaths': split_subpaths(pen.commands),
        }
        
        # Collect Y points for global bounds
        for subpath in scaled_subpaths:
            for x, y in subpath:
                all_y_points.append(y)
        
        # Store additional data for second pass
        temp_data[char]['original_subpaths'] = split_subpaths(pen.commands)
        temp_data[char]['center_x'] = center_x
        temp_data[char]['width'] = width
        temp_data[char]['subpath_points_list'] = subpath_points_list
    
    # Calculate global Y bounds from all collected points
    if all_y_points:
        global_min_y = min(all_y_points)
        global_max_y = max(all_y_points)
    else:
        global_min_y = 0
        global_max_y = LETTER_HEIGHT
    
    # Calculate required height with padding
    VIEWBOX_PADDING = 5  # Reduced padding
    global_height = global_max_y - global_min_y + 2 * VIEWBOX_PADDING
    LETTER_HEIGHT = global_height
    
    # Calculate global vertical offset to center at LETTER_HEIGHT/2
    global_center = (global_min_y + global_max_y) / 2
    global_offset_y = LETTER_HEIGHT / 2 - global_center
    
    # Second pass: build paths with global centering
    for char, data in temp_data.items():
        scaled_subpaths = data['scaled_subpaths']
        width = data['width']
        center_x = data['center_x']
        subpath_points_list = data['subpath_points_list']
        original_subpaths = data['original_subpaths']
        
        # Apply global vertical offset to all subpaths
        centered_subpaths = []
        for subpath in scaled_subpaths:
            centered_subpath = [(x, y + global_offset_y) for x, y in subpath]
            centered_subpaths.append(centered_subpath)
        
        # Recalculate center_y for dummy counter path (now centered globally)
        center_y = LETTER_HEIGHT / 2
        
        # Identify counters and outer subpaths (same logic as before)
        def get_area(subpath):
            xs, ys = [], []
            for cmd in subpath:
                if cmd[0] == 'M':
                    xs.append(cmd[1][0]); ys.append(cmd[1][1])
                elif cmd[0] == 'L':
                    xs.append(cmd[1][0]); ys.append(cmd[1][1])
                elif cmd[0] == 'C':
                    xs.extend([cmd[1][0], cmd[2][0], cmd[3][0]])
                    ys.extend([cmd[1][1], cmd[2][1], cmd[3][1]])
            if len(xs) < 2:
                return 0
            return (max(xs) - min(xs)) * (max(ys) - min(ys))
        
        outer_idx = 0
        if len(original_subpaths) > 1:
            areas = [(i, get_area(sub)) for i, sub in enumerate(original_subpaths)]
            areas.sort(key=lambda x: x[1], reverse=True)
            outer_idx = areas[0][0]
        
        counter_subpath_indices = []
        for i in range(len(original_subpaths)):
            if i == outer_idx:
                continue
            if is_likely_counter(original_subpaths[i], original_subpaths[outer_idx]):
                counter_subpath_indices.append(i)
        
        outer_subpath_indices = [i for i in range(len(original_subpaths)) if i not in counter_subpath_indices]
        
        # Build outer_path
        if len(outer_subpath_indices) == 1:
            outer_path = path_to_d_string_single(centered_subpaths[outer_subpath_indices[0]], LETTER_HEIGHT)
        else:
            parts = []
            for idx in outer_subpath_indices:
                subpath = centered_subpaths[idx]
                if not subpath:
                    continue
                parts.append(f"M {subpath[0][0]:.3f} {LETTER_HEIGHT - subpath[0][1]:.3f}")
                for x, y in subpath[1:]:
                    parts.append(f"L {x:.3f} {LETTER_HEIGHT - y:.3f}")
                parts.append("Z")
            outer_path = " ".join(parts)
        
        # Build counter_path
        has_counter = len(counter_subpath_indices) > 0
        if has_counter:
            counter_subpaths_list = [centered_subpaths[i] for i in counter_subpath_indices]
            counter_path = path_to_d_string(counter_subpaths_list, LETTER_HEIGHT)
        else:
            counter_path = create_dummy_counter_path(center_x, center_y, LETTER_HEIGHT, 20)
        
        letters[char] = {
            'width': round(width, 1),
            'outer_path': outer_path,
            'counter_path': counter_path,
            'has_counter': has_counter,
            'num_subpaths': len(subpath_points_list)
        }
        
        counter_status = "has counter" if has_counter else "no counter (dummy)"
        print(f"Built {char}: {len(subpath_points_list)} subpaths, {counter_status}, width={width:.1f}")
    
    # Update global variables
    LETTER_HEIGHT = global_height
    VIEWBOX_PADDING = 5
    
    return letters


def generate_python_code(letters):
    """Generate Python code for letter paths with separate outer and counter paths."""
    lines = [
        '"""',
        f'Pre-computed SVG paths for A-Z, a-z, 0-9.',
        f'All paths have {TARGET_POINTS} points for consistent KUTE.js morphing.',
        'Paths are scaled and positioned for viewBox with positive Y coordinates.',
        'Each letter has outer_path (main shape) and counter_path (hole or dummy point).',
        '"""',
        '',
        f'TARGET_POINTS = {TARGET_POINTS}',
        f'SCALE_K = {SCALE_K}',
        f'LETTER_HEIGHT = {LETTER_HEIGHT}',
        f'VIEWBOX_PADDING = {VIEWBOX_PADDING}',
        '',
        'LETTER_PATHS = {',
    ]
    
    # Write uppercase first
    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if char in letters:
            data = letters[char]
            lines.append(f"    '{char}': {{")
            lines.append(f"        'width': {data['width']},")
            lines.append(f"        'outer_path': \"{data['outer_path']}\",")
            lines.append(f"        'counter_path': \"{data['counter_path']}\",")
            lines.append(f"        'has_counter': {data['has_counter']},")
            lines.append("    },")
    
    # Then lowercase
    for char in "abcdefghijklmnopqrstuvwxyz":
        if char in letters:
            data = letters[char]
            lines.append(f"    '{char}': {{")
            lines.append(f"        'width': {data['width']},")
            lines.append(f"        'outer_path': \"{data['outer_path']}\",")
            lines.append(f"        'counter_path': \"{data['counter_path']}\",")
            lines.append(f"        'has_counter': {data['has_counter']},")
            lines.append("    },")
    
    # Then digits
    for char in "0123456789":
        if char in letters:
            data = letters[char]
            lines.append(f"    '{char}': {{")
            lines.append(f"        'width': {data['width']},")
            lines.append(f"        'outer_path': \"{data['outer_path']}\",")
            lines.append(f"        'counter_path': \"{data['counter_path']}\",")
            lines.append(f"        'has_counter': {data['has_counter']},")
            lines.append("    },")
    
    lines.append('}')
    lines.append('')
    
    return '\n'.join(lines)


if __name__ == '__main__':
    landing_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_font = os.path.join(landing_root, 'landing', 'morph_banner', 'Quadrillion Sb.otf')
    default_out = os.path.join(landing_root, 'landing', 'morph_banner', 'letter_paths_all.py')

    ap = argparse.ArgumentParser(description='Extracción A–Z / a–z / 0–9 → LETTER_PATHS')
    ap.add_argument('--font', '-f', default=default_font, help='Archivo .otf/.ttf')
    ap.add_argument(
        '--out', '-o', default=default_out,
        help='Archivo Python de salida (producción: .../letter_paths.py)',
    )
    args = ap.parse_args()

    font_file = os.path.abspath(args.font)
    if not os.path.isfile(font_file):
        print(f"ERROR: no existe la fuente: {font_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Extrayendo paths desde {font_file}")
    print(f"Puntos objetivo por letra: {TARGET_POINTS}")
    print()

    letters = extract_letter_paths(font_file)

    code = generate_python_code(letters)
    output_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"\nGuardado en: {output_path}")

    print(f"\nGlifos totales: {len(letters)}")
    print("Mayúsculas:", sum(1 for c in letters if c.isupper()))
    print("Minúsculas:", sum(1 for c in letters if c.islower()))
    print("Dígitos:", sum(1 for c in letters if c.isdigit()))