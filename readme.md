# Multimedia Organizer Tool

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Python 3.13][python-shield]][python-url]
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

The Multimedia Organizer Tool processes all files in a source directory and copies them into a destination
directory, grouped by the day they were taken and by the camera that took them:

```
destination/2015-03-01/olympus_stylus1/photo.jpg
```

### Key Features:

* Capture date: read from the EXIF data (`DateTimeOriginal`, then `DateTimeDigitized`, then `DateTime`). Videos use
  the container creation date. If nothing is found, the file modification date is used.
* Camera folder: `make_model` from the EXIF data, lowercase and safe as a folder name (`Canon EOS 60D` -> `canoneos60d`).
  Files without camera information go directly in the date folder.
* Formats: gif, png, jpg, jpeg, heic, heif, webp, tif, tiff, mov, mp4, m4v, avi, 3gp, opus. Use `--extensions` to change them.
* Videos need [`ffprobe`](https://ffmpeg.org/) (part of FFmpeg) in the `PATH` to read their date and camera.
  Without it the modification date is used.
* Safe: files are copied by default and nothing is overwritten. Output names are always lowercase. If two different
  files end up with the same name the second one gets a suffix (`img_1.jpg`); identical files are skipped.
* Options: `--dry-run`, `--copy`/`--move`, `--folder-template` and `--skip-duplicates` (see below).
* Final report with copied, renamed, duplicated and failed files. The exit code is 1 if any file failed.

## Usage:

1) Prepare your directories:
   * Ensure you have a source directory containing your multimedia files.
   * Create or specify a destination directory where the organized files will be stored.
   

2) Run the tool:
    ```shell
    uv run reorganize.py --source /path/to/source/directory --destination /path/to/destination/directory
    ```

    Replace `/path/to/source/directory` with the path to your source directory and `/path/to/destination/directory` with 
    the path to your destination directory.


3) Example command:
    ```shell
    uv run reorganize.py --source /home/user/photos --destination /home/user/organized_photos
    ```
    This command will process all multimedia files in `/home/user/photos`, identify their dates, and 
    organize them into date-based subfolders in `/home/user/organized_photos`.

### Options

| Option | What it does |
|---|---|
| `--dry-run` | Shows what would happen (copies, renames, duplicates) and writes nothing. No confirmation is asked. |
| `--copy` | Copies the files and leaves the source untouched. This is the default; it cannot be combined with `--move`. |
| `--move` | Moves instead of copying. The source is deleted only after the copy has been verified byte by byte; duplicates are left in the source. Not available for MTP devices. |
| `--folder-template` | Sub folders of the destination. Fields: `{year}` `{month}` `{day}` `{date}` `{camera}`. Default `{date}/{camera}`. Example: `"{year}/{month}/{camera}"`. Empty parts (no camera) are dropped. |
| `--skip-duplicates` | Skips files whose content is identical to another file of the same run, whatever their name. Files with the same name and the same content are always skipped. |
| `--extensions` | Comma separated list of extensions to process. |
| `--debug` | Verbose log with tracebacks. |

### Example:

Given the source directory
```shell
 ~/Desktop/test  tree                                                                                                                                   ok | 15:53:04
.
├── Església St Pere de Rubí 150301_2014.JPG
├── a_file.txt
└── document.doc
```

Run the multimedia tool organizer command

```shell
python reorganize.py --source ~/Desktop/test/ --destination ~/Desktop/output/

[+] Start Processing
 |- Searching files... OK

------------------------
  Files Report
------------------------
 Extensions to be processed : ('.gif', '.png', '.jpg', '.jpeg', '.mov', '.mp4')
 Files found : 1 / 3

 Missing files   : 2 / 3
 Missed files have the following extensions: {'.doc', '.txt'}

Do you want to continue? yes/no > yes
[+] Reading files
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 35.23files/s]
[+] Creating directories
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 2126.93directory/s]
[+] Copying files
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 158.72file/s]
[+] All files were moved successfully!
```

Output directory result
```shell
 ~/Desktop/output  tree                                                                                                                                 ok | 15:47:55
.
└── 2015-03-01
    └── olympus_stylus1
        └── església st pere de rubí 150301_2014.jpg
```

## Getting Started

To get a local copy up and running follow these simple example steps.

### Installation

Install the project dependencies using [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

To be sure that everything is working as expected you can run the tests:
```shell
uv run pytest
```
## Developer
### Pre-commit hooks

Please run `uv run pre-commit install` just once to install the git hooks that allow performing some checks before committing. 
That will save us resources and time.

The pre-commit checks that we run are:

 * flake8
 * utf-8 encoding
 * correct JSON files

### Run the tests
```shell
uv run pytest
```

## Releases 
[Release History](releases.md)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[python-shield]: https://img.shields.io/badge/python-3.13-blue.svg
[python-url]: https://www.python.org/downloads/release/python-3130/
[contributors-shield]: https://img.shields.io/github/contributors/eballo/file-organizer.svg?style=flat-square
[contributors-url]: https://github.com/eballo/file-organizer/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/eballo/file-organizer.svg?style=flat-square
[forks-url]: https://github.com/eballo/file-organizer/network/members
[stars-shield]: https://img.shields.io/github/stars/eballo/file-organizer.svg?style=flat-square
[stars-url]: https://github.com/eballo/file-organizer/stargazers
[issues-shield]: https://img.shields.io/github/issues/eballo/file-organizer.svg?style=flat-square
[issues-url]: https://github.com/eballo/file-organizer/issues
