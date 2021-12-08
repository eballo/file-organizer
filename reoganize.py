import argparse
import os
import sys
from typing import Tuple, Union, Any
from src.organizer import FileOrganizer


def get_arguments() -> Tuple[str, str, Tuple[Union[str, Any], ...]]:
    parser = argparse.ArgumentParser(description='Image Organizer')
    parser.add_argument('--source', metavar='source', type=str, help='the path where the images are located')
    parser.add_argument('--destination', metavar='destination', type=str,
                        help='the destination path where the images will be ordered')
    parser.add_argument('--extensions', metavar='extensions', type=str,
                        help='the filter extensions coma separated. Default extensions: gif, png, jpg, jpeg, mov, mp4')
    args = parser.parse_args()

    extensions: Tuple[Union[str, Any], ...] = None
    if args.source:
        if not os.path.isdir(args.source):
            print('The source path specified does not exist')
            sys.exit()

    if args.destination:
        if os.path.isdir(args.destination):
            print('The destination path specified already exist')
            sys.exit()

    if args.extensions:
        ext = args.extensions + ","
        ext_list = ext.split(",")
        extensions = tuple(["*." + t.replace(" ", "") for t in ext_list])

    return args.source, args.destination, extensions


if __name__ == '__main__':
    source, destination, extensions = get_arguments()
    image_organizer = FileOrganizer(source, destination, extensions)
    image_organizer.start()
