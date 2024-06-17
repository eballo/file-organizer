# Multimedia Organizer Tool

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=bluecodex_file-organizer&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=bluecodex_file-organizer)

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Python 3.12][python-shield]][python-url]
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]

The Multimedia Organizer Tool is designed to streamline and automate the organization of multimedia files within a 
specified folder. This powerful utility processes all files in a given source directory, identifies their modification 
dates, and systematically sorts them into subfolders within a designated destination directory. Each subfolder is named 
according to the date format YYYY-MM-DD, corresponding to the modification date of the files it contains. 

This tool ensures that all media files are neatly organized by date, making it easier to manage and locate them.

### Key Features:

* Automatic Sorting: Efficiently processes and sorts multimedia files by their modification date.
* Date-Based Folders: Creates subfolders in the destination directory named after the modification date in YYYY-MM-DD format.
* Comprehensive File Support: Supports a wide range of multimedia files, including images, videos, and audio files.
* User-Friendly: Simple and easy to use, with minimal setup required.

## Usage:

1) Prepare your directories:
   * Ensure you have a source directory containing your multimedia files.
   * Create or specify a destination directory where the organized files will be stored.
   

2) Run the tool:
    ```shell
    python organize_media.py --source /path/to/source/directory --destination /path/to/destination/directory
    ```

    Replace `/path/to/source/directory` with the path to your source directory and `/path/to/destination/directory` with 
    the path to your destination directory.


3) Example command:
    ```shell
    python organize_media.py --source /home/user/photos --destination /home/user/organized_photos
    ```
    This command will process all multimedia files in `/home/user/photos`, identify their modification dates, and 
    organize them into date-based subfolders in `/home/user/organized_photos`.

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
└── 2024-06-14
    └── stylus1
        └── església st pere de rubí 150301_2014.jpg
```

## Getting Started

To get a local copy up and running follow these simple example steps.

### Installation

Install the project dependencies

```sh
pyenv virtualenv 3.12.1 image
pyenv local image
pip install -r requirements.txt
```

To be sure that everything is working as expected you can run the tests
```shell
pytest                                                                           ok | image 3.8.6 py | 15:40:20
========================================================================= test session starts =========================================================================
platform darwin -- Python 3.12.1, pytest-8.2.2, pluggy-1.5.0
rootdir: /Users/eballo/Documents/work/python/file-organizer
collected 9 items

tests/test_organizer.py .....                                                                                                                                   [ 55%]
tests/test_process.py ....                                                                                                                                      [100%]

========================================================================== 9 passed in 0.21s ==========================================================================

```
## Developer
### Pre-commit hooks

Please run  `pre-commit install` just once to install the git hooks that allow to preform some checks before commiting. 
That will save us resources and time

The pre-commit checks that we run are:

 * flake8
 * utf-8 encoding
 * correct JSON files

### Run the tests
From inside the test directory
```shell
$image-organizer/tests/python -m pytest tests
```

## Releases 
[Release History](releases.md)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[python-shield]: https://img.shields.io/badge/python-3.12-blue.svg
[python-url]: https://www.python.org/downloads/release/python-3124/
[contributors-shield]: https://img.shields.io/github/contributors/eballo/file-organizer.svg?style=flat-square
[contributors-url]: https://github.com/eballo/file-organizer/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/eballo/file-organizer.svg?style=flat-square
[forks-url]: https://github.com/eballo/file-organizer/network/members
[stars-shield]: https://img.shields.io/github/stars/eballo/file-organizer.svg?style=flat-square
[stars-url]: https://github.com/eballo/file-organizer/stargazers
[issues-shield]: https://img.shields.io/github/issues/eballo/file-organizer.svg?style=flat-square
[issues-url]: https://github.com/eballo/file-organizer/issues
