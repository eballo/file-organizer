# File Organizer

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

The goal of this project is to organize all the multimedia files from a given folder.
The output will be a folder (YYYY-MM-DD format), and all media data that belongs to that date inside.

Source
```shell
 ~/Desktop/test > tree
.
├── 48e9a3cb-454c-4b57-b17b-a8751ac12938_Original.jpg
├── IMG-20190720-WA0000.jpg
├── IMG-20190720-WA0010.jpg
└── IMG_20190719_153829.jpg
```

Output

```shell
python reorganize.py --source ~/Desktop/test2/ --destination ~/Desktop/out/
[+] Start Processing

------------------------
  Files Report
------------------------
 Extensions to be processed : ('.gif', '.png', '.jpg', '.jpeg', '.mov', '.mp4')
 Files found : 4 / 4

 Missing files   : 0 / 0
 Missed files have the following extensions: -

Do you want to continue? yes/no > yes
[+] All files were moved successfully!
 
~/Desktop/out > tree
.
├── 2019-07-19
│   └── pixel3a
│       └── IMG_20190719_153829.jpg
├── 2019-07-20
│   ├── IMG-20190720-WA0000.jpg
│   └── IMG-20190720-WA0010.jpg
└── 2019-12-14
    └── nikond5200
        └── 48e9a3cb-454c-4b57-b17b-a8751ac12938_Original.jpg
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

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[python-shield]: https://img.shields.io/badge/python-3.8-blue.svg
[python-url]: https://www.python.org/downloads/release/python-370/
[contributors-shield]: https://img.shields.io/github/contributors/eballo/snake-pygame.svg?style=flat-square
[contributors-url]: https://github.com/eballo/snake-pygame/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/eballo/snake-pygame.svg?style=flat-square
[forks-url]: https://github.com/eballo/snake-pygame/network/members
[stars-shield]: https://img.shields.io/github/stars/eballo/snake-pygame.svg?style=flat-square
[stars-url]: https://github.com/eballo/snake-pygame/stargazers
[issues-shield]: https://img.shields.io/github/issues/eballo/snake-pygame.svg?style=flat-square
[issues-url]: https://github.com/eballo/snake-pygame/issues
