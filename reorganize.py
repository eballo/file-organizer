import argparse
import logging
import platform
import os
import sys
import textwrap
from typing import Tuple, Union, Any

from src.organizer import FileOrganizer, FileOrganizerWin32
from src.utils import do_you_want_to_continue


def get_arguments() -> Tuple[bool, str, str, Tuple[Union[str, Any], ...], bool]:
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent('''\
    [ Multimedia Organizer Tool ]

    The Multimedia Organizer Tool is designed to streamline and automate the organization of multimedia files within 
    a specified folder. This powerful utility processes all files in a given source directory, identifies their 
    modification dates, and systematically sorts them into subfolders within a designated destination directory. 
    Each subfolder is named according to the date format YYYY-MM-DD, corresponding to the modification date of the 
    files it contains. This tool ensures that all media files are neatly organized by date, making it easier to manage 
    and locate them.
    
    Usage:

    1) Specify the source directory containing the multimedia files.
    2) Choose the destination directory where the organized files will be stored.
    3) The tool will automatically scan the source directory, determine the modification date of each file, and 
    move or copy the files to the appropriate date-based subfolder in the destination directory.


    '''))
    parser.add_argument('--source', metavar='source', type=str,
                        help='the path where the images are located', required=True)
    parser.add_argument('--destination', metavar='destination', type=str,
                        help='the destination path where the images will be ordered',  required=True)
    parser.add_argument('--extensions', metavar='extensions', type=str,
                        help='the filter extensions coma separated. Default extensions: gif, png, jpg, jpeg, mov, mp4')
    parser.add_argument('--debug', help='enables debug log',
                        action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)

    args = parser.parse_args()
    init_logger(args.loglevel)

    extensions: Tuple[Union[str, Any], ...] = None
    is_mtp: bool = False
    app_source = args.source
    if app_source:
        if not app_source.endswith(os.path.sep):
            app_source = args.source + os.path.sep
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

    if args.destination:
        if os.path.isdir(args.destination):
            logging.warning("[-] The destination path specified already exist")
            do_you_want_to_continue()
    else:
        logging.warning('[-] The "destination" parameter is mandatory')
        sys.exit()

    if args.extensions:
        ext = args.extensions.replace(" ", "")
        ext_list = ext.split(",")
        extensions = tuple(["." + t for t in ext_list])

    app_debug = False
    if args.loglevel:
        app_debug = True

    return is_mtp, app_source, args.destination, extensions, app_debug


def init_logger(level):
    if level == logging.DEBUG:
        logging.basicConfig(format='%(levelname)s\t : %(message)s', level=level)
    else:
        logging.basicConfig(format='%(message)s', level=level)
    # Force PIL to warn level always
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_file_organizer(is_w32: bool, src: str, dest: str, ext: Tuple[Union[str, Any], ...]) -> FileOrganizer:
    if is_w32:
        return FileOrganizerWin32(src, dest, ext)
    else:
        return FileOrganizer(src, dest, ext)


if __name__ == '__main__':
    is_mtp, source, destination, extensions, debug = get_arguments()

    try:
        init_logger(debug)
        logging.debug("[+] Parameters: source= %s, destination= %s, extennsions= %s, debug= %s", source, destination,
                      extensions, debug)
        image_organizer = get_file_organizer(is_mtp, source, destination, extensions)
        logging.debug("[+] Starting")
        image_organizer.start()
    except Exception as err:
        if debug == logging.DEBUG:
            error_msg = f"Unexpected {err=}, {type(err)=}"
        else:
            error_msg = "[-] Something went really wrong"
        logging.error(error_msg)
    logging.debug("[+] Finish")
