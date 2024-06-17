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
[![Python 3.8][python-shield]][python-url]
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
pyenv virtualenv 3.8.6 image
pyenv local image
pip install -r requirements.txt
```

To be sure that everything is working as expected you can run the tests
```shell
pytest                                                                           ok | image 3.8.6 py | 15:40:20
========================================================================= test session starts =========================================================================
platform darwin -- Python 3.8.6, pytest-6.2.5, py-1.11.0, pluggy-1.5.0
rootdir: /Users/eballo/Documents/work/python/file-organizer
collected 9 items

tests/test_organizer.py .....                                                                                                                                   [ 55%]
tests/test_process.py ....                                                                                                                                      [100%]

========================================================================== 9 passed in 0.21s ==========================================================================

```

### Run
```sh 
python reorganize.py --help
usage: reorganize.py [-h] [--source source] [--destination destination] [--types types]

Image Organizer

optional arguments:
  -h, --help            show this help message and exit
  --source source       the path where the images are located
  --destination destination
                        the destination path where the images will be ordered
  --types types         the filter types coma separated. Default types: gif, png, jpg, jpeg, mov, mp4
```

Sample with specific extensions
```shell
python reorganize.py --source ~/Desktop/Media --destination ~/Desktop/out/ --extensions opus,jpg,mp3
[+] Start Processing

------------------------
  Files Report
------------------------
 Extensions to be processed : ('.opus', '.jpg', '.mp3')
 Files found : 2735 / 3369

 Missing files   : 634 / 3369
 Missed files have the following extensions: {'.webp', '.pdf', '.aac', '.', '.jpeg', '.mp4', '.m4a'}

Do you want to continue? yes/no > yes
[+] All files were moved successfully!
```
Debug sample:
```shell
python reorganize.py --source ~/Desktop/Media --destination ~/Desktop/out/ --debug
WARNING	 : [-] The destination path specified already exist
Do you want to continue? yes/no > yes
DEBUG	 : [+] Parameters: source= /Users/eballo/Desktop/Media/, destination= /Users/eballo/Desktop/out/, extennsions= None, debug= True
DEBUG	 : [+] Starting
INFO	 : [+] Start Processing
INFO	 :
INFO	 : ------------------------
INFO	 :   Files Report
INFO	 : ------------------------
INFO	 :  Extensions to be processed : ('.gif', '.png', '.jpg', '.jpeg', '.mov', '.mp4')
INFO	 :  Files found : 1935 / 3369
INFO	 :
INFO	 :  Missing files   : 1434 / 3369
INFO	 :  Missed files have the following extensions: {'.', '.aac', '.pdf', '.m4a', '.webp', '.mp3', '.opus'}
INFO	 :
Do you want to continue? yes/no > yes
INFO	 : [-] Output directory already exists
INFO	 : [+] All files were moved successfully!
DEBUG	 : [+] Finish
```


### Pre-commit hooks

Please run  `pre-commit install` just once to install the git hooks that allow
that allow to preform some checks before commiting. That will save us resouces and time

The pre-commit checks that we run are:

 * flake8
 * utf-8 encoding
 * correct JSON files

### Run the tests
From inside the test directory
```shell
$image-organizer/tests/python -m pytest tests
```

## Release History

* 1.0
    * Create directories
    * add exif model information if any
    * copy in parallel 10 threads

* 2.0
    * code refactor
    * update readme
    * add tests
    * Fix bug capitalized extensions
    * Fix EXIF information issue (omotto)
    * Add Logging
    * Fix when source os separator missing, recursive not working
    * Add Debug parameter, Info by default
    * Add Missing files format summary (Debug)
  
* 3.0
    * Add Progress Bar (@omotto contribution)
    * Add Win32 support (@omotto contribution)
    * Refactor code to have Win32 configuration in a separate class
    * Add Tests
    * Add Pull Request Template
    * Add github actions build + tests + sonar
    * Improve Tool Help
    * Improve Readme

* 4.0
    * Fix destination parameter when there is no separator


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[python-shield]: https://img.shields.io/badge/python-3.8-blue.svg
[python-url]: https://www.python.org/downloads/release/python-370/
[contributors-shield]: https://img.shields.io/github/contributors/eballo/file-organizer.svg?style=flat-square
[contributors-url]: https://github.com/eballo/file-organizer/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/eballo/file-organizer.svg?style=flat-square
[forks-url]: https://github.com/eballo/file-organizer/network/members
[stars-shield]: https://img.shields.io/github/stars/eballo/file-organizer.svg?style=flat-square
[stars-url]: https://github.com/eballo/file-organizer/stargazers
[issues-shield]: https://img.shields.io/github/issues/eballo/file-organizer.svg?style=flat-square
[issues-url]: https://github.com/eballo/file-organizer/issues
