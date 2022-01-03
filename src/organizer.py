import glob
import os
from typing import Tuple, List, Union, Any, Set

from src.constants import DEFAULT_EXTENSION
from src.process import FileProcessor
import logging
import src.utils
import src.mtp_windows


class FileOrganizer:
    def __init__(
            self, is_mtp: bool, source: str, destination: str, extensions: Tuple[Union[str, Any], ...]
    ) -> object:
        self.file_process = FileProcessor(is_mtp)
        self.source = source
        self.destination = destination
        self.extensions = extensions if extensions else DEFAULT_EXTENSION
        self.is_mtp = is_mtp

    @staticmethod
    def get_files(is_mtp: bool, source: str, extensions: Tuple[str]):
        all_files = []
        processed_files = []
        we = src.utils.WaitingEffect(" |- Searching files...")
        if not is_mtp:
            for filename in glob.iglob(source + "**" + os.path.sep + "*.*", recursive=True):
                we.run()
                all_files.append(filename.lower())
                base, ext = os.path.splitext(filename)
                if ext.lower() in extensions:
                    processed_files.append(filename.lower())
            we.run(end=True)
        else:
            # Searching recursively
            all_files = src.mtp_windows.get_sub_files(source)
            for filename in all_files:
                we.run()
                extension = os.path.splitext(filename)[1].lower()
                if extension in extensions:
                    processed_files.append(filename)
            we.run(end=True)
        missing_files = [x for x in all_files if x not in processed_files]
        return [all_files, processed_files, missing_files]

    @staticmethod
    def get_unique_extensions(files: List[str]) -> Set[str]:
        unique_extensions = set()
        for file in files:
            extension = os.path.splitext(file)[1]
            if extension not in unique_extensions:
                unique_extensions.add(extension)
        return unique_extensions

    def start(self):
        if self.source and self.destination:
            logging.info("[+] Start Processing")
            files = self.get_files(self.is_mtp, self.source, self.extensions)
            all_files = files[0]
            list_of_files_to_be_processed = files[1]
            missing = files[2]
            if list_of_files_to_be_processed:
                self.reporting_summary(
                    all_files, list_of_files_to_be_processed, missing
                )
                src.utils.do_you_want_to_continue()
                self.file_process.process(list_of_files_to_be_processed, self.destination)
            else:
                logging.info("[-] No files found that matches the types")

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
