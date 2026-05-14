#!/usr/bin/env python3
"""
MP4 ELST Patch Validator
Prints detailed atom structure and validates the bypass payload injection.
"""

import sys
import os
import struct
import json
from datetime import datetime


# ANSI Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def color(text, color_code):
    """Apply color to text if terminal supports it."""
    return f"{color_code}{text}{Colors.END}"


def read_atom_header(data, offset):
    """
    Read standard MP4 atom header.
    Returns (size, name, header_bytes) or None if invalid.
    """
    if offset + 8 > len(data):
        return None
    
    size = struct.unpack('>I', data[offset:offset+4])[0]
    name = data[offset+4:offset+8].decode('ascii', errors='replace')
    
    # Extended size (64-bit)
    if size == 1:
        if offset + 16 > len(data):
            return None
        size = struct.unpack('>Q', data[offset+8:offset+16])[0]
        return (size, name, 16)
    elif size == 0:
        # Atom extends to end of file
        size = len(data) - offset
    
    return (size, name, 8)


def find_all_atoms(data, start=0, end=None, depth=0, max_depth=3):
    """
    Recursively find and list all MP4 atoms.
    Returns list of dicts with atom info.
    """
    if end is None:
        end = len(data)
    
    atoms = []
    offset = start
    
    while offset < end:
        header = read_atom_header(data, offset)
        if not header:
            break
        
        size, name, header_size = header
        atom_end = offset + size
        
        if atom_end > end or size < 8:
            # Invalid or truncated
            break
        
        atom_info = {
            'offset': offset,
            'size': size,
            'name': name,
            'header_size': header_size,
            'data_start': offset + header_size,
            'depth': depth
        }
        
        # Parse specific atom types
        if name in ['elst', 'mvhd', 'tkhd', 'mdhd', 'stsz', 'stsd']:
            atom_info['parsed'] = parse_atom_data(name, data, offset + header_size, size - header_size)
        
        atoms.append(atom_info)
        
        # Recurse into container atoms
        if name in ['moov', 'trak', 'mdia', 'minf', 'stbl', 'edts', 'dinf'] and depth < max_depth:
            children = find_all_atoms(data, offset + header_size, atom_end, depth + 1, max_depth)
            atoms.extend(children)
        
        offset = atom_end
    
    return atoms


def parse_atom_data(atom_name, data, start, length):
    """Parse specific atom data structures."""
    parsed = {}
    
    try:
        if atom_name == 'elst' and length >= 12:
            # elst: version(1) + flags(3) + entry_count(4) + entries...
            version = data[start]
            flags = struct.unpack('>I', b'\x00' + data[start+1:start+4])[0]
            entry_count = struct.unpack('>I', data[start+4:start+8])[0]
            
            parsed['version'] = version
            parsed['flags'] = f"0x{flags:06x}"
            parsed['flags_raw'] = flags
            parsed['entry_count'] = entry_count
            
            # Read entries based on version
            entry_offset = start + 8
            entries = []
            for i in range(min(entry_count, 5)):  # Limit to 5 entries for display
                if version == 0:
                    if entry_offset + 12 > len(data):
                        break
                    segment_duration = struct.unpack('>I', data[entry_offset:entry_offset+4])[0]
                    media_time = struct.unpack('>i', data[entry_offset+4:entry_offset+8])[0]
                    media_rate = struct.unpack('>H', data[entry_offset+8:entry_offset+10])[0]
                    entries.append({
                        'segment_duration': segment_duration,
                        'media_time': media_time,
                        'media_rate_integer': media_rate
                    })
                    entry_offset += 12
                else:  # version 1
                    if entry_offset + 20 > len(data):
                        break
                    segment_duration = struct.unpack('>Q', data[entry_offset:entry_offset+8])[0]
                    media_time = struct.unpack('>q', data[entry_offset+8:entry_offset+16])[0]
                    media_rate = struct.unpack('>H', data[entry_offset+16:entry_offset+18])[0]
                    entries.append({
                        'segment_duration': segment_duration,
                        'media_time': media_time,
                        'media_rate_integer': media_rate
                    })
                    entry_offset += 20
            
            parsed['entries'] = entries
            
            # Check for bypass payload
            # The patch writes at offset +8 from atom start (which is start+header_size+8)
            # But in our structure, the atom data starts at 'start', so version/flags are at start+0
            # The JS code: dv.setUint32(ei + 8, config.payload, false)
            # ei is the atom name offset, so ei + 8 = start of version/flags field
            flags_raw = struct.unpack('>I', data[start:start+4])[0]
            parsed['bypass_payload_detected'] = (flags_raw == 0x01000000)
            parsed['flags_hex'] = f"0x{flags_raw:08x}"
        
        elif atom_name == 'mvhd' and length >= 24:
            version = data[start]
            parsed['version'] = version
            if version == 0:
                parsed['creation_time'] = struct.unpack('>I', data[start+4:start+8])[0]
                parsed['modification_time'] = struct.unpack('>I', data[start+8:start+12])[0]
                parsed['timescale'] = struct.unpack('>I', data[start+12:start+16])[0]
                parsed['duration'] = struct.unpack('>I', data[start+16:start+20])[0]
            else:
                parsed['creation_time'] = struct.unpack('>Q', data[start+4:start+12])[0]
                parsed['modification_time'] = struct.unpack('>Q', data[start+12:start+20])[0]
                parsed['timescale'] = struct.unpack('>I', data[start+20:start+24])[0]
                parsed['duration'] = struct.unpack('>Q', data[start+24:start+32])[0]
        
        elif atom_name == 'tkhd' and length >= 20:
            version = data[start]
            parsed['version'] = version
            if version == 0:
                parsed['width'] = struct.unpack('>I', data[start+48:start+52])[0] >> 16
                parsed['height'] = struct.unpack('>I', data[start+52:start+56])[0] >> 16
            else:
                parsed['width'] = struct.unpack('>I', data[start+60:start+64])[0] >> 16
                parsed['height'] = struct.unpack('>I', data[start+64:start+68])[0] >> 16
        
        elif atom_name == 'stsz' and length >= 8:
            parsed['version'] = data[start]
            parsed['sample_size'] = struct.unpack('>I', data[start+4:start+8])[0]
            parsed['sample_count'] = struct.unpack('>I', data[start+8:start+12])[0]
        
        elif atom_name == 'mdhd' and length >= 24:
            version = data[start]
            parsed['version'] = version
            if version == 0:
                parsed['timescale'] = struct.unpack('>I', data[start+12:start+16])[0]
                parsed['duration'] = struct.unpack('>I', data[start+16:start+20])[0]
            else:
                parsed['timescale'] = struct.unpack('>I', data[start+20:start+24])[0]
                parsed['duration'] = struct.unpack('>Q', data[start+24:start+32])[0]
    
    except Exception as e:
        parsed['parse_error'] = str(e)
    
    return parsed


