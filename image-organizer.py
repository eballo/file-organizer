import argparse
import os
import sys
import glob
from typing import List, Tuple

from src.process import FileProcessor

DEFAULT_EXTENSION = ('*.gif', '*.png', '*.jpg', '*.jpeg', '*.mov', '*.mp4')


class ImageOrganizer:

    def __init__(self, extensions=None):
        self.file_process = FileProcessor()
        self.extensions = extensions if extensions is not None else DEFAULT_EXTENSION

    @staticmethod
    def get_arguments():
        parser = argparse.ArgumentParser(description='Image Organizer')
        parser.add_argument('--source', metavar='source', type=str, help='the path where the images are located')
        parser.add_argument('--destination', metavar='destination', type=str,
                            help='the destination path where the images will be ordered')
        parser.add_argument('--types', metavar='types', type=str,
                            help='the filter types coma separated. Default types: gif, png, jpg, jpeg, mov, mp4')
        args = parser.parse_args()

        extensions = None
        if args.source:
            if not os.path.isdir(args.source):
                print('The source path specified does not exist')
                sys.exit()

        if args.destination:
            if os.path.isdir(args.destination):
                print('The destination path specified already exist')
                sys.exit()

        if args.types:
            types = args.types + ","
            types_list = types.split(",")
            extensions = tuple(["*." + t.replace(" ", "") for t in types_list])

        return args.source, args.destination, extensions

    @staticmethod
    def get_all_files(source: str, ):
        matches = []
        for filename in glob.iglob(source + '**' + os.path.sep + '*.*', recursive=True):
            matches.append(filename)
        return matches

    @staticmethod
    def get_list_of_files(source: str, extensions: Tuple[str]):
        matches = []
        for extension in extensions:
            for filename in glob.iglob(source + '**' + os.path.sep + extension, recursive=True):
                matches.append(filename)
        return matches

    def start(self):
        path, destination, types = self.get_arguments()
        if path and destination:
            print("[+] Start Processing")
            all_files = self.get_all_files(path)
            extensions = types if types else self.extensions
            list_of_files = self.get_list_of_files(path, extensions)
            missing = [x for x in all_files if x not in list_of_files]
            if list_of_files:
                self.file_process.process(list_of_files, destination)
                self.reporting_summary(all_files, list_of_files, missing)
            else:
                print(f"No files found that matches the types")

    @staticmethod
    def reporting_summary(all_files, list_of_files, missing):
        print("----------------")
        print(" Summary Report ")
        print("----------------")
        print(f" Processed files : {len(list_of_files)}/{len(all_files)}")
        print(f" Missing files   : {len(missing)}/{len(all_files)}")
        for file in missing:
            print(file)


if __name__ == '__main__':
    image_organizer = ImageOrganizer()
    image_organizer.start()
