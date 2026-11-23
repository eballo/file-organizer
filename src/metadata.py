"""Reads the capture date and the camera name of a media file."""

import json
import logging
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, NamedTuple, Optional

from PIL import ExifTags, Image

try:  # optional: adds HEIC/HEIF support to Pillow
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover
    pass


class Metadata(NamedTuple):
    date: Optional[datetime] = None  # naive, local time of the capture
    camera: Optional[str] = None  # safe to use as a folder name


class CameraName:
    """Builds camera names that are safe to use as a folder name."""

    @staticmethod
    def clean(value) -> Optional[str]:
        """Lowercase and keep only characters that are safe in a folder name on every OS."""
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")
        if not isinstance(value, str):
            return None
        cleaned = re.sub(r"[^\w.-]", "", value.replace(" ", "").lower()).strip(".")
        return cleaned or None

    @classmethod
    def build(cls, make, model) -> Optional[str]:
        """
        'Canon' + 'Canon EOS 60D' -> 'canoneos60d'; 'Apple' + 'iPhone 12' -> 'apple_iphone12'.
        Only the first word of the make is used: 'OLYMPUS IMAGING CORP.' -> 'olympus'.
        """
        if isinstance(make, str):
            make = make.split()[0] if make.split() else None
        make, model = cls.clean(make), cls.clean(model)
        if make and model and not model.startswith(make):
            return f"{make}_{model}"
        return model or make


class ExifParser:
    """Extracts the metadata we care about from a Pillow EXIF object."""

    DATE_FORMAT = "%Y:%m:%d %H:%M:%S"
    MIN_VALID_YEAR = 1971  # containers use 1904 or 1970 as "unknown"

    @classmethod
    def valid_date(cls, date: Optional[datetime]) -> Optional[datetime]:
        return date if date and date.year >= cls.MIN_VALID_YEAR else None

    @classmethod
    def parse_date(cls, value) -> Optional[datetime]:
        if isinstance(value, bytes):
            value = value.decode("ascii", errors="ignore")
        if not isinstance(value, str):
            return None
        try:
            return cls.valid_date(datetime.strptime(value.strip("\x00 ")[:19], cls.DATE_FORMAT))
        except ValueError:  # includes the '0000:00:00 00:00:00' placeholder
            return None

    @classmethod
    def parse(cls, exif) -> Metadata:
        if not exif:
            return Metadata()
        try:
            exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        except Exception:  # damaged IFD
            exif_ifd = {}
        date = None
        for source, tag in (
            (exif_ifd, ExifTags.Base.DateTimeOriginal),
            (exif_ifd, ExifTags.Base.DateTimeDigitized),
            (exif, ExifTags.Base.DateTime),
        ):
            date = cls.parse_date(source.get(tag))
            if date:
                break
        return Metadata(date, CameraName.build(exif.get(ExifTags.Base.Make), exif.get(ExifTags.Base.Model)))


class MetadataReader(ABC):
    """Reads the metadata of one family of files."""

    @abstractmethod
    def supports(self, path: str) -> bool:
        """True if this reader knows how to read the file."""

    @abstractmethod
    def read(self, path: str) -> Metadata:
        """Never raises: returns empty metadata when the file cannot be read."""


class VideoMetadataReader(MetadataReader):
    """Reads video containers through ffprobe (part of FFmpeg)."""

    EXTENSIONS = (".mov", ".mp4", ".m4v", ".avi", ".3gp")
    TIMEOUT = 20

    def __init__(self):
        self._ffprobe_checked = False
        self._ffprobe_path: Optional[str] = None

    @property
    def ffprobe(self) -> Optional[str]:
        if not self._ffprobe_checked:
            self._ffprobe_path = shutil.which("ffprobe")
            self._ffprobe_checked = True
            if not self._ffprobe_path:
                logging.warning("[-] ffprobe not found: videos will use the file modification date and no camera name")
        return self._ffprobe_path

    def supports(self, path: str) -> bool:
        return os.path.splitext(path)[1].lower() in self.EXTENSIONS

    def read(self, path: str) -> Metadata:
        if not self.ffprobe:
            return Metadata()
        try:
            out = subprocess.run(
                [self.ffprobe, "-v", "error", "-print_format", "json", "-show_entries", "format_tags", "-i", path],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT,
                check=True,
            ).stdout
            tags = {k.lower(): v for k, v in json.loads(out).get("format", {}).get("tags", {}).items()}
        except (OSError, subprocess.SubprocessError, ValueError) as err:
            logging.debug("[-] ffprobe failed for %s: %s", path, err)
            return Metadata()
        make = tags.get("com.apple.quicktime.make") or tags.get("make")
        model = tags.get("com.apple.quicktime.model") or tags.get("model")
        return Metadata(self.parse_date(tags), CameraName.build(make, model))

    @staticmethod
    def parse_date(tags: dict) -> Optional[datetime]:
        try:
            apple = tags.get("com.apple.quicktime.creationdate")
            if apple:  # local time with the offset of the place where it was shot
                return ExifParser.valid_date(datetime.strptime(apple, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None))
            created = tags.get("creation_time")
            if created:  # UTC
                return ExifParser.valid_date(datetime.fromisoformat(created).astimezone().replace(tzinfo=None))
        except ValueError:
            pass
        return None


class ImageMetadataReader(MetadataReader):
    """Reads EXIF data with Pillow. It is the fallback reader: it accepts any file and fails softly."""

    def supports(self, path: str) -> bool:
        return True

    def read(self, path: str) -> Metadata:
        try:
            with Image.open(path) as img:
                return ExifParser.parse(img.getexif())
        except Exception as err:  # not an image, truncated, corrupt...
            logging.debug("[-] No EXIF for %s: %s", path, err)
            return Metadata()


class MetadataExtractor:
    """Picks the first reader that supports the file. Readers can be injected to add formats or in tests."""

    def __init__(self, readers: Optional[List[MetadataReader]] = None):
        self.readers = readers if readers is not None else [VideoMetadataReader(), ImageMetadataReader()]

    def read(self, path: str) -> Metadata:
        for reader in self.readers:
            if reader.supports(path):
                return reader.read(path)
        return Metadata()
