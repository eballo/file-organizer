import glob
import os
from typing import Tuple, List, Union, Any, Set

from src.constants import DEFAULT_EXTENSION
from src.process import FileProcessor, FileProcessorWin32
import logging

from src.utils import WaitingEffect, do_you_want_to_continue


class FileOrganizer:
    def __init__(self, source: str, destination: str, extensions: Tuple[Union[str, Any], ...]):
        self.file_process = self.get_file_processor()
        self.source = source
        self.destination = destination
        self.extensions = extensions if extensions else DEFAULT_EXTENSION

    @staticmethod
    def get_file_processor():
        return FileProcessor()

    def start(self):
        if self.source and self.destination:
            self.validate_data_input()
            logging.info("[+] Start Processing")
            files = self.get_files(self.source, self.extensions)
            all_files = files[0]
            list_of_files_to_be_processed = files[1]
            missing = files[2]
            if list_of_files_to_be_processed:
                self.reporting_summary(all_files, list_of_files_to_be_processed, missing)
                do_you_want_to_continue()
                self.file_process.process(list_of_files_to_be_processed, self.destination)
            else:
                logging.info("[-] No files found that matches the types")

    def validate_data_input(self):
        # Validates that the source and destination folder ends up with a os.path.separator
        # if not we will add a separator

        if not self.source.endswith(os.path.sep):
            self.source = self.source + os.path.sep

        if not self.destination.endswith(os.path.sep):
            self.destination = self.destination + os.path.sep

    def get_files(self, source: str, extensions: Tuple[str]) -> List[List[str]]:
        all_files, processed_files = self._filter_files(source, extensions)
        missing_files = [x for x in all_files if x not in processed_files]
        return [all_files, processed_files, missing_files]

    def _filter_files(self, source: str, extensions: Tuple[str]) -> Tuple[List[str], List[str]]:
        all_files = []
        processed_files = []
        we = WaitingEffect(" |- Searching files...")
        for filename in glob.iglob(source + "**" + os.path.sep + "*.*", recursive=True):
            we.run()
            all_files.append(filename.lower())
            base, ext = os.path.splitext(filename)
            if ext.lower() in extensions:
                processed_files.append(filename.lower())
        we.run(end=True)
        return all_files, processed_files

    @staticmethod
    def get_unique_extensions(files: List[str]) -> Set[str]:
        unique_extensions = set()
        for file in files:
            extension = os.path.splitext(file)[1]
            if extension not in unique_extensions:
                unique_extensions.add(extension)
        return unique_extensions

    def reporting_summary(self, all_files, list_of_processed, missing):
        logging.info(" ")
        logging.info("------------------------")
        logging.info("  Files Report  ")
        logging.info("------------------------")
        logging.info(" Extensions to be processed : %s ", self.extensions)
        logging.info(" Files found : %s / %s ", len(list_of_processed), len(all_files))
        logging.info(" ")
        logging.info(" Missing files   : %s / %s", len(missing), len(all_files))
        logging.info(
            " Missed files have the following extensions: %s",
            self.get_unique_extensions(missing),
        )
        logging.info(" ")


class FileOrganizerWin32(FileOrganizer):

    @staticmethod
    def get_file_processor():
        return FileProcessorWin32()

    def _filter_files(self, source: str, extensions: Tuple[str]) -> Tuple[List[str], List[str]]:
        from src.mtp_windows import get_sub_files

        processed_files = []
        we = WaitingEffect(" |- Searching files...")
        # Searching recursively
        all_files = get_sub_files(source)
        for filename in all_files:
            we.run()
            extension = os.path.splitext(filename)[1].lower()
            if extension in extensions:
                processed_files.append(filename)
        we.run(end=True)
        return all_files, processed_files
