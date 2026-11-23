# Roadmap

What is done, what is planned and why. Past versions are listed in [releases.md](releases.md).

Status legend: **Done**, **Planned**, **Idea** (not committed to).

## Done

* Capture date from EXIF (`DateTimeOriginal`, `DateTimeDigitized`, `DateTime`), with the file modification date as fallback.
* Camera folder as `make_model`, safe on every OS. HEIC/HEIF support and video metadata through `ffprobe`.
* Output names are always lowercase. Name clashes never overwrite anything: identical files are skipped, different files get a numeric suffix. A final report lists copied, renamed, duplicate and failed files.
* `--dry-run`, `--copy`/`--move` (the source is deleted only after the copy is verified), `--folder-template`, `--skip-duplicates`.
* Windows portable devices (MTP) reachable again: `--source` is optional on Windows. Covered by tests with a simulated device.
* `file-organizer` command (`uv tool install`), flake8 in CI, working pre-commit config.

## Planned

### Epic: Rename the `src` and `gen` packages to `file_organizer`

**Status:** Planned. **Priority:** low, not blocking anything today.

**Why**

* The project installs two top-level packages called `src` and `gen`. Those names are far too generic: in a shared Python environment (`pip install` next to other projects) they can collide with any other project that made the same choice, and they say nothing about what they contain.
* With `uv tool install` or `pipx` this is harmless, because every tool gets its own isolated environment. That is why the `file-organizer` command could ship without the rename (see the packaging PR). The rename is what makes a plain `pip install` safe too.
* It cannot be done at install time. The code imports itself as `src.*` and `gen.*`, and a wheel can move files but cannot rewrite imports. Having one name for development and another for the installed package would mean relative imports everywhere and two names for the same code. The only clean way is to rename at the source.
* It makes the code import path match the distribution name (`file-organizer` / `file_organizer`), which is what contributors expect.

**Scope**

1. `git mv src file_organizer`; update every `src.` import in the package, `reorganize.py` and the tests.
2. `git mv gen file_organizer/_com`; update the single import in `file_organizer/mtp_windows.py`. The generated COM modules are not edited.
3. Update `pyproject.toml` (`only-include`, entry point), `setup.cfg`, the coverage settings and the CI lint paths.
4. Keep the root `reorganize.py` as a thin wrapper so `python reorganize.py` keeps working.
5. Do it in a single PR that contains only the rename, so it can be reviewed by reading the file moves.

**Done when**

* `uv run pytest`, `flake8` and the packaging smoke test in CI pass.
* `pip install .` in a clean virtualenv, followed by `file-organizer --help` and a run on a sample folder, works.
* `src` and `gen` no longer appear in the installed wheel.
* The MTP flow has been checked on a real Windows machine with a phone (see the next epic). This is the main risk: the generated modules import each other by name and the automated tests only use a simulated device.

**Depends on:** ideally after the real-device validation below, so a Windows regression can be told apart from a rename regression.

### Epic: Validate the MTP flow on real hardware

**Status:** Planned. **Priority:** medium.

**Why:** the Windows portable-device code (`mtp_windows.py` and the generated COM modules) cannot run on the machines used for development and CI. The code around it is tested with an in-memory device, but nobody has run the whole flow since it became reachable again.

**Scope**

* Run the tool against a real phone: device selection, recursive listing, EXIF/device dates, copy, name clashes, a large video.
* Fix anything found and, where possible, turn it into a simulated-device test.
* Consider a `windows-latest` job in CI that at least imports the module and runs the unit tests.

**Done when:** a documented manual run (device model, number of files, result) and no open Windows bugs.

## Ideas

* **Duplicates against files already in the destination.** `--skip-duplicates` only compares files of the same run. A size index of the destination would extend it, at the cost of reading it first.
* **More formats.** RAW files (CR2, NEF, ARW, DNG) through `exiftool` or a Pillow-compatible reader, implemented as a new `MetadataReader`.
* **Better date for files without metadata.** Parse dates from file names such as `IMG_20230501_123456.jpg` or `VID-20230501-WA0001.mp4` before falling back to the modification date.
* **Configuration file.** Remember the folder template and extensions per user instead of repeating them on the command line.
* **Undo manifest.** Write a log of what was copied or moved so a run can be reverted.
