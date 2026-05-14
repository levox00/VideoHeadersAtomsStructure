#!/usr/bin/env python3
"""
MP4 Deep Structure Analyzer - Complete Atom & Binary Dumper
Prints every possible detail about MP4/MOV container structure.
"""

import sys
import os
import struct
import json
import binascii
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

MAC_EPOCH = datetime(1904, 1, 1)
HEX_WIDTH = 16
MAX_HEX_DUMP = 256
MAX_ENTRIES_DISPLAY = 10

# ============================================================
# ANSI COLORS
# ============================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def c(text, color):
    return f"{color}{text}{Colors.END}"


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def mac_time_to_datetime(mac_timestamp):
    try:
        dt = MAC_EPOCH + timedelta(seconds=mac_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return f"Invalid ({mac_timestamp})"


def format_duration(duration, timescale):
    if timescale and timescale > 0:
        seconds = duration / timescale
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:05.2f} ({seconds:.3f}s)"
        return f"{minutes}:{secs:05.2f} ({seconds:.3f}s)"
    return f"{duration} (no timescale)"


def hex_dump(data, offset=0, max_bytes=MAX_HEX_DUMP, indent="  "):
    result = []
    length = min(len(data), max_bytes)
    for i in range(0, length, HEX_WIDTH):
        chunk = data[i:i+HEX_WIDTH]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        hex_part = hex_part.ljust(HEX_WIDTH * 3 - 1)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        line = f"{indent}{offset+i:08x}  {hex_part}  |{ascii_part}|"
        result.append(line)
    if len(data) > max_bytes:
        result.append(f"{indent}... ({len(data) - max_bytes} more bytes)")
    return '\n'.join(result)


def read_atom_header(data, offset):
    if offset + 8 > len(data):
        return None
    size = struct.unpack('>I', data[offset:offset+4])[0]
    name = data[offset+4:offset+8].decode('ascii', errors='replace')
    header_size = 8
    if size == 1 and offset + 16 <= len(data):
        size = struct.unpack('>Q', data[offset+8:offset+16])[0]
        header_size = 16
    elif size == 0:
        size = len(data) - offset
    return (size, name, header_size)


# ============================================================
# COMPREHENSIVE ATOM PARSERS
# ============================================================

def parse_fullbox(data, offset):
    if offset + 4 > len(data):
        return None
    version = data[offset]
    flags = struct.unpack('>I', b'\x00' + data[offset+1:offset+4])[0]
    return {'version': version, 'flags': flags, 'flags_hex': f"0x{flags:06x}"}


def parse_ftyp(data, offset, length):
    parsed = {}
    if length >= 4:
        parsed['major_brand'] = data[offset:offset+4].decode('ascii', errors='replace')
    if length >= 8:
        parsed['minor_version'] = struct.unpack('>I', data[offset+4:offset+8])[0]
    brands = []
    for i in range(8, length, 4):
        if i + 4 <= len(data):
            brand = data[offset+i:offset+i+4].decode('ascii', errors='replace')
            brands.append(brand)
    parsed['compatible_brands'] = brands
    parsed['brand_count'] = len(brands)
    return parsed