def print_atom_tree(atoms, highlight_elst=True):
    """Print formatted atom tree."""
    print(color("\n" + "═" * 70, Colors.HEADER))
    print(color("  MP4 ATOM STRUCTURE", Colors.BOLD + Colors.HEADER))
    print(color("═" * 70, Colors.HEADER))
    
    for atom in atoms:
        indent = "  " * atom['depth']
        size_kb = atom['size'] / 1024
        
        # Highlight elst atom
        is_elst = atom['name'] == 'elst'
        name_color = Colors.GREEN if is_elst else Colors.CYAN
        if highlight_elst and is_elst:
            name_color = Colors.BOLD + Colors.GREEN
        
        line = f"{indent}├─ {color(atom['name'], name_color)} "
        line += f"offset={atom['offset']:<8} size={atom['size']:<8} ({size_kb:.1f} KB)"
        
        # Add parsed data summary
        if 'parsed' in atom:
            p = atom['parsed']
            details = []
            
            if atom['name'] == 'elst':
                details.append(f"ver={p.get('version', '?')}")
                details.append(f"flags={p.get('flags_hex', p.get('flags', '?'))}")
                details.append(f"entries={p.get('entry_count', '?')}")
                if p.get('bypass_payload_detected'):
                    details.append(color("✓ BYPASS PAYLOAD ACTIVE", Colors.GREEN + Colors.BOLD))
            
            elif atom['name'] == 'mvhd':
                details.append(f"timescale={p.get('timescale', '?')}")
                details.append(f"duration={p.get('duration', '?')}")
            
            elif atom['name'] == 'tkhd':
                details.append(f"{p.get('width', '?')}×{p.get('height', '?')}")
            
            elif atom['name'] == 'stsz':
                details.append(f"samples={p.get('sample_count', '?')}")
            
            if details:
                line += "  [" + " | ".join(details) + "]"
        
        print(line)
    
    print(color("═" * 70, Colors.HEADER))


