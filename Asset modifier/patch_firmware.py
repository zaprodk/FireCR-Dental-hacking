#!/usr/bin/env python3
"""Firmware Patcher: Safely injects Splash and Sleep graphics 
while surgically preserving the hidden factory wipe frame (Frame 1.B).
"""

import argparse
import struct
from PIL import Image

SOF_MAGIC = b"SoF\x00\x40\x01\xf0\x00"
BLOCK_SIZE = 0x80000  # 512 KB per language block
TOTAL_BLOCKS = 14

def rgb888_to_rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

def encode_rle(pixels):
    encoded = []
    i = 0
    n = len(pixels)
    while i < n:
        val = pixels[i]
        run = 1
        while i + run < n and pixels[i + run] == val and run < 32767:
            run += 1
        if run >= 2:
            encoded.append(run)
            encoded.append(val)
            i += run
        else:
            lit = [pixels[i]]
            i += 1
            while i < n and len(lit) < 32767:
                if i + 1 < n and pixels[i] == pixels[i + 1]:
                    break
                lit.append(pixels[i])
                i += 1
            encoded.append(-len(lit))
            encoded.extend(lit)
    return encoded

def patch_firmware(clean_exe, output_exe, splash_img=None, sleep_img=None):
    with open(clean_exe, "rb") as f:
        exe_data = bytearray(f.read())

    base = exe_data.find(SOF_MAGIC)
    if base == -1:
        raise ValueError("Could not locate UI asset table.")

    # 1. Patch Splash (Frame 0)
    if splash_img:
        img = Image.open(splash_img).convert("RGB")
        raw = [rgb888_to_rgb565(p[0], p[1], p[2]) for p in list(img.getdata())]
        words = encode_rle(raw)
        wc = len(words)
        payload = struct.pack(f"<{wc}H", *(v & 0xFFFF for v in words))
        
        for b in range(TOTAL_BLOCKS):
            b_base = base + (b * BLOCK_SIZE)
            exe_data[b_base + 0x00010 : b_base + 0x00014] = struct.pack("<I", wc)
            exe_data[b_base + 0x00014 : b_base + 0x00014 + len(payload)] = payload
        print(f"[+] Splash injected into {TOTAL_BLOCKS} blocks ({wc} words)")

    # 2. Patch Sleep (Frame 1) without killing the Wipe Frame
    if sleep_img:
        img = Image.open(sleep_img).convert("RGB")
        raw = [rgb888_to_rgb565(p[0], p[1], p[2]) for p in list(img.getdata())]
        words = encode_rle(raw)
        wc = len(words)
        
        # Max safe words before hitting the hidden Wipe Frame header at 0x05FBE
        MAX_SAFE_WORDS = 4011 
        if wc > MAX_SAFE_WORDS:
            raise ValueError(f"Graphic is {wc} words. Must be < {MAX_SAFE_WORDS} to preserve wipe frame.")
            
        payload = struct.pack(f"<{wc}H", *(v & 0xFFFF for v in words))
        
        # Pad with zeros strictly up to 8022 bytes, leaving 0x05FBE perfectly intact
        padded_payload = payload + (b"\x00" * ((MAX_SAFE_WORDS * 2) - len(payload)))
        
        for b in range(TOTAL_BLOCKS):
            b_base = base + (b * BLOCK_SIZE)
            
            # The factory expects wc to bridge both the image AND the wipe frame header,
            # so we must leave the main header wc at 4019. We ONLY inject the padded payload.
            exe_data[b_base + 0x04068 : b_base + 0x04068 + len(padded_payload)] = padded_payload
            
        print(f"[+] Sleep graphic safely injected ({wc} words). Wipe Frame preserved.")

    with open(output_exe, "wb") as f_out:
        f_out.write(exe_data)
    print(f"[+] Generated: {output_exe}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("exe")
    parser.add_argument("--splash")
    parser.add_argument("--sleep")
    parser.add_argument("-o", "--output", default="DentalCR_SystemUpdater_Patched.exe")
    args = parser.parse_args()
    patch_firmware(args.exe, args.output, args.splash, args.sleep)