import filecmp
import io
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import Dict, List, Optional, Set, Tuple

from PIL import Image
from tqdm import tqdm

from src.layout import FolderTemplate
from src.metadata import ExifParser, Metadata, MetadataExtractor
from src.report import CopyReport
from src.resolver import DUPLICATE, RENAMED, TargetResolver


class FileProcessor:
    """Coordinates the run: reads the metadata, builds the folders and copies (or moves) the files."""

    def __init__(
        self,
        extractor: Optional[MetadataExtractor] = None,
        template: Optional[FolderTemplate] = None,
        dry_run: bool = False,
        move: bool = False,
        skip_duplicates: bool = False,
    ):
        self.extractor = extractor or MetadataExtractor()
        self.template = template or FolderTemplate()
        self.dry_run = dry_run
        self.move = move
        self.skip_duplicates = skip_duplicates
        self.resolver = self._new_resolver()
        self._info: Dict[str, Tuple[datetime, Optional[str]]] = {}  # source -> (capture date, camera)
        self.progress_bar_reading = None
        self.progress_bar_directories = None
        self.progress_bar_files = None

    def _new_resolver(self) -> TargetResolver:
        return TargetResolver(self._same_content, self._size_of, self.skip_duplicates)

    def process(self, images: List[str], destination: str) -> CopyReport:
        self.resolver = self._new_resolver()
        self._info = {}
        if not self.dry_run:
            self.create_destination(destination)
        logging.info("[+] Reading files ")
        self.progress_bar_reading = tqdm(total=len(images), unit="files")
        folders = self.get_unique_folders(images)

        if not self.dry_run:
            logging.info("[+] Creating directories ")
            self.progress_bar_directories = tqdm(total=len(folders), unit="directory")
            self.create_directories(folders, destination)

        logging.info("[+] %s files ", "Checking" if self.dry_run else ("Moving" if self.move else "Copying"))
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

    def create_directories(self, folders: Set[str], destination: str) -> None:
        for folder in sorted(folders):
            path = os.path.join(destination, folder)
            if folder and not os.path.isdir(path):
                self.create_destination(path)
            self.progress_bar_directories.update()
        self.progress_bar_directories.close()

    def get_unique_folders(self, images: List[str]) -> Set[str]:
        folders = set()
        for image in images:
            try:
                folders.add(self.folder_for(image))
            except Exception as err:
                # The copy step will try again and report this file as failed
                logging.debug("[-] Could not read metadata of %s: %s", image, err)
            self.progress_bar_reading.update()
        self.progress_bar_reading.close()
        return folders

    def process_in_parallel(self, images: List[str], destination: str) -> CopyReport:
        report = CopyReport(total=len(images), dry_run=self.dry_run, move=self.move)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [(image, executor.submit(self.move_images, (image, destination))) for image in images]
            for image, future in futures:
                try:
                    status, other = future.result()
                except Exception as err:
                    logging.debug("[-] Failed to process %s: %s", image, err)
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
            return self._copy_file(image, os.path.join(destination, self.folder_for(image)))
        finally:
            self.progress_bar_files.update()

    def _target_name(self, image: str) -> str:
        """Output file names are always lowercase."""
        return Path(image).name.lower()

    def _write_file(self, image: str, target: str) -> None:
        copyfile(image, target)

    def _remove_source(self, image: str) -> None:
        os.remove(image)

    def _size_of(self, image: str) -> Optional[int]:
        try:
            return os.path.getsize(image)
        except OSError:
            return None

    def _same_content(self, a: str, b: str) -> bool:
        try:
            return filecmp.cmp(a, b, shallow=False)
        except OSError:
            return False

    def _copy_file(self, image: str, directory: str) -> Tuple[str, str]:
        resolution = self.resolver.reserve(image, directory, self._target_name(image))
        target = resolution.target
        if target is None or self.dry_run:
            return resolution.status, resolution.other
        try:
            self._write_file(image, target)
            if self.move and not self._same_content(image, target):
                raise OSError("the copy could not be verified, the source was kept")
        except Exception:
            self.resolver.release(target)
            try:
                os.remove(target)  # do not leave a partial file behind
            except OSError:
                pass
            raise
        if self.move:
            self._remove_source(image)  # if this fails the verified copy stays and the file is reported as failed
        return resolution.status, resolution.other

    def folder_for(self, file: str) -> str:
        """Folder of the file relative to the destination, from the folder template."""
        date, camera = self.capture_info(file)
        return self.template.render(date, camera)

    def capture_info(self, file: str) -> Tuple[datetime, Optional[str]]:
        """Capture date (modification date if unknown) and camera. Cached: every file is read once per run."""
        if file not in self._info:
            taken, camera = self._read_metadata(file)
            self._info[file] = (taken or datetime.fromtimestamp(os.path.getmtime(file)), camera)
        return self._info[file]

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

    def _size_of(self, image: str) -> Optional[int]:
        return None  # no content based duplicate detection on devices

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