def validate_elst_patch(original_path, patched_path):
    """
    Compare original and patched files to validate the elst modification.
    """
    print(color("\n" + "█" * 70, Colors.BOLD + Colors.BLUE))
    print(color("  MP4 ELST PATCH VALIDATOR", Colors.BOLD + Colors.BLUE))
    print(color("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), Colors.BLUE))
    print(color("█" * 70, Colors.BOLD + Colors.BLUE))
    
    # Check files exist
    for path, label in [(original_path, "Original"), (patched_path, "Patched")]:
        if not os.path.exists(path):
            print(color(f"\n✗ ERROR: {label} file not found: {path}", Colors.RED))
            return False
    
    # Read files
    with open(original_path, 'rb') as f:
        original_data = f.read()
    with open(patched_path, 'rb') as f:
        patched_data = f.read()
    
    print(f"\n{color('Original:', Colors.YELLOW)} {original_path}")
    print(f"  Size: {len(original_data):,} bytes ({len(original_data)/1048576:.2f} MB)")
    print(f"\n{color('Patched:', Colors.YELLOW)} {patched_path}")
    print(f"  Size: {len(patched_data):,} bytes ({len(patched_data)/1048576:.2f} MB)")
    
    # Find elst atoms in both
    def find_elst(data):
        for i in range(len(data) - 4):
            if data[i:i+4] == b'elst':
                header = read_atom_header(data, i)
                if header:
                    return i, header[0], parse_atom_data('elst', data, i + header[2], header[0] - header[2])
        return None
    
    orig_elst = find_elst(original_data)
    patch_elst = find_elst(patched_data)
    
    print(color("\n" + "─" * 70, Colors.YELLOW))
    print(color("  ELST ATOM COMPARISON", Colors.BOLD + Colors.YELLOW))
    print(color("─" * 70, Colors.YELLOW))
    
    if not orig_elst:
        print(color("\n✗ No 'elst' atom found in ORIGINAL file!", Colors.RED))
        return False
    
    if not patch_elst:
        print(color("\n✗ No 'elst' atom found in PATCHED file!", Colors.RED))
        return False
    
    orig_offset, orig_size, orig_parsed = orig_elst
    patch_offset, patch_size, patch_parsed = patch_elst
    
    print(f"\n{color('Original elst:', Colors.CYAN)}")
    print(f"  Offset: {orig_offset}")
    print(f"  Size: {orig_size}")
    print(f"  Version: {orig_parsed.get('version', '?')}")
    print(f"  Flags: {orig_parsed.get('flags_hex', orig_parsed.get('flags', '?'))}")
    print(f"  Entry Count: {orig_parsed.get('entry_count', '?')}")
    
    print(f"\n{color('Patched elst:', Colors.CYAN)}")
    print(f"  Offset: {patch_offset}")
    print(f"  Size: {patch_size}")
    print(f"  Version: {patch_parsed.get('version', '?')}")
    print(f"  Flags: {patch_parsed.get('flags_hex', patch_parsed.get('flags', '?'))}")
    print(f"  Entry Count: {patch_parsed.get('entry_count', '?')}")
    
    # Validate the patch
    print(color("\n" + "─" * 70, Colors.YELLOW))
    print(color("  VALIDATION RESULTS", Colors.BOLD + Colors.YELLOW))
    print(color("─" * 70, Colors.YELLOW))
    
    checks = []
    
    # Check 1: File sizes should be identical (in-place modification)
    size_match = len(original_data) == len(patched_data)
    checks.append(("File size unchanged", size_match, 
                   f"{len(original_data)} == {len(patched_data)}"))
    
    # Check 2: Only elst region should differ
    diff_count = sum(1 for a, b in zip(original_data, patched_data) if a != b)
    only_elst_modified = diff_count <= 16  # Should only be the 4 bytes at elst+8
    checks.append(("Only elst atom modified", only_elst_modified,
                   f"{diff_count} bytes differ"))
    
    # Check 3: elst flags should contain bypass payload
    bypass_active = patch_parsed.get('bypass_payload_detected', False)
    checks.append(("Bypass payload detected (0x01000000)", bypass_active,
                   f"flags = {patch_parsed.get('flags_hex', '?')}"))
    
    # Check 4: Original should NOT have bypass
    orig_clean = not orig_parsed.get('bypass_payload_detected', False)
    checks.append(("Original file clean", orig_clean,
                   f"flags = {orig_parsed.get('flags_hex', '?')}"))
    
    # Print results
    all_pass = True
    for check_name, passed, detail in checks:
        status = color("✓ PASS", Colors.GREEN) if passed else color("✗ FAIL", Colors.RED)
        print(f"\n  {status} {color(check_name, Colors.BOLD)}")
        print(f"    Detail: {detail}")
        if not passed:
            all_pass = False
    
    # Print full atom trees
    print(color("\n" + "─" * 70, Colors.YELLOW))
    print(color("  ORIGINAL FILE ATOM TREE", Colors.BOLD + Colors.YELLOW))
    orig_atoms = find_all_atoms(original_data)
    print_atom_tree(orig_atoms)
    
    print(color("\n" + "─" * 70, Colors.YELLOW))
    print(color("  PATCHED FILE ATOM TREE", Colors.BOLD + Colors.YELLOW))
    patch_atoms = find_all_atoms(patched_data)
    print_atom_tree(patch_atoms)
    
    # Final summary
    print(color("\n" + "█" * 70, Colors.BOLD + (Colors.GREEN if all_pass else Colors.RED)))
    if all_pass:
        print(color("  ✓ PATCH VALIDATED SUCCESSFULLY", Colors.BOLD + Colors.GREEN))
        print(color("  The elst bypass payload is correctly injected.", Colors.GREEN))
    else:
        print(color("  ✗ PATCH VALIDATION FAILED", Colors.BOLD + Colors.RED))
        print(color("  Review the failed checks above.", Colors.RED))
    print(color("█" * 70, Colors.BOLD + (Colors.GREEN if all_pass else Colors.RED)))
    
    return all_pass


def print_single_file(file_path):
    """Analyze and print details of a single MP4 file."""
    if not os.path.exists(file_path):
        print(color(f"✗ File not found: {file_path}", Colors.RED))
        return False
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(color("\n" + "█" * 70, Colors.BOLD + Colors.BLUE))
    print(color(f"  FILE ANALYSIS: {os.path.basename(file_path)}", Colors.BOLD + Colors.BLUE))
    print(color("█" * 70, Colors.BOLD + Colors.BLUE))
    print(f"  Path: {file_path}")
    print(f"  Size: {len(data):,} bytes ({len(data)/1048576:.2f} MB)")
    
    atoms = find_all_atoms(data)
    print_atom_tree(atoms, highlight_elst=True)
    
    # Find and detail elst specifically
    elst_found = False
    for atom in atoms:
        if atom['name'] == 'elst' and 'parsed' in atom:
            elst_found = True
            p = atom['parsed']
            print(color("\n" + "─" * 70, Colors.CYAN))
            print(color("  ELST ATOM DETAIL", Colors.BOLD + Colors.CYAN))
            print(color("─" * 70, Colors.CYAN))
            print(f"  Version: {p.get('version', '?')}")
            print(f"  Flags: {p.get('flags', '?')} (raw: {p.get('flags_hex', '?')})")
            print(f"  Entry Count: {p.get('entry_count', '?')}")
            print(f"  Bypass Payload Detected: {color('YES', Colors.GREEN) if p.get('bypass_payload_detected') else color('NO', Colors.RED)}")
            
            if 'entries' in p:
                print(f"\n  Entries:")
                for i, entry in enumerate(p['entries']):
                    print(f"    [{i}] segment_duration={entry['segment_duration']}, "
                          f"media_time={entry['media_time']}, "
                          f"media_rate={entry['media_rate_integer']}")
    
    if not elst_found:
        print(color("\n✗ No 'elst' atom found in this file!", Colors.RED))
    
    print(color("\n" + "█" * 70, Colors.BOLD + Colors.BLUE))
    return True


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(
        description='MP4 ELST Patch Validator - Analyze and validate Maska bypass patches',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  python validate.py video.mp4
  
  # Compare original vs patched
  python validate.py original.mp4 patched.mp4
  
  # Export to JSON
  python validate.py video.mp4 --json output.json
        """
    )
    parser.add_argument('files', nargs='+', help='MP4 file(s) to analyze (1 or 2 files)')
    parser.add_argument('--json', '-j', metavar='FILE', help='Export atom data to JSON file')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')
    
    # Handle different modes
    if len(args.files) == 1:
        # Single file analysis
        success = print_single_file(args.files[0])
        
        # JSON export if requested
        if args.json and success:
            with open(args.files[0], 'rb') as f:
                data = f.read()
            atoms = find_all_atoms(data)
            export_data = {
                'filename': os.path.basename(args.files[0]),
                'file_size': len(data),
                'analysis_time': datetime.now().isoformat(),
                'atoms': atoms
            }
            with open(args.json, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\nExported to JSON: {args.json}")
    
    elif len(args.files) == 2:
        # Compare mode
        success = validate_elst_patch(args.files[0], args.files[1])
        
        if args.json:
            with open(args.files[0], 'rb') as f:
                orig_data = f.read()
            with open(args.files[1], 'rb') as f:
                patch_data = f.read()
            
            export_data = {
                'original': {
                    'filename': os.path.basename(args.files[0]),
                    'file_size': len(orig_data),
                    'atoms': find_all_atoms(orig_data)
                },
                'patched': {
                    'filename': os.path.basename(args.files[1]),
                    'file_size': len(patch_data),
                    'atoms': find_all_atoms(patch_data)
                },
                'comparison_time': datetime.now().isoformat()
            }
            with open(args.json, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\nExported to JSON: {args.json}")
    
    else:
        parser.error("Provide 1 file to analyze, or 2 files to compare (original + patched)")


if __name__ == "__main__":
    main()