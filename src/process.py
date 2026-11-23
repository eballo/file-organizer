import filecmp
import io
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional
from shutil import copyfile
from pathlib import Path
from PIL import Image
import logging
from tqdm import tqdm

from src.metadata import ExifParser, Metadata, MetadataExtractor

COPIED = "copied"
RENAMED = "renamed"
DUPLICATE = "duplicate"


@dataclass
class CopyReport:
    """Outcome of a run: what was copied and every conflict or failure found on the way."""

    total: int = 0
    copied: int = 0
    renamed: List[Tuple[str, str]] = field(default_factory=list)  # (source, final target)
    duplicates: List[Tuple[str, str]] = field(default_factory=list)  # (source, identical existing file)
    failed: List[Tuple[str, str]] = field(default_factory=list)  # (source, error)

    def log(self) -> None:
        logging.info(" ")
        logging.info("------------------------")
        logging.info("  Final Report  ")
        logging.info("------------------------")
        logging.info(" Files to process      : %d", self.total)
        logging.info(" Copied (total)        : %d", self.copied + len(self.renamed))
        logging.info(" Renamed (name clash)  : %d", len(self.renamed))
        logging.info(" Skipped (duplicates)  : %d", len(self.duplicates))
        logging.info(" Failed                : %d", len(self.failed))
        self._log_section("Renamed because the name was already taken by a different file", self.renamed, "->")
        self._log_section("Not copied because an identical file already exists", self.duplicates, "==")
        self._log_section("Failed", self.failed, ":")
        logging.info(" ")

    @staticmethod
    def _log_section(title: str, items: List[Tuple[str, str]], sep: str) -> None:
        if items:
            logging.warning(" %s:", title)
            for source, other in items:
                logging.warning("   %s %s %s", source, sep, other)


