# FireCR / DentalCR Firmware Asset Patcher

A Python tool to reverse-engineer, modify, and repack the embedded UI graphics (Boot Splash and Sleep screens) in the FireCR / DentalCR scanner firmware updater.

This script parses the raw executable (`DentalCR_SystemUpdater_1.1.2.exe`), encodes standard PNG images into the proprietary 16-bit RGB565 RLE format expected by the STM32 display controller, and injects them safely across all 14 language blocks in the firmware.

## Features
* **Custom Boot Splash (Frame 0):** Replace the startup logo.
* **Custom Sleep Screen (Frame 1):** Replace the factory stopwatch animation with a custom graphic (e.g., a sleeping cat).
* **Safe Injection:** Surgically patches the firmware without overwriting downstream string tables or the hidden UI "wipe" frame, ensuring the physical touch screen menus remain 100% glitch-free.

## Requirements
* Python 3.x
* Pillow (`pip install Pillow`)

## Usage

Place your clean firmware executable, the patcher script, and your PNG images in the same folder. 

Run the script via command line:
```cmd
python patch_firmware.py DentalCR_SystemUpdater_1.1.2.exe --splash splash_img.png --sleep sleep_img.png -o DentalCR_SystemUpdater_Patched.exe
```

You can then run `DentalCR_SystemUpdater_Patched.exe` to flash the custom assets to the scanner.

## Image Design Guidelines (CRITICAL)

The STM32 embedded GUI (emWin/SEGGER) on this device is strictly hardware-constrained. **Your PNGs must adhere to these rules**, otherwise the UI will glitch or the scanner will drop the image.

### 1. `splash_img.png` (Boot Screen)
* **Dimensions:** `320x240` pixels.
* **Format:** Standard RGB PNG.
* **Limit:** Must compress to under **8,226 words** (16,452 bytes) when RLE encoded. (Tip: Use flat colors and limit color count to keep the RLE stream small).

### 2. `sleep_img.png` (Sleep Screen Overlay)
The sleep screen is **not** a full-screen wallpaper. It is a partial-window overlay drawn on top of the home screen dashboard.
* **Dimensions:** `320x240` pixels canvas.
* **Hardware Transparency:** The background color of the canvas **must be pure black `RGB(0, 0, 0)`**. The display controller uses `0x0000` as a hardware chroma key. It will not paint these pixels, allowing the firmware's native UI to show through seamlessly.
* **Bounding Box:** Your actual artwork must be centered horizontally (center = `x:158`) and completely stay **above row 155**. The window manager physically clips the bottom 1/3rd of the screen during sleep mode to preserve the home screen icons and the "Touch to Awake" text.
* **Limit:** Must compress to under **4,011 words** (8,022 bytes). Quantizing your image to 8 or 16 colors is highly recommended.

## Technical Details / Reverse Engineering Notes

During the development of this tool, several quirks of the FireCR firmware were mapped out:
1. **Language Blocks:** The firmware payload is split into 14 distinct blocks (512 KB each) separated by a `SoF` magic header. The patcher updates all 14 blocks simultaneously so the active language setting on the device doesn't load corrupt pointers.
2. **Custom RLE Compression:** The device uses a custom Run-Length Encoding stream based on 16-bit Little-Endian RGB565 words. Positive tokens indicate a run of identical pixels; negative tokens indicate a literal run of uncompressed pixels.
3. **The Hidden Wipe Frame:** Frame 1 is strictly capped at 4,011 words. The 16 bytes immediately following it at offset `0x05FBE` contain a hidden 320x210 solid-color wipe frame used by the GUI to erase dashboard debris. Previous blind-padding methods destroyed this header, causing UI corruption. This script pads the exact byte difference, preserving the wipe frame perfectly.

## Disclaimer
*This tool is provided for educational and research purposes. Modifying device firmware carries inherent risks. The author is not responsible for bricked devices, voided warranties, or broken equipment. Always keep a backup of the original factory updater.*