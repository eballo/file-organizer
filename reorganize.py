import argparse
import logging
import platform
import os
import sys
from typing import Tuple, Union, Any

from src.organizer import FileOrganizer
from src.utils import do_you_want_to_continue
import src.mtp_windows


def get_arguments() -> Tuple[bool, str, str, Tuple[Union[str, Any], ...], bool]:

    parser = argparse.ArgumentParser(description='Image Organizer')
    parser.add_argument('--source', metavar='source', type=str, help='the path where the images are located')
    parser.add_argument('--destination', metavar='destination', type=str,
                        help='the destination path where the images will be ordered')
    parser.add_argument('--extensions', metavar='extensions', type=str,
                        help='the filter extensions coma separated. Default extensions: gif, png, jpg, jpeg, mov, mp4')
    parser.add_argument('--debug', help='enables debug log', action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.INFO)

    args = parser.parse_args()
    init_logger(args.loglevel)

    extensions: Tuple[Union[str, Any], ...] = None
    is_mtp = False
    app_source = args.source
    if app_source:
        if not app_source.endswith(os.path.sep):
            app_source = args.source + os.path.sep
        if not os.path.isdir(app_source):
            logging.warning('[-] The source path specified does not exist')
            sys.exit()
    else:
        if any(platform.win32_ver()):
            logging.info(' |- Running under windows ')
            logging.info(" |- Select MTP device...")
            devices = []
            for idx, device in enumerate(src.mtp_windows.get_portable_devices()):
                logging.info(" |-> %d  %s" % (idx, device.getDescription()))
                devices.append(device.getDescription())
            if len(devices) > 0:
                try:
                    idx_device = int(input("Please enter device number [0..%d] ..: " % (len(devices)-1)))
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
    # Force PIL to warning level always
    logging.getLogger("PIL").setLevel(logging.WARNING)


if __name__ == '__main__':
    is_mtp, source, destination, extensions, debug = get_arguments()

    init_logger(debug)
    logging.debug("[+] Parameters: source= %s, destination= %s, extennsions= %s, debug= %s", source, destination,
                  extensions, debug)
    image_organizer = FileOrganizer(is_mtp, source, destination, extensions)
    #try:
    logging.debug("[+] Starting")
    image_organizer.start()
    #except Exception as err:
    #    if debug == logging.DEBUG:
    #        error_msg = f"Unexpected {err=}, {type(err)=}"
    #    else:
    #        error_msg = "[-] Something went really wrong"
    #    logging.error(error_msg)
    logging.debug("[+] Finish")
