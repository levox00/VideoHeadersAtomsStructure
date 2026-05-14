# VideoHeadersAtomsStructure
Give out detailed information about mp4 videos.

Usage:
Place main.py in videos directory
Open cmd in that directory

# Full analysis with everything
> python main.py outputFinal.mp4 --hex --raw

# Compare original vs patched
> python main.py original.mp4 outputFinal.mp4

# Export to JSON for further processing
> python main.py outputFinal.mp4 --json data.json

:)

Example output:
```


C:\Users\leand\Desktop\testVIdeos>python validate.py clip3.mp4

██████████████████████████████████████████████████████████████████████
  DEEP ANALYSIS: clip3.mp4
██████████████████████████████████████████████████████████████████████
  Path: C:\Users\leand\Desktop\testVIdeos\clip3.mp4
  Size: 9,776,337 bytes (9.32 MB)
  Modified: 2026-05-10 00:41:22

══════════════════════════════════════════════════════════════════════
  FILE STATISTICS
══════════════════════════════════════════════════════════════════════
  Total file size:        9,776,337 bytes (9.32 MB)
  Total atom size:        9,812,096 bytes
  Unaccounted bytes:      -35,759
  Number of atoms:        44
  Unique atom types:      26
  mdat (media data):      9,734,976 bytes (99.6%)
  moov (movie metadata):  7,569 bytes (0.1%)
  metadata/media ratio:   0.0008

  ATOM TYPE COUNTS:
    hdlr    : 4
    trak    : 2
    tkhd    : 2
    edts    : 2
    elst    : 2
    mdia    : 2
    mdhd    : 2
    minf    : 2
    dinf    : 2
    dref    : 2
    stbl    : 2
    stsd    : 2
    stts    : 2
    stsc    : 2
    stsz    : 2
    stco    : 2
    ftyp    : 1
    moov    : 1
    mvhd    : 1
    vmhd    : 1
    stss    : 1
    sdtp    : 1
    smhd    : 1
    udta    : 1
    uuid    : 1
    mdat    : 1

══════════════════════════════════════════════════════════════════════
  FILE LAYOUT MAP
══════════════════════════════════════════════════════════════════════
  Offset       Size         End          Type     Content
  ----------- ----------- ----------- ------- ----------------------------------------
  0x00000000  0x00000018  0x00000018  ftyp    brand=?
  0x00000018  0x00001d91  0x00001da9  moov    movie metadata (7.4 KB)
  0x00001da9  0x000083e8  0x0000a191  uuid
  0x0000a191  0x00948b40  0x00952cd1  mdat    media data (9.3 MB)

══════════════════════════════════════════════════════════════════════
  COMPLETE ATOM TREE
══════════════════════════════════════════════════════════════════════
├─ ftyp offset=0         size=24        (    0.02 KB)
├─ moov offset=24        size=7569      (    7.39 KB)
  ├─ mvhd offset=32        size=108       (    0.11 KB)  [timescale=90000 | duration=0:06.74 (6.741s) | rate=1.0]
  ├─ trak offset=140       size=5094      (    4.97 KB)
    ├─ tkhd offset=148       size=92        (    0.09 KB)  [track_id=1 | 0x25956 | enabled=True]
    ├─ edts offset=240       size=36        (    0.04 KB)
      ├─ elst offset=248       size=28        (    0.03 KB)  [ver=0 | flags=0x00000000 | entries=1]
    ├─ mdia offset=276       size=4958      (    4.84 KB)
      ├─ mdhd offset=284       size=32        (    0.03 KB)  [timescale=120000 | duration=0:06.71 (6.708s) | lang=eng]
      ├─ hdlr offset=316       size=64        (    0.06 KB)  [type=vide]
      ├─ minf offset=380       size=4854      (    4.74 KB)
        ├─ vmhd offset=388       size=20        (    0.02 KB)
        ├─ hdlr offset=408       size=51        (    0.05 KB)  [type=alis]
        ├─ dinf offset=459       size=36        (    0.04 KB)
          ├─ dref offset=467       size=28        (    0.03 KB)
        ├─ stbl offset=495       size=4739      (    4.63 KB)
          ├─ stsd offset=503       size=146       (    0.14 KB)  [entries=1 | codecs=avc1]
          ├─ stts offset=649       size=24        (    0.02 KB)  [entries=1 | total_samples=805]
          ├─ stsc offset=673       size=40        (    0.04 KB)  [entries=2]
          ├─ stsz offset=713       size=3240      (    3.16 KB)  [samples=805 | variable sizes]
          ├─ stco offset=3953      size=340       (    0.33 KB)  [chunks=81 | first=0xa1a1]
          ├─ stss offset=4293      size=124       (    0.12 KB)
          ├─ sdtp offset=4417      size=817       (    0.80 KB)
  ├─ trak offset=5234      size=2310      (    2.26 KB)
    ├─ tkhd offset=5242      size=92        (    0.09 KB)  [track_id=2 | 0x25956 | enabled=True]
    ├─ edts offset=5334      size=36        (    0.04 KB)
      ├─ elst offset=5342      size=28        (    0.03 KB)  [ver=0 | flags=0x00000000 | entries=1]
    ├─ mdia offset=5370      size=2174      (    2.12 KB)
      ├─ mdhd offset=5378      size=32        (    0.03 KB)  [timescale=48000 | duration=0:06.74 (6.741s) | lang=eng]
      ├─ hdlr offset=5410      size=68        (    0.07 KB)  [type=soun]
      ├─ minf offset=5478      size=2066      (    2.02 KB)
        ├─ smhd offset=5486      size=16        (    0.02 KB)
        ├─ hdlr offset=5502      size=51        (    0.05 KB)  [type=alis]
        ├─ dinf offset=5553      size=36        (    0.04 KB)
          ├─ dref offset=5561      size=28        (    0.03 KB)
        ├─ stbl offset=5589      size=1955      (    1.91 KB)
          ├─ stsd offset=5597      size=91        (    0.09 KB)  [entries=1 | codecs=mp4a]
          ├─ stts offset=5688      size=24        (    0.02 KB)  [entries=1 | total_samples=316]
          ├─ stsc offset=5712      size=208       (    0.20 KB)  [entries=16]
          ├─ stsz offset=5920      size=1284      (    1.25 KB)  [samples=316 | variable sizes]
          ├─ stco offset=7204      size=340       (    0.33 KB)  [chunks=81 | first=0x20828]
  ├─ udta offset=7544      size=49        (    0.05 KB)
├─ uuid offset=7593      size=33768     (   32.98 KB)
├─ mdat offset=41361     size=9734976   ( 9506.81 KB)

══════════════════════════════════════════════════════════════════════
  TRACK SUMMARY
══════════════════════════════════════════════════════════════════════

  TRACK #1
    Track ID:        1
    Dimensions:      0x25956
    Enabled:         True
    In Movie:        True
    Layer:           1
    Volume:          0.0
    Timescale:       120000
    Duration:        0:06.71 (6.708s)
    Language:        eng
    Handler Type:    alis
    Sample Tables:   stsd, stts, stsc, stsz, stco, stss

  TRACK #2
    Track ID:        2
    Dimensions:      0x25956
    Enabled:         True
    In Movie:        False
    Layer:           1
    Volume:          0.0
    Timescale:       48000
    Duration:        0:06.74 (6.741s)
    Language:        eng
    Handler Type:    alis
    Sample Tables:   stsd, stts, stsc, stsz, stco

══════════════════════════════════════════════════════════════════════
  ELST (EDIT LIST) DEEP ANALYSIS
══════════════════════════════════════════════════════════════════════

  ELST #1 @ offset 248
    Atom size:            28 bytes
    Data size:            20 bytes
    FullBox version:      0
    FullBox flags:        0x000000 (raw: 0x00000000)
    Entry count:          1
    Entries parsed:       1
    Total entry bytes:    12
    Clean elst (no bypass payload)

    ENTRY ANALYSIS:
      [0]
        segment_duration:  603750
        media_time:        0 (hex: 0x00000000)
        media_rate_int:    1
        media_rate_frac:   0

  ELST #2 @ offset 5342
    Atom size:            28 bytes
    Data size:            20 bytes
    FullBox version:      0
    FullBox flags:        0x000000 (raw: 0x00000000)
    Entry count:          1
    Entries parsed:       1
    Total entry bytes:    12
    Clean elst (no bypass payload)

    ENTRY ANALYSIS:
      [0]
        segment_duration:  603750
        media_time:        0 (hex: 0x00000000)
        media_rate_int:    1
        media_rate_frac:   0

══════════════════════════════════════════════════════════════════════
  DETAILED ATOM PARSING
══════════════════════════════════════════════════════════════════════

  MVHD @ offset 32
    FullBox: version=0, flags=0x000000
    version: 0
    flags: 0
    flags_hex: 0x000000
    creation_time: 3861211282
    creation_time_date: 2026-05-09 22:41:22 UTC
    modification_time: 3861211282
    modification_time_date: 2026-05-09 22:41:22 UTC
    timescale: 90000
    duration: 606720
    duration_formatted: 0:06.74 (6.741s)
    rate: 1.0
    volume: 1.0
    matrix_preview: [1.0000, 0.0000, 0.0000, ...]
    next_track_id: 0

    TKHD @ offset 148
      FullBox: version=0, flags=0x000007
      version: 0
      flags: 7
      flags_hex: 0x000007
      track_enabled: True
      track_in_movie: True
      track_in_preview: True
      creation_time: 3861211282
      modification_time: 3861211282
      track_id: 1
      duration: 603750
      layer: 1
      alternate_group: 0
      volume: 0.0
      width_fixed: 36
      height_fixed: 1701082227
      width: 0
      height: 25956
      width_fraction: 0.00054931640625
      height_fraction: 0.4548797607421875

      ELST @ offset 248
        FullBox: version=0, flags=0x000000
        version: 0
        flags: 0
        flags_hex: 0x000000
        entry_count: 1
        entries_parsed: 1
        total_entry_bytes: 12
        flags_raw_hex: 0x00000000
        bypass_payload_detected: False
        bypass_payload_v1: False
        ENTRIES:
          - index=0, segment_duration=603750, media_time=0, media_time_hex=0x00000000, media_rate_integer=1, media_rate_fraction=0, size=12

      MDHD @ offset 284
        FullBox: version=0, flags=0x000000
        version: 0
        flags: 0
        flags_hex: 0x000000
        creation_time: 3861211282
        creation_time_date: 2026-05-09 22:41:22 UTC
        modification_time: 3861211282
        modification_time_date: 2026-05-09 22:41:22 UTC
        timescale: 120000
        duration: 805000
        duration_formatted: 0:06.71 (6.708s)
        language: 5575
        language_str: eng
        quality: 0

      HDLR @ offset 316
        FullBox: version=0, flags=0x000000
        version: 0
        flags: 0
        flags_hex: 0x000000
        predefined: 0
        handler_type: vide
        handler_type_hex: 76696465

        VMHD @ offset 388
          FullBox: version=0, flags=0x000001
          version: 0
          flags: 1
          flags_hex: 0x000001
          graphicsmode: 0
          opcolor: [0, 0, 0]

        HDLR @ offset 408
          FullBox: version=0, flags=0x000000
          version: 0
          flags: 0
          flags_hex: 0x000000
          predefined: 0
          handler_type: alis
          handler_type_hex: 616c6973

          DREF @ offset 467
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 1

          STSD @ offset 503
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 1
            ENTRIES:
              - index=0, size=130, type=avc1, type_hex=61766331, data_reference_index=0, width=0, height=0, horizresolution=0.0, vertresolution=1080.029296875, frame_count=72, depth=0

          STTS @ offset 649
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 1
            total_samples: 805
            ENTRIES:
              - sample_count=805, sample_delta=1000

          STSC @ offset 673
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 2
            ENTRIES:
              - first_chunk=1, samples_per_chunk=10, sample_description_index=1
              - first_chunk=81, samples_per_chunk=5, sample_description_index=1

          STSZ @ offset 713
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            sample_size: 0
            sample_count: 805
            sample_sizes_total: 91783
            sample_sizes_note: Showing first 10 of 805
            SAMPLE SIZES: [64103, 1189, 1828, 2533, 2971, 2597, 3416, 3895, 4246, 5005]

          STCO @ offset 3953
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 81
            first_offset: 41377
            last_offset: 1173661
            offsets_note: Showing first 10 of 81
            CHUNK OFFSETS: [41377, 135865, 202375, 297784, 505276, 589790, 687896, 919713, 1047284, 1173661]

    TKHD @ offset 5242
      FullBox: version=0, flags=0x000001
      version: 0
      flags: 1
      flags_hex: 0x000001
      track_enabled: True
      track_in_movie: False
      track_in_preview: False
      creation_time: 3861211282
      modification_time: 3861211282
      track_id: 2
      duration: 603750
      layer: 1
      alternate_group: 0
      volume: 0.0
      width_fixed: 36
      height_fixed: 1701082227
      width: 0
      height: 25956
      width_fraction: 0.00054931640625
      height_fraction: 0.4548797607421875

      ELST @ offset 5342
        FullBox: version=0, flags=0x000000
        version: 0
        flags: 0
        flags_hex: 0x000000
        entry_count: 1
        entries_parsed: 1
        total_entry_bytes: 12
        flags_raw_hex: 0x00000000
        bypass_payload_detected: False
        bypass_payload_v1: False
        ENTRIES:
          - index=0, segment_duration=603750, media_time=0, media_time_hex=0x00000000, media_rate_integer=1, media_rate_fraction=0, size=12

      MDHD @ offset 5378
        FullBox: version=0, flags=0x000000
        version: 0
        flags: 0
        flags_hex: 0x000000
        creation_time: 3861211282
        creation_time_date: 2026-05-09 22:41:22 UTC
        modification_time: 3861211282
        modification_time_date: 2026-05-09 22:41:22 UTC
        timescale: 48000
        duration: 323584
        duration_formatted: 0:06.74 (6.741s)
        language: 5575
        language_str: eng
        quality: 0

      HDLR @ offset 5410
        FullBox: version=0, flags=0x000000
        version: 0
        flags: 0
        flags_hex: 0x000000
        predefined: 0
        handler_type: soun
        handler_type_hex: 736f756e

        SMHD @ offset 5486
          FullBox: version=0, flags=0x000000
          version: 0
          flags: 0
          flags_hex: 0x000000
          balance: 0.0

        HDLR @ offset 5502
          FullBox: version=0, flags=0x000000
          version: 0
          flags: 0
          flags_hex: 0x000000
          predefined: 0
          handler_type: alis
          handler_type_hex: 616c6973

          DREF @ offset 5561
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 1

          STSD @ offset 5597
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 1
            ENTRIES:
              - index=0, size=75, type=mp4a, type_hex=6d703461, data_reference_index=0, channel_count=0, sample_size=0, sample_rate=2.000244140625

          STTS @ offset 5688
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 1
            total_samples: 316
            ENTRIES:
              - sample_count=316, sample_delta=1024

          STSC @ offset 5712
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 16
            entries_note: Showing first 10 of 16
            ENTRIES:
              - first_chunk=1, samples_per_chunk=4, sample_description_index=1
              - first_chunk=11, samples_per_chunk=3, sample_description_index=1
              - first_chunk=12, samples_per_chunk=4, sample_description_index=1
              - first_chunk=22, samples_per_chunk=3, sample_description_index=1
              - first_chunk=23, samples_per_chunk=4, sample_description_index=1
              - first_chunk=32, samples_per_chunk=3, sample_description_index=1
              - first_chunk=33, samples_per_chunk=4, sample_description_index=1
              - first_chunk=43, samples_per_chunk=3, sample_description_index=1
              - first_chunk=44, samples_per_chunk=4, sample_description_index=1
              - first_chunk=54, samples_per_chunk=3, sample_description_index=1

          STSZ @ offset 5920
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            sample_size: 0
            sample_count: 316
            sample_sizes_total: 7783
            sample_sizes_note: Showing first 10 of 316
            SAMPLE SIZES: [167, 845, 848, 845, 847, 846, 847, 846, 846, 846]

          STCO @ offset 7204
            FullBox: version=0, flags=0x000000
            version: 0
            flags: 0
            flags_hex: 0x000000
            entry_count: 81
            first_offset: 133160
            last_offset: 1412525
            offsets_note: Showing first 10 of 81
            CHUNK OFFSETS: [133160, 198989, 294399, 501890, 586405, 684511, 916328, 1043898, 1170276, 1412525]

██████████████████████████████████████████████████████████████████████
  ANALYSIS COMPLETE
██████████████████████████████████████████████████████████████████████

C:\Users\leand\Desktop\testVIdeos>
```
