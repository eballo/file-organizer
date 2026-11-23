import argparse
import logging
import platform
import os
import sys
import textwrap
from dataclasses import dataclass
from typing import Tuple, Union, Any, Optional

from src.layout import FolderTemplate
from src.organizer import FileOrganizer, FileOrganizerWin32
from src.process import FileProcessor, FileProcessorWin32
from src.utils import do_you_want_to_continue


@dataclass
class Options:
    is_mtp: bool
    source: str
    destination: str
    extensions: Optional[Tuple[Union[str, Any], ...]]
    debug: bool
    template: FolderTemplate
    dry_run: bool = False
    move: bool = False
    skip_duplicates: bool = False


def get_arguments() -> Options:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent('''\
    [ Multimedia Organizer Tool ]

    The Multimedia Organizer Tool is designed to streamline and automate the organization of multimedia files within 
    a specified folder. This powerful utility processes all files in a given source directory, identifies their 
    capture dates, and systematically sorts them into subfolders within a designated destination directory. 
    Each subfolder is named according to the date format YYYY-MM-DD, corresponding to the capture date of the 
    files it contains. This tool ensures that all media files are neatly organized by date, making it easier to manage 
    and locate them.
    
    Usage:

    1) Specify the source directory containing the multimedia files.
    2) Choose the destination directory where the organized files will be stored.
    3) The tool will automatically scan the source directory, determine the capture date of each file, and 
    copy the files to the appropriate date-based subfolder in the destination directory.


    '''))
    parser.add_argument('--source', metavar='source', type=str,
                        help='the path where the images are located', required=True)
    parser.add_argument('--destination', metavar='destination', type=str,
                        help='the destination path where the images will be ordered',  required=True)
    parser.add_argument('--extensions', metavar='extensions', type=str,
                        help='the filter extensions coma separated. Default extensions: gif, png, jpg, jpeg, mov, mp4')
    parser.add_argument('--folder-template', metavar='template', type=str, default=FolderTemplate.DEFAULT,
                        help='sub folders created in the destination. Fields: {year} {month} {day} {date} {camera}. '
                             'Default: "%s". Example: "{year}/{month}/{camera}"' % FolderTemplate.DEFAULT)
    parser.add_argument('--dry-run', action='store_true',
                        help='shows what would be done (including renames and duplicates) without writing anything')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--copy', action='store_true',
                      help='copies the files and leaves the source untouched (default)')
    mode.add_argument('--move', action='store_true',
                      help='moves the files instead of copying them: the source is only deleted after the copy '
                           'has been verified')
    parser.add_argument('--skip-duplicates', action='store_true',
                        help='skips files whose content is identical to another file of this run, whatever their name')
    parser.add_argument('--debug', help='enables debug log',
                        action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)

    args = parser.parse_args()
    init_logger(args.loglevel)

    try:
        template = FolderTemplate(args.folder_template)
    except ValueError as err:
        parser.error(f'--folder-template: {err}')

    extensions: Tuple[Union[str, Any], ...] = None
    is_mtp: bool = False
    app_source = args.source
    if app_source:
        if not os.path.isdir(app_source):
            logging.warning('[-] The source path specified does not exist')
            sys.exit()
    else:
        if any(platform.win32_ver()):
            import src.mtp_windows

            logging.info(' |- Running under windows ')
            logging.info(" |- Select MTP device...")
            devices = []
            for idx, device in enumerate(src.mtp_windows.get_portable_devices()):
                logging.info(" |-> %d  %s" % (idx, device.getDescription()))
                devices.append(device.getDescription())
            if len(devices) > 0:
                try:
                    idx_device = int(input("Please enter device number [0..%d] ..: " % (len(devices) - 1)))
                except Exception:
                    logging.warning('[-] Invalid value')
                    sys.exit()
                if idx_device >= len(devices) or idx_device < 0:
                    logging.warning('[-] Invalid value')
                    sys.exit()
                else:
                    app_source = devices[idx_device]
                    is_mtp = True
            else:
                logging.warning('[-] MTP devices not found')
                sys.exit()
        else:
            logging.warning('[-] The "source" parameter is mandatory')
            sys.exit()

    app_destination = args.destination
    if app_destination:
        if os.path.isdir(app_destination) and not args.dry_run:
            logging.warning("[-] The destination path specified already exist")
            do_you_want_to_continue()
    else:
        logging.warning('[-] The "destination" parameter is mandatory')
        sys.exit()

    if args.extensions:
        ext = args.extensions.replace(" ", "")
        ext_list = ext.split(",")
        extensions = tuple(["." + t for t in ext_list])

    if is_mtp and args.move:
        parser.error('--move is not supported for devices (MTP)')

    return Options(is_mtp, app_source, app_destination, extensions, args.loglevel == logging.DEBUG, template,
                   args.dry_run, args.move, args.skip_duplicates)


def init_logger(level):
    if level == logging.DEBUG:
        logging.basicConfig(format='%(levelname)s\t : %(message)s', level=level)
    else:
        logging.basicConfig(format='%(message)s', level=level)
    # Force PIL to warn level always
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_file_organizer(options: Options) -> FileOrganizer:
    processor_class, organizer_class = (FileProcessorWin32, FileOrganizerWin32) if options.is_mtp else (
        FileProcessor, FileOrganizer)
    processor = processor_class(template=options.template, dry_run=options.dry_run, move=options.move,
                                skip_duplicates=options.skip_duplicates)
    return organizer_class(options.source, options.destination, options.extensions, processor)


if __name__ == '__main__':
    opts = get_arguments()

    try:
        logging.debug("[+] Parameters: %s", opts)
        image_organizer = get_file_organizer(opts)
        logging.debug("[+] Starting")
        report = image_organizer.start()
        if report and report.failed:
            sys.exit(1)
    except Exception as err:
        logging.error("[-] Something went really wrong: %s", err, exc_info=opts.debug)
        sys.exit(1)
    logging.debug("[+] Finish")