class FileProcessor:

    def __init__(self, extractor: Optional[MetadataExtractor] = None):
        self.extractor = extractor or MetadataExtractor()
        self._lock = threading.Lock()
        self._reserved: Dict[str, str] = {}  # target path -> source that owns it in this run
        self._dates: Dict[str, Tuple[str, Optional[str]]] = {}  # source -> (date folder, camera folder)
        self.progress_bar_reading = None
        self.progress_bar_directories = None
        self.progress_bar_files = None

    def process(self, images: List[str], destination: str) -> CopyReport:
        self._reserved = {}
        self._dates = {}
        self.create_destination(destination)
        logging.info("[+] Reading files ")
        self.progress_bar_reading = tqdm(total=len(images), unit="files")
        sorted_dates = self.get_unique_sorted_dates(images)

        logging.info("[+] Creating directories ")
        self.progress_bar_directories = tqdm(total=len(sorted_dates), unit="directory")
        self.create_directories(sorted_dates, destination)

        logging.info("[+] Copying files ")
        self.progress_bar_files = tqdm(total=len(images), unit="file")
        report = self.process_in_parallel(images, destination)
        report.log()
        return report

    @staticmethod
    def create_destination(directory_name):
        try:
            if not os.path.isdir(directory_name):
                os.makedirs(directory_name)
            else:
                logging.info("[-] Output directory already exists")
        except OSError:
            logging.warning("Creation of the directory %s failed" % directory_name)

    def create_directories(self, sorted_dates, destination: str) -> None:
        for date, model in sorted_dates:
            if not os.path.isdir(destination + date):
                self.create_destination(destination + date)
            if model:
                if not os.path.isdir(destination + date + os.path.sep + model):
                    self.create_destination(destination + date + os.path.sep + model)
            self.progress_bar_directories.update()
        self.progress_bar_directories.close()

    def get_unique_sorted_dates(self, images: List[str]) -> Set[Tuple[str, str]]:
        unique_dates = set()
        for image in images:
            try:
                unique_dates.add(self.modification_date(image))
            except Exception as err:
                # The copy step will try again and report this file as failed
                logging.debug("[-] Could not read metadata of %s: %s", image, err)
            self.progress_bar_reading.update()
        self.progress_bar_reading.close()
        return unique_dates

    def process_in_parallel(self, images: List[str], destination: str) -> CopyReport:
        report = CopyReport(total=len(images))
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [(image, executor.submit(self.move_images, (image, destination))) for image in images]
            for image, future in futures:
                try:
                    status, other = future.result()
                except Exception as err:
                    logging.debug("[-] Failed to copy %s: %s", image, err)
                    report.failed.append((image, str(err)))
                    continue
                if status == RENAMED:
                    report.renamed.append((image, other))
                elif status == DUPLICATE:
                    report.duplicates.append((image, other))
                else:
                    report.copied += 1
        self.progress_bar_files.close()
        return report

    def move_images(self, args: Tuple[str, str]) -> Tuple[str, str]:
        image, destination = args
        try:
            date, model = self.modification_date(image)
            destination += date + os.path.sep
            if model:
                destination += model + os.path.sep
            return self._copy_file(image, destination)
        finally:
            self.progress_bar_files.update()

    def _target_name(self, image: str) -> str:
        """Output file names are always lowercase."""
        return Path(image).name.lower()

    def _write_file(self, image: str, target: str) -> None:
        copyfile(image, target)

    def _same_content(self, a: str, b: str) -> bool:
        try:
            return filecmp.cmp(a, b, shallow=False)
        except OSError:
            return False

    def _reserve_target(self, image: str, directory: str, name: str) -> Tuple[Optional[str], str, str]:
        """
        Picks a free target path for the image. Returns (target, status, other):
        target is None when an identical file already exists (status DUPLICATE, other is that file).
        A clash with a different file gets a numeric suffix (status RENAMED, other is the final path).
        """
        stem, ext = os.path.splitext(name)
        with self._lock:
            attempt = 0
            while True:
                candidate = name if attempt == 0 else f"{stem}_{attempt}{ext}"
                target = directory + candidate
                owner = self._reserved.get(target)
                if owner is None and not os.path.exists(target):
                    self._reserved[target] = image
                    return target, (RENAMED if attempt else COPIED), target
                existing = owner or target
                if self._same_content(image, existing):
                    return None, DUPLICATE, existing
                attempt += 1

    def _copy_file(self, image: str, destination: str) -> Tuple[str, str]:
        target, status, other = self._reserve_target(image, destination, self._target_name(image))
        if target is None:
            return status, other
        try:
            self._write_file(image, target)
        except Exception:
            with self._lock:
                self._reserved.pop(target, None)
            try:
                os.remove(target)  # do not leave a partial file behind
            except OSError:
                pass
            raise
        return status, other

    def modification_date(self, file: str) -> Tuple[str, Optional[str]]:
        """Returns (YYYY-MM-DD, camera folder or None). Cached: every file is read once per run."""
        if file not in self._dates:
            taken, camera = self._read_metadata(file)
            date = taken or datetime.fromtimestamp(os.path.getmtime(file))
            self._dates[file] = (date.strftime("%Y-%m-%d"), camera)
        return self._dates[file]

    def _read_metadata(self, file: str) -> Metadata:
        """Capture date and camera from the file itself; empty fields fall back to the modification date."""
        return self.extractor.read(file)


class FileProcessorWin32(FileProcessor):
    """
    This class holds the specific logic needed for win32
    """

    def _target_name(self, image: str) -> str:
        import src.mtp_windows

        return src.mtp_windows.get_content_from_device_path(image).getName().lower()

    def _write_file(self, image: str, target: str) -> None:
        import src.mtp_windows

        cont = src.mtp_windows.get_content_from_device_path(image)
        with open(target, "wb") as target_file:
            cont.downloadStream(target_file)

    def _same_content(self, a: str, b: str) -> bool:
        # Device files cannot be compared cheaply: a clash is always resolved by renaming
        return False

    def _read_metadata(self, file: str) -> Metadata:
        try:
            import src.mtp_windows

            cont = src.mtp_windows.get_content_from_device_path(file)
            with Image.open(io.BytesIO(cont.read_data())) as img:
                found = ExifParser.parse(img.getexif())
            return Metadata(found.date or cont.getDate(), found.camera)
        except Exception as e:
            logging.error(e)
            return Metadata(datetime.today(), None)