def parse_mvhd(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    ver = fullbox['version']

    if ver == 0:
        if off + 96 > len(data): return parsed
        parsed['creation_time'] = struct.unpack('>I', data[off:off+4])[0]
        parsed['creation_time_date'] = mac_time_to_datetime(parsed['creation_time'])
        parsed['modification_time'] = struct.unpack('>I', data[off+4:off+8])[0]
        parsed['modification_time_date'] = mac_time_to_datetime(parsed['modification_time'])
        parsed['timescale'] = struct.unpack('>I', data[off+8:off+12])[0]
        parsed['duration'] = struct.unpack('>I', data[off+12:off+16])[0]
        parsed['duration_formatted'] = format_duration(parsed['duration'], parsed['timescale'])
        parsed['rate'] = struct.unpack('>I', data[off+16:off+20])[0] / 65536
        parsed['volume'] = struct.unpack('>H', data[off+20:off+22])[0] / 256
        off += 32
    else:
        if off + 108 > len(data): return parsed
        parsed['creation_time'] = struct.unpack('>Q', data[off:off+8])[0]
        parsed['creation_time_date'] = mac_time_to_datetime(parsed['creation_time'])
        parsed['modification_time'] = struct.unpack('>Q', data[off+8:off+16])[0]
        parsed['modification_time_date'] = mac_time_to_datetime(parsed['modification_time'])
        parsed['timescale'] = struct.unpack('>I', data[off+16:off+20])[0]
        parsed['duration'] = struct.unpack('>Q', data[off+20:off+28])[0]
        parsed['duration_formatted'] = format_duration(parsed['duration'], parsed['timescale'])
        parsed['rate'] = struct.unpack('>I', data[off+28:off+32])[0] / 65536
        parsed['volume'] = struct.unpack('>H', data[off+32:off+34])[0] / 256
        off += 44

    if off + 36 <= len(data):
        matrix = []
        for i in range(9):
            val = struct.unpack('>i', data[off+i*4:off+i*4+4])[0]
            matrix.append(val / 65536)
        parsed['matrix'] = matrix
        parsed['matrix_preview'] = f"[{matrix[0]:.4f}, {matrix[1]:.4f}, {matrix[2]:.4f}, ...]"

    if off + 44 <= len(data):
        parsed['next_track_id'] = struct.unpack('>I', data[off+40:off+44])[0]

    return parsed


def parse_tkhd(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    ver = fullbox['version']
    flags = fullbox['flags']

    parsed['track_enabled'] = bool(flags & 0x000001)
    parsed['track_in_movie'] = bool(flags & 0x000002)
    parsed['track_in_preview'] = bool(flags & 0x000004)

    if ver == 0:
        if off + 80 > len(data): return parsed
        parsed['creation_time'] = struct.unpack('>I', data[off:off+4])[0]
        parsed['modification_time'] = struct.unpack('>I', data[off+4:off+8])[0]
        parsed['track_id'] = struct.unpack('>I', data[off+8:off+12])[0]
        parsed['duration'] = struct.unpack('>I', data[off+16:off+20])[0]
        off += 36
    else:
        if off + 92 > len(data): return parsed
        parsed['creation_time'] = struct.unpack('>Q', data[off:off+8])[0]
        parsed['modification_time'] = struct.unpack('>Q', data[off+8:off+16])[0]
        parsed['track_id'] = struct.unpack('>I', data[off+16:off+20])[0]
        parsed['duration'] = struct.unpack('>Q', data[off+24:off+32])[0]
        off += 48

    if off + 8 <= len(data):
        parsed['layer'] = struct.unpack('>h', data[off:off+2])[0]
        parsed['alternate_group'] = struct.unpack('>h', data[off+2:off+4])[0]
        parsed['volume'] = struct.unpack('>H', data[off+4:off+6])[0] / 256
        off += 8

    if off + 36 <= len(data):
        matrix = []
        for i in range(9):
            val = struct.unpack('>i', data[off+i*4:off+i*4+4])[0]
            matrix.append(val / 65536)
        parsed['matrix'] = matrix
        off += 36

    if off + 8 <= len(data):
        w = struct.unpack('>I', data[off:off+4])[0]
        h = struct.unpack('>I', data[off+4:off+8])[0]
        parsed['width_fixed'] = w
        parsed['height_fixed'] = h
        parsed['width'] = w >> 16
        parsed['height'] = h >> 16
        parsed['width_fraction'] = (w & 0xFFFF) / 65536
        parsed['height_fraction'] = (h & 0xFFFF) / 65536

    return parsed


def decode_lang(code):
    if code == 0: return "und (English default)"
    try:
        c1 = chr(((code >> 10) & 0x1F) + 0x60)
        c2 = chr(((code >> 5) & 0x1F) + 0x60)
        c3 = chr((code & 0x1F) + 0x60)
        return f"{c1}{c2}{c3}"
    except:
        return f"0x{code:04x}"


def parse_mdhd(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    ver = fullbox['version']

    if ver == 0:
        if off + 20 > len(data): return parsed
        parsed['creation_time'] = struct.unpack('>I', data[off:off+4])[0]
        parsed['creation_time_date'] = mac_time_to_datetime(parsed['creation_time'])
        parsed['modification_time'] = struct.unpack('>I', data[off+4:off+8])[0]
        parsed['modification_time_date'] = mac_time_to_datetime(parsed['modification_time'])
        parsed['timescale'] = struct.unpack('>I', data[off+8:off+12])[0]
        parsed['duration'] = struct.unpack('>I', data[off+12:off+16])[0]
        parsed['duration_formatted'] = format_duration(parsed['duration'], parsed['timescale'])
        parsed['language'] = struct.unpack('>H', data[off+16:off+18])[0]
        parsed['language_str'] = decode_lang(parsed['language'])
        parsed['quality'] = struct.unpack('>H', data[off+18:off+20])[0]
    else:
        if off + 32 > len(data): return parsed
        parsed['creation_time'] = struct.unpack('>Q', data[off:off+8])[0]
        parsed['creation_time_date'] = mac_time_to_datetime(parsed['creation_time'])
        parsed['modification_time'] = struct.unpack('>Q', data[off+8:off+16])[0]
        parsed['modification_time_date'] = mac_time_to_datetime(parsed['modification_time'])
        parsed['timescale'] = struct.unpack('>I', data[off+16:off+20])[0]
        parsed['duration'] = struct.unpack('>Q', data[off+20:off+28])[0]
        parsed['duration_formatted'] = format_duration(parsed['duration'], parsed['timescale'])
        parsed['language'] = struct.unpack('>H', data[off+28:off+30])[0]
        parsed['language_str'] = decode_lang(parsed['language'])
        parsed['quality'] = struct.unpack('>H', data[off+30:off+32])[0]

    return parsed


def parse_hdlr(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 12 > len(data): return parsed

    parsed['predefined'] = struct.unpack('>I', data[off:off+4])[0]
    parsed['handler_type'] = data[off+4:off+8].decode('ascii', errors='replace')
    parsed['handler_type_hex'] = data[off+4:off+8].hex()
    off += 12

    name_bytes = []
    while off < len(data) and off < offset + length and data[off] != 0:
        name_bytes.append(data[off])
        off += 1
    if name_bytes:
        parsed['component_name'] = bytes(name_bytes).decode('utf-8', errors='replace')

    return parsed


def parse_elst(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    ver = fullbox['version']

    if off + 4 > len(data): return parsed
    parsed['entry_count'] = struct.unpack('>I', data[off:off+4])[0]
    off += 4

    entries = []
    for i in range(parsed['entry_count']):
        if ver == 0:
            if off + 12 > len(data):
                parsed['truncated'] = True
                break
            entry = {
                'index': i,
                'segment_duration': struct.unpack('>I', data[off:off+4])[0],
                'media_time': struct.unpack('>i', data[off+4:off+8])[0],
                'media_time_hex': f"0x{struct.unpack('>I', data[off+4:off+8])[0]:08x}",
                'media_rate_integer': struct.unpack('>H', data[off+8:off+10])[0],
                'media_rate_fraction': struct.unpack('>H', data[off+10:off+12])[0],
                'size': 12
            }
            off += 12
        else:
            if off + 20 > len(data):
                parsed['truncated'] = True
                break
            entry = {
                'index': i,
                'segment_duration': struct.unpack('>Q', data[off:off+8])[0],
                'media_time': struct.unpack('>q', data[off+8:off+16])[0],
                'media_time_hex': f"0x{struct.unpack('>Q', data[off+8:off+16])[0]:016x}",
                'media_rate_integer': struct.unpack('>H', data[off+16:off+18])[0],
                'media_rate_fraction': struct.unpack('>H', data[off+18:off+20])[0],
                'size': 20
            }
            off += 20
        entries.append(entry)

    parsed['entries'] = entries
    parsed['entries_parsed'] = len(entries)
    parsed['total_entry_bytes'] = off - (offset + 8)

    flags_raw = struct.unpack('>I', data[offset:offset+4])[0]
    parsed['flags_raw_hex'] = f"0x{flags_raw:08x}"
    parsed['bypass_payload_detected'] = (flags_raw == 0x10000001)
    parsed['bypass_payload_v1'] = (flags_raw == 0x01000000)

    return parsed


def parse_stsd(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 4 > len(data): return parsed
    parsed['entry_count'] = struct.unpack('>I', data[off:off+4])[0]
    off += 4

    entries = []
    for i in range(parsed['entry_count']):
        if off + 8 > len(data):
            parsed['truncated'] = True
            break
        entry_size = struct.unpack('>I', data[off:off+4])[0]
        entry_type = data[off+4:off+8].decode('ascii', errors='replace')
        entry = {
            'index': i,
            'size': entry_size,
            'type': entry_type,
            'type_hex': data[off+4:off+8].hex(),
            'data_reference_index': struct.unpack('>H', data[off+8:off+10])[0] if off + 10 <= len(data) else None
        }

        if entry_type in ['avc1', 'hvc1', 'hev1', 'mp4v', 'av01']:
            if off + 78 <= len(data):
                entry['width'] = struct.unpack('>H', data[off+24:off+26])[0]
                entry['height'] = struct.unpack('>H', data[off+26:off+28])[0]
                entry['horizresolution'] = struct.unpack('>I', data[off+28:off+32])[0] / 65536
                entry['vertresolution'] = struct.unpack('>I', data[off+32:off+36])[0] / 65536
                entry['frame_count'] = struct.unpack('>H', data[off+40:off+42])[0]
                entry['depth'] = struct.unpack('>H', data[off+66:off+68])[0]
        elif entry_type in ['mp4a', 'aac ', 'ac-3', 'ec-3']:
            if off + 36 <= len(data):
                entry['channel_count'] = struct.unpack('>H', data[off+16:off+18])[0]
                entry['sample_size'] = struct.unpack('>H', data[off+18:off+20])[0]
                entry['sample_rate'] = struct.unpack('>I', data[off+24:off+28])[0] / 65536

        entries.append(entry)
        off += entry_size

    parsed['entries'] = entries
    return parsed


def parse_stsz(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 8 > len(data): return parsed

    parsed['sample_size'] = struct.unpack('>I', data[off:off+4])[0]
    parsed['sample_count'] = struct.unpack('>I', data[off+4:off+8])[0]
    off += 8

    if parsed['sample_size'] == 0 and parsed['sample_count'] > 0:
        sizes = []
        for i in range(min(parsed['sample_count'], MAX_ENTRIES_DISPLAY)):
            if off + 4 > len(data):
                parsed['truncated'] = True
                break
            sizes.append(struct.unpack('>I', data[off:off+4])[0])
            off += 4
        parsed['sample_sizes'] = sizes
        parsed['sample_sizes_total'] = sum(sizes) if sizes else 0
        if parsed['sample_count'] > MAX_ENTRIES_DISPLAY:
            parsed['sample_sizes_note'] = f"Showing first {MAX_ENTRIES_DISPLAY} of {parsed['sample_count']}"

    return parsed


def parse_stts(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 4 > len(data): return parsed

    parsed['entry_count'] = struct.unpack('>I', data[off:off+4])[0]
    off += 4

    entries = []
    total_samples = 0
    for i in range(min(parsed['entry_count'], MAX_ENTRIES_DISPLAY)):
        if off + 8 > len(data):
            parsed['truncated'] = True
            break
        count = struct.unpack('>I', data[off:off+4])[0]
        duration = struct.unpack('>I', data[off+4:off+8])[0]
        entries.append({'sample_count': count, 'sample_delta': duration})
        total_samples += count
        off += 8

    parsed['entries'] = entries
    parsed['total_samples'] = total_samples
    if parsed['entry_count'] > MAX_ENTRIES_DISPLAY:
        parsed['entries_note'] = f"Showing first {MAX_ENTRIES_DISPLAY} of {parsed['entry_count']}"

    return parsed


def parse_stsc(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 4 > len(data): return parsed

    parsed['entry_count'] = struct.unpack('>I', data[off:off+4])[0]
    off += 4

    entries = []
    for i in range(min(parsed['entry_count'], MAX_ENTRIES_DISPLAY)):
        if off + 12 > len(data):
            parsed['truncated'] = True
            break
        entries.append({
            'first_chunk': struct.unpack('>I', data[off:off+4])[0],
            'samples_per_chunk': struct.unpack('>I', data[off+4:off+8])[0],
            'sample_description_index': struct.unpack('>I', data[off+8:off+12])[0]
        })
        off += 12

    parsed['entries'] = entries
    if parsed['entry_count'] > MAX_ENTRIES_DISPLAY:
        parsed['entries_note'] = f"Showing first {MAX_ENTRIES_DISPLAY} of {parsed['entry_count']}"

    return parsed


def parse_stco(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 4 > len(data): return parsed

    parsed['entry_count'] = struct.unpack('>I', data[off:off+4])[0]
    off += 4

    offsets = []
    for i in range(min(parsed['entry_count'], MAX_ENTRIES_DISPLAY)):
        if off + 4 > len(data):
            parsed['truncated'] = True
            break
        offsets.append(struct.unpack('>I', data[off:off+4])[0])
        off += 4

    parsed['chunk_offsets'] = offsets
    parsed['first_offset'] = offsets[0] if offsets else None
    parsed['last_offset'] = offsets[-1] if offsets else None
    if parsed['entry_count'] > MAX_ENTRIES_DISPLAY:
        parsed['offsets_note'] = f"Showing first {MAX_ENTRIES_DISPLAY} of {parsed['entry_count']}"

    return parsed


def parse_co64(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 4 > len(data): return parsed

    parsed['entry_count'] = struct.unpack('>I', data[off:off+4])[0]
    off += 4

    offsets = []
    for i in range(min(parsed['entry_count'], MAX_ENTRIES_DISPLAY)):
        if off + 8 > len(data):
            parsed['truncated'] = True
            break
        offsets.append(struct.unpack('>Q', data[off:off+8])[0])
        off += 8

    parsed['chunk_offsets'] = offsets
    parsed['first_offset'] = offsets[0] if offsets else None
    if parsed['entry_count'] > MAX_ENTRIES_DISPLAY:
        parsed['offsets_note'] = f"Showing first {MAX_ENTRIES_DISPLAY} of {parsed['entry_count']}"

    return parsed


def parse_smhd(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 4 <= len(data):
        parsed['balance'] = struct.unpack('>h', data[off:off+2])[0] / 256
    return parsed


def parse_vmhd(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 8 <= len(data):
        parsed['graphicsmode'] = struct.unpack('>H', data[off:off+2])[0]
        parsed['opcolor'] = [
            struct.unpack('>H', data[off+2:off+4])[0],
            struct.unpack('>H', data[off+4:off+6])[0],
            struct.unpack('>H', data[off+6:off+8])[0]
        ]
    return parsed


def parse_dref(data, offset, length, fullbox):
    parsed = dict(fullbox)
    off = offset + 4
    if off + 4 > len(data): return parsed
    parsed['entry_count'] = struct.unpack('>I', data[off:off+4])[0]
    return parsed


ATOM_PARSERS = {
    'ftyp': parse_ftyp,
    'mvhd': parse_mvhd,
    'tkhd': parse_tkhd,
    'mdhd': parse_mdhd,
    'hdlr': parse_hdlr,
    'elst': parse_elst,
    'stsd': parse_stsd,
    'stsz': parse_stsz,
    'stts': parse_stts,
    'stsc': parse_stsc,
    'stco': parse_stco,
    'co64': parse_co64,
    'smhd': parse_smhd,
    'vmhd': parse_vmhd,
    'dref': parse_dref,
}


# ============================================================
# RECURSIVE ATOM SCANNER
# ============================================================

def scan_atoms(data, start=0, end=None, depth=0, parent_name="", max_depth=8):
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
            atoms.append({
                'offset': offset,
                'size': end - offset,
                'name': 'TRUNCATED',
                'header_size': 0,
                'data_start': offset,
                'data_size': end - offset,
                'depth': depth,
                'error': f'Invalid atom at offset {offset}, claimed size {size} exceeds parent boundary {end}'
            })
            break

        data_start = offset + header_size
        data_size = size - header_size

        atom_info = {
            'offset': offset,
            'size': size,
            'name': name,
            'header_size': header_size,
            'data_start': data_start,
            'data_size': data_size,
            'depth': depth,
            'parent': parent_name,
            'hex_preview': data[offset:offset+min(32, size)].hex(),
            'first_bytes': list(data[offset:offset+min(16, size)]),
        }

        if name in ATOM_PARSERS and data_size >= 4:
            fullbox = parse_fullbox(data, data_start)
            if fullbox:
                atom_info['fullbox'] = fullbox
                try:
                    atom_info['parsed'] = ATOM_PARSERS[name](data, data_start, data_size, fullbox)
                except Exception as e:
                    atom_info['parse_error'] = str(e)

        atoms.append(atom_info)

        if name in ['moov', 'trak', 'mdia', 'minf', 'stbl', 'edts', 'dinf', 'meta'] and depth < max_depth:
            child_start = data_start
            if name == 'meta' and data_size >= 4:
                child_start += 4

            children = scan_atoms(data, child_start, atom_end, depth + 1, name, max_depth)
            atoms.extend(children)

        offset = atom_end

    return atoms


# ============================================================
# PRINT FUNCTIONS
# ============================================================

def print_section(title, char="█", color=Colors.BOLD + Colors.BLUE):
    bar = char * 70
    print(f"\n{c(bar, color)}")
    print(c(f"  {title}", color))
    print(c(bar, color))


def print_subsection(title, char="─", color=Colors.YELLOW):
    bar = char * 70
    print(f"\n{c(bar, color)}")
    print(c(f"  {title}", Colors.BOLD + color))
    print(c(bar, color)}")


def print_tree(atoms, data):
    print_subsection("COMPLETE ATOM TREE", "═", Colors.CYAN)

    for atom in atoms:
        if atom['name'] == 'TRUNCATED':
            continue

        indent = "  " * atom['depth']
        size_kb = atom['size'] / 1024

        name_color = Colors.GREEN if atom['name'] == 'elst' else Colors.CYAN
        if atom['name'] == 'elst':
            name_color = Colors.BOLD + Colors.GREEN
        elif atom['name'] == 'mdat':
            name_color = Colors.YELLOW
        elif atom['name'] in ['moov', 'trak']:
            name_color = Colors.BOLD + Colors.CYAN

        line = f"{indent}├─ {c(atom['name'], name_color)} "
        line += f"offset={atom['offset']:<9} size={atom['size']:<9} ({size_kb:>8.2f} KB)"

        if 'parsed' in atom:
            p = atom['parsed']
            details = []

            if atom['name'] == 'elst':
                details.append(f"ver={p.get('version', '?')}")
                details.append(f"flags={p.get('flags_raw_hex', p.get('flags_hex', '?'))}")
                details.append(f"entries={p.get('entry_count', '?')}")
                if p.get('bypass_payload_detected'):
                    details.append(c("BYPASS v2 (0x10000001)", Colors.GREEN + Colors.BOLD))
                elif p.get('bypass_payload_v1'):
                    details.append(c("BYPASS v1 (0x01000000)", Colors.GREEN))

            elif atom['name'] == 'mvhd':
                details.append(f"timescale={p.get('timescale', '?')}")
                details.append(f"duration={p.get('duration_formatted', p.get('duration', '?'))}")
                details.append(f"rate={p.get('rate', '?')}")

            elif atom['name'] == 'tkhd':
                details.append(f"track_id={p.get('track_id', '?')}")
                details.append(f"{p.get('width', '?')}x{p.get('height', '?')}")
                details.append(f"enabled={p.get('track_enabled', '?')}")

            elif atom['name'] == 'mdhd':
                details.append(f"timescale={p.get('timescale', '?')}")
                details.append(f"duration={p.get('duration_formatted', p.get('duration', '?'))}")
                details.append(f"lang={p.get('language_str', '?')}")

            elif atom['name'] == 'hdlr':
                details.append(f"type={p.get('handler_type', '?')}")
                if 'component_name' in p:
                    details.append(f"name='{p['component_name']}'")

            elif atom['name'] == 'stsd':
                details.append(f"entries={p.get('entry_count', '?')}")
                if p.get('entries'):
                    types = [e['type'] for e in p['entries']]
                    details.append(f"codecs={','.join(types)}")

            elif atom['name'] == 'stsz':
                details.append(f"samples={p.get('sample_count', '?')}")
                if p.get('sample_size') == 0:
                    details.append(f"variable sizes")
                else:
                    details.append(f"fixed={p['sample_size']}")

            elif atom['name'] == 'stts':
                details.append(f"entries={p.get('entry_count', '?')}")
                details.append(f"total_samples={p.get('total_samples', '?')}")

            elif atom['name'] == 'stsc':
                details.append(f"entries={p.get('entry_count', '?')}")

            elif atom['name'] == 'stco' or atom['name'] == 'co64':
                details.append(f"chunks={p.get('entry_count', '?')}")
                if p.get('first_offset'):
                    details.append(f"first=0x{p['first_offset']:x}")

            if details:
                line += "  [" + " | ".join(details) + "]"

        if 'error' in atom:
            line += f"  {c(atom['error'], Colors.RED)}"

        print(line)


def print_hex_dumps(atoms, data):
    print_subsection("ATOM HEX DUMPS", "═", Colors.YELLOW)

    for atom in atoms:
        if atom['name'] in ['ftyp', 'free', 'udta']:
            continue

        indent = "  " * atom['depth']
        print(f"\n{indent}{c(atom['name'], Colors.BOLD + Colors.CYAN)} @ offset {atom['offset']} ({atom['size']} bytes)")

        dump_start = atom['offset']
        dump_size = min(atom['size'], MAX_HEX_DUMP)
        print(hex_dump(data[dump_start:dump_start+dump_size], dump_start, MAX_HEX_DUMP, indent + "  "))


def print_detailed_parsing(atoms):
    print_subsection("DETAILED ATOM PARSING", "═", Colors.GREEN)

    for atom in atoms:
        if 'parsed' not in atom:
            continue

        p = atom['parsed']
        name = atom['name']
        indent = "  " * atom['depth']

        print(f"\n{indent}{c(name.upper(), Colors.BOLD + Colors.GREEN)} @ offset {atom['offset']}")

        if 'fullbox' in atom:
            fb = atom['fullbox']
            print(f"{indent}  FullBox: version={fb['version']}, flags={fb['flags_hex']}")

        for key, value in p.items():
            if key in ['entries', 'sample_sizes', 'chunk_offsets', 'matrix']:
                continue
            if isinstance(value, list):
                print(f"{indent}  {c(key, Colors.YELLOW)}: {value}")
            elif isinstance(value, dict):
                print(f"{indent}  {c(key, Colors.YELLOW)}:")
                for k2, v2 in value.items():
                    print(f"{indent}    {k2}: {v2}")
            else:
                print(f"{indent}  {c(key, Colors.YELLOW)}: {value}")

        if 'entries' in p and p['entries']:
            print(f"{indent}  {c('ENTRIES', Colors.BOLD + Colors.YELLOW)}:")
            for entry in p['entries'][:MAX_ENTRIES_DISPLAY]:
                entry_str = ", ".join(f"{k}={v}" for k, v in entry.items())
                print(f"{indent}    - {entry_str}")
            if len(p['entries']) > MAX_ENTRIES_DISPLAY:
                remaining = len(p['entries']) - MAX_ENTRIES_DISPLAY
                print(f"{indent}    ... ({remaining} more entries)")

        if 'sample_sizes' in p and p['sample_sizes']:
            print(f"{indent}  {c('SAMPLE SIZES', Colors.BOLD + Colors.YELLOW)}: {p['sample_sizes'][:10]}")
            if len(p['sample_sizes']) > 10:
                print(f"{indent}    ... ({len(p['sample_sizes']) - 10} more)")

        if 'chunk_offsets' in p and p['chunk_offsets']:
            print(f"{indent}  {c('CHUNK OFFSETS', Colors.BOLD + Colors.YELLOW)}: {p['chunk_offsets'][:10]}")
            if len(p['chunk_offsets']) > 10:
                print(f"{indent}    ... ({len(p['chunk_offsets']) - 10} more)")

        if 'truncated' in p:
            print(f"{indent}  {c('WARNING: Data truncated', Colors.RED)}")

        if 'parse_error' in atom:
            print(f"{indent}  {c('PARSE ERROR: ' + atom['parse_error'], Colors.RED)}")


def print_raw_structure(atoms, data):
    print_subsection("RAW BINARY STRUCTURE", "═", Colors.DIM)

    for atom in atoms:
        indent = "  " * atom['depth']
        hex_preview = atom.get('hex_preview', '')[:64]
        first_bytes = atom.get('first_bytes', [])

        byte_analysis = []
        if first_bytes:
            printable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in first_bytes[:8])
            byte_analysis.append(f"ascii='{printable}'")
            if first_bytes[:4] == [0, 0, 0, 0]:
                byte_analysis.append("null padding")
            if any(b == 0 for b in first_bytes[:4]):
                byte_analysis.append("contains nulls")

        print(f"{indent}{atom['name']:4s} @ 0x{atom['offset']:08x}  "
              f"size=0x{atom['size']:08x}  "
              f"header={atom['header_size']}  "
              f"data=0x{atom['data_start']:08x}  "
              f"hex={hex_preview}  "
              f"{' | '.join(byte_analysis)}")


def print_statistics(atoms, data):
    print_subsection("FILE STATISTICS", "═", Colors.BOLD + Colors.BLUE)

    total_size = len(data)
    atom_types = {}
    total_atom_size = 0
    mdat_size = 0
    moov_size = 0

    for atom in atoms:
        atom_types[atom['name']] = atom_types.get(atom['name'], 0) + 1
        total_atom_size += atom['size']
        if atom['name'] == 'mdat':
            mdat_size = atom['size']
        elif atom['name'] == 'moov':
            moov_size = atom['size']

    print(f"  Total file size:        {total_size:,} bytes ({total_size/1048576:.2f} MB)")
    print(f"  Total atom size:        {total_atom_size:,} bytes")
    print(f"  Unaccounted bytes:      {total_size - total_atom_size:,}")
    print(f"  Number of atoms:        {len(atoms)}")
    print(f"  Unique atom types:      {len(atom_types)}")
    print(f"  mdat (media data):      {mdat_size:,} bytes ({mdat_size/total_size*100:.1f}%)")
    print(f"  moov (movie metadata):  {moov_size:,} bytes ({moov_size/total_size*100:.1f}%)")
    print(f"  metadata/media ratio:   {moov_size/max(mdat_size,1):.4f}")

    print(f"\n  {c('ATOM TYPE COUNTS', Colors.YELLOW)}:")
    for name, count in sorted(atom_types.items(), key=lambda x: -x[1]):
        print(f"    {name:8s}: {count}")


def print_elst_deep_analysis(atoms):
    print_subsection("ELST (EDIT LIST) DEEP ANALYSIS", "═", Colors.BOLD + Colors.RED)

    elst_atoms = [a for a in atoms if a['name'] == 'elst']

    if not elst_atoms:
        print(c("  No elst atoms found!", Colors.RED))
        return

    for i, atom in enumerate(elst_atoms):
        p = atom.get('parsed', {})
        print(f"\n  {c(f'ELST #{i+1}', Colors.BOLD)} @ offset {atom['offset']}")
        print(f"    Atom size:            {atom['size']} bytes")
        print(f"    Data size:            {atom['data_size']} bytes")
        print(f"    FullBox version:      {p.get('version', '?')}")
        print(f"    FullBox flags:        {p.get('flags_hex', '?')} (raw: {p.get('flags_raw_hex', '?')})")
        print(f"    Entry count:          {p.get('entry_count', '?')}")
        print(f"    Entries parsed:       {p.get('entries_parsed', '?')}")
        print(f"    Total entry bytes:    {p.get('total_entry_bytes', '?')}")

        if p.get('bypass_payload_detected'):
            print(f"    {c('WARNING: BYPASS PAYLOAD v2 DETECTED (0x10000001 = 268435457)', Colors.RED + Colors.BOLD)}")
            print(f"    {c('  This sets version=16 (undefined) and flags=0x000001', Colors.RED)}")
        elif p.get('bypass_payload_v1'):
            print(f"    {c('WARNING: BYPASS PAYLOAD v1 DETECTED (0x01000000)', Colors.YELLOW + Colors.BOLD)}")
            print(f"    {c('  This sets version=1 but likely mismatches entry structure', Colors.YELLOW)}")
        else:
            print(f"    {c('Clean elst (no bypass payload)', Colors.GREEN)}")

        if p.get('entries'):
            print(f"\n    {c('ENTRY ANALYSIS', Colors.BOLD)}:")
            for entry in p['entries'][:5]:
                print(f"      [{entry['index']}]")
                print(f"        segment_duration:  {entry.get('segment_duration', '?')}")
                print(f"        media_time:        {entry.get('media_time', '?')} (hex: {entry.get('media_time_hex', '?')})")
                print(f"        media_rate_int:    {entry.get('media_rate_integer', '?')}")
                print(f"        media_rate_frac:   {entry.get('media_rate_fraction', '?')}")

                mt = entry.get('media_time', 0)
                if mt == -1:
                    print(f"        {c('  -> media_time = -1 (empty edit / dwell)', Colors.YELLOW)}")
                elif mt < 0:
                    print(f"        {c('  -> NEGATIVE media_time (unusual)', Colors.RED)}")

                dur = entry.get('segment_duration', 0)
                if dur == 0:
                    print(f"        {c('  -> ZERO duration (immediate cut)', Colors.YELLOW)}")

        if p.get('truncated'):
            print(f"    {c('WARNING: Entry data truncated!', Colors.RED)}")


def print_track_summary(atoms):
    print_subsection("TRACK SUMMARY", "═", Colors.BOLD + Colors.CYAN)

    tracks = []
    current_track = None

    for atom in atoms:
        if atom['name'] == 'trak':
            current_track = {'atoms': [], 'tkhd': None, 'mdhd': None, 'hdlr': None}
            tracks.append(current_track)

        if current_track is not None:
            current_track['atoms'].append(atom)
            if atom['name'] == 'tkhd' and 'parsed' in atom:
                current_track['tkhd'] = atom['parsed']
            elif atom['name'] == 'mdhd' and 'parsed' in atom:
                current_track['mdhd'] = atom['parsed']
            elif atom['name'] == 'hdlr' and 'parsed' in atom:
                current_track['hdlr'] = atom['parsed']

    for i, track in enumerate(tracks):
        print(f"\n  {c(f'TRACK #{i+1}', Colors.BOLD + Colors.CYAN)}")

        if track['tkhd']:
            t = track['tkhd']
            print(f"    Track ID:        {t.get('track_id', '?')}")
            print(f"    Dimensions:      {t.get('width', '?')}x{t.get('height', '?')}")
            print(f"    Enabled:         {t.get('track_enabled', '?')}")
            print(f"    In Movie:        {t.get('track_in_movie', '?')}")
            print(f"    Layer:           {t.get('layer', '?')}")
            print(f"    Volume:          {t.get('volume', '?')}")

        if track['mdhd']:
            m = track['mdhd']
            print(f"    Timescale:       {m.get('timescale', '?')}")
            print(f"    Duration:        {m.get('duration_formatted', m.get('duration', '?'))}")
            print(f"    Language:        {m.get('language_str', '?')}")

        if track['hdlr']:
            h = track['hdlr']
            print(f"    Handler Type:    {h.get('handler_type', '?')}")
            if 'component_name' in h:
                print(f"    Handler Name:    '{h['component_name']}'")

        stbl_atoms = [a['name'] for a in track['atoms'] if a['name'] in ['stsd', 'stts', 'stsc', 'stsz', 'stco', 'co64', 'stss']]
        if stbl_atoms:
            print(f"    Sample Tables:   {', '.join(stbl_atoms)}")


def print_file_layout(atoms, data):
    print_subsection("FILE LAYOUT MAP", "═", Colors.DIM)

    print(f"  {'Offset':<12} {'Size':<12} {'End':<12} {'Type':<8} {'Content'}")
    print(f"  {'-'*11} {'-'*11} {'-'*11} {'-'*7} {'-'*40}")

    for atom in atoms:
        if atom['depth'] > 0:
            continue

        end = atom['offset'] + atom['size']
        content = ""

        if atom['name'] == 'ftyp':
            p = atom.get('parsed', {})
            content = f"brand={p.get('major_brand', '?')}"
        elif atom['name'] == 'mdat':
            content = f"media data ({atom['size']/1048576:.1f} MB)"
        elif atom['name'] == 'moov':
            content = f"movie metadata ({atom['size']/1024:.1f} KB)"
        elif atom['name'] == 'free':
            content = "padding"

        print(f"  0x{atom['offset']:08x}  0x{atom['size']:08x}  0x{end:08x}  {atom['name']:<7} {content}")


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_file(file_path, dump_hex=False, raw_mode=False):
    if not os.path.exists(file_path):
        print(c(f"ERROR: File not found: {file_path}", Colors.RED))
        return False

    with open(file_path, 'rb') as f:
        data = f.read()

    print_section(f"DEEP ANALYSIS: {os.path.basename(file_path)}")
    print(f"  Path: {os.path.abspath(file_path)}")
    print(f"  Size: {len(data):,} bytes ({len(data)/1048576:.2f} MB)")
    print(f"  Modified: {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}")

    atoms = scan_atoms(data)

    print_statistics(atoms, data)
    print_file_layout(atoms, data)
    print_tree(atoms, data)
    print_track_summary(atoms)
    print_elst_deep_analysis(atoms)
    print_detailed_parsing(atoms)

    if raw_mode:
        print_raw_structure(atoms, data)

    if dump_hex:
        print_hex_dumps(atoms, data)

    print_section("ANALYSIS COMPLETE", "█", Colors.GREEN)

    return atoms


# ============================================================
# COMPARISON MODE
# ============================================================

def compare_files(original_path, patched_path):
    print_section(f"COMPARISON: {os.path.basename(original_path)} vs {os.path.basename(patched_path)}")

    with open(original_path, 'rb') as f:
        orig_data = f.read()
    with open(patched_path, 'rb') as f:
        patch_data = f.read()

    print(f"\n  Original: {len(orig_data):,} bytes")
    print(f"  Patched:  {len(patch_data):,} bytes")
    print(f"  Delta:    {len(patch_data) - len(orig_data):,} bytes")

    diff_positions = []
    for i in range(min(len(orig_data), len(patch_data))):
        if orig_data[i] != patch_data[i]:
            diff_positions.append(i)

    print(f"\n  {c('BYTE-LEVEL DIFFERENCES', Colors.YELLOW)}:")
    print(f"    Total differing bytes: {len(diff_positions)}")

    if len(diff_positions) <= 20:
        for pos in diff_positions:
            print(f"    Offset 0x{pos:08x}: 0x{orig_data[pos]:02x} -> 0x{patch_data[pos]:02x}")
    else:
        if diff_positions:
            start = diff_positions[0]
            end = diff_positions[-1]
            print(f"    First diff: 0x{start:08x}")
            print(f"    Last diff:  0x{end:08x}")
            print(f"    Diff range: {end - start + 1} bytes")

            for pos in diff_positions[:10]:
                print(f"    Offset 0x{pos:08x}: 0x{orig_data[pos]:02x} -> 0x{patch_data[pos]:02x}")
            if len(diff_positions) > 10:
                print(f"    ... and {len(diff_positions) - 10} more")

    print(f"\n{c('═' * 70, Colors.CYAN)}")
    orig_atoms = scan_atoms(orig_data)
    patch_atoms = scan_atoms(patch_data)

    orig_elst = [a for a in orig_atoms if a['name'] == 'elst']
    patch_elst = [a for a in patch_atoms if a['name'] == 'elst']

    print_subsection("ELST COMPARISON", "─", Colors.RED)

    for o, p in zip(orig_elst, patch_elst):
        print(f"\n  Original elst @ {o['offset']}:")
        if 'parsed' in o:
            op = o['parsed']
            print(f"    version={op.get('version', '?')}, flags={op.get('flags_raw_hex', '?')}, entries={op.get('entry_count', '?')}")

        print(f"\n  Patched elst @ {p['offset']}:")
        if 'parsed' in p:
            pp = p['parsed']
            print(f"    version={pp.get('version', '?')}, flags={pp.get('flags_raw_hex', '?')}, entries={pp.get('entry_count', '?')}")
            if pp.get('bypass_payload_detected'):
                print(f"    {c('BYPASS PAYLOAD v2 CONFIRMED', Colors.GREEN + Colors.BOLD)}")
            elif pp.get('bypass_payload_v1'):
                print(f"    {c('BYPASS PAYLOAD v1 CONFIRMED', Colors.GREEN)}")


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='MP4 Deep Structure Analyzer - Complete binary dump',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python deep_analyze.py video.mp4\n  python deep_analyze.py video.mp4 --hex\n  python deep_analyze.py video.mp4 --raw\n  python deep_analyze.py orig.mp4 patched.mp4\n  python deep_analyze.py video.mp4 --json output.json"
    )
    parser.add_argument('files', nargs='+', help='MP4 file(s) to analyze')
    parser.add_argument('--hex', '-x', action='store_true', help='Include hex dumps')
    parser.add_argument('--raw', '-r', action='store_true', help='Include raw binary structure')
    parser.add_argument('--json', '-j', metavar='FILE', help='Export to JSON')
    parser.add_argument('--no-color', action='store_true', help='Disable colors')

    args = parser.parse_args()

    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    if len(args.files) == 1:
        atoms = analyze_file(args.files[0], dump_hex=args.hex, raw_mode=args.raw)

        if args.json and atoms:
            export = {
                'filename': os.path.basename(args.files[0]),
                'file_size': os.path.getsize(args.files[0]),
                'analysis_time': datetime.now().isoformat(),
                'atoms': atoms
            }
            with open(args.json, 'w') as f:
                json.dump(export, f, indent=2, default=str)
            print(f"\nExported to: {args.json}")

    elif len(args.files) == 2:
        compare_files(args.files[0], args.files[1])
    else:
        parser.error("Provide 1 file to analyze, or 2 files to compare")


if __name__ == "__main__":
    main()