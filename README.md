# RecoverX

RecoverX is a Python toolkit for scanning Android Gallery cache files and carving JPEG and PNG image candidates from cached binary data.

RecoverX identifies image signatures and saves best-effort candidates. It does not guarantee photo recovery or restore deleted originals.

## Features

- Scan one cache file or recursively scan a directory.
- Report JPEG/PNG signature counts and byte offsets.
- Stream large inputs in bounded memory.
- Carve JPEG candidates using JPEG start and end markers.
- Carve PNG candidates by parsing chunk lengths through the IEND chunk.
- Write candidates into separate `jpeg` and `png` folders with unique, non-overwriting names.
- Save truncated candidates when a matching end marker is absent and report them as partial.
- Work with files already copied to the computer; ADB is optional.
- Use only the Python standard library at runtime.

## How it works

The scanner searches binary data for the JPEG start signature (`FF D8 FF`) and PNG signature (`89 50 4E 47 0D 0A 1A 0A`). It reports signatures, not confirmed photographs. The extractor uses JPEG start/end markers and PNG chunk boundaries through IEND to carve candidate byte ranges.

Recovered candidates may be partial, duplicated, blurred, corrupted, or invalid. RecoverX does not fully decode or validate image contents and may encounter false-positive signatures.

## Supported formats

- JPEG (`FF D8 FF` start marker and `FF D9` end marker)
- PNG (8-byte signature and IEND chunk)

## Prerequisites

- Python 3.10 or newer.
- Optional: Android Platform Tools (`adb`) for copying files from a connected phone.
- No third-party Python dependencies are required.

## Installation

Clone or download this repository, then from its root run:

```powershell
python -m pip install -e .
```

The editable install is optional; the commands below also work directly from the repository root without installation. `requirements.txt` intentionally contains no package dependencies.

## Usage

Show help:

```powershell
python recoverx.py --help
python recoverx.py scan --help
python recoverx.py extract --help
```

Scan a cache file or directory:

```powershell
python recoverx.py scan "path/to/cache"
```

Extract candidates into separate `jpeg` and `png` subfolders:

```powershell
python recoverx.py extract "path/to/cache" --output "GalleryRecovery"
```

Convenience wrappers are also available:

```powershell
python scripts/scan_cache.py "path/to/cache"
python scripts/extract_cache.py "path/to/cache" --output "GalleryRecovery"
```

For example, after copying the files below into a local `phone-cache` folder:

```powershell
python recoverx.py scan ".\phone-cache"
python recoverx.py extract ".\phone-cache" --output ".\GalleryRecovery"
```

The extraction summary reports the number of candidates, including those that reached end-of-file without an end marker. It does not label candidates as confirmed recovered photos.

## Android ADB workflow (optional)

1. Install Android SDK Platform Tools from the official Android developer website and ensure `adb` is available in your terminal.
2. On the phone, enable Developer options (typically by tapping **Build number** several times under **Settings > About phone**), then enable **USB debugging** in Developer options.
3. Connect the phone to the computer using USB. Unlock the phone and accept the computer's USB debugging authorization prompt.
4. Verify the connection:

   ```powershell
   adb devices
   ```

   The device should appear with status `device`. If it says `unauthorized`, unlock the phone and accept the prompt.

5. Locate cache paths on the device. Gallery cache locations vary by Android version, vendor, and app. `adb shell` can be used to inspect accessible storage. For example, check common shared-storage locations:

   ```powershell
   adb shell "find /sdcard/Android/data -type f \( -name imgcache.0 -o -name screennailcache.0 \) 2>/dev/null"
   ```

   Access to app-private directories may be restricted; do not attempt to bypass Android security. Use only locations and data you are authorized to access.

6. Copy any accessible cache files to a local folder before scanning. Replace the sample device paths with paths reported on your own device:

   ```powershell
   New-Item -ItemType Directory -Force ".\phone-cache"
   adb pull "/sdcard/path/to/imgcache.0" ".\phone-cache\imgcache.0"
   adb pull "/sdcard/path/to/screennailcache.0" ".\phone-cache\screennailcache.0"
   ```

7. Run RecoverX against the copied files:

   ```powershell
   python recoverx.py scan ".\phone-cache"
   python recoverx.py extract ".\phone-cache" --output ".\GalleryRecovery"
   ```

ADB is used only to read/copy files in this workflow. RecoverX itself operates on local paths and never deletes or modifies files on the phone. Back up important device data before any recovery-related work.

## Limitations and troubleshooting

- Gallery caches may be missing, overwritten, inaccessible, or different from the example filenames. Their locations and formats vary across devices and software versions.
- A matching signature does not establish that an image is complete, valid, unique, or a deleted original.
- Cache entries may be thumbnails or screen-sized previews rather than original-resolution photos.
- JPEG extraction uses the first following end marker; malformed data or embedded markers may produce imperfect boundaries.
- PNG extraction uses declared chunk lengths and the IEND chunk but does not validate CRCs or decode pixels.
- Truncated candidates are saved up to the next recognized signature or the end of the input file, and counted as partial.
- The tool does not bypass permissions, decrypt data, or recover content that is no longer present in the scanned bytes.
- If a path is missing or unreadable, verify the local copy's path and your operating-system permissions. Copy device data to the computer before processing.
- If `adb devices` shows no device, check the USB cable, USB mode, drivers where applicable, and USB debugging authorization.

In one previous experiment, 10,499 candidates were reported from `imgcache.0` and 3,317 from `screennailcache.0` (13,816 total). These are results from that experiment only, not expected or guaranteed results for other files or devices.

## Privacy and data safety

Process only files you own or are authorized to access. Cache files and extracted candidates can contain private information. Keep them in a secure location, do not upload them to public repositories, and review output paths before sharing logs or results. The `.gitignore` excludes common cache, backup, credential, and generated-recovery paths, but always verify staged files before committing. RecoverX does not alter the source cache or phone data.

## Testing

Run the standard-library test suite from the repository root:

```powershell
python -m unittest discover -s tests -v
```

Check syntax:

```powershell
python -m compileall -q recoverx.py recoverx scripts tests
```

Tests construct synthetic signatures and markers in temporary files; no personal photos or real device cache files are required.

## Contributing

Contributions are welcome. Please open an issue to discuss substantial changes, keep changes focused, add or update tests, and run the test and syntax-check commands above. Do not include personal images, device cache data, backups, or credentials in issues or pull requests.

## License

Released under the MIT License. See [LICENSE](LICENSE).
