"""Reads the capture date and the camera name of a media file."""

import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from functools import lru_cache
from typing import NamedTuple, Optional

from PIL import ExifTags, Image

try:  # optional: adds HEIC/HEIF support to Pillow
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover
    pass

VIDEO_EXTENSIONS = (".mov", ".mp4", ".m4v", ".avi", ".3gp")
EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"
MIN_VALID_YEAR = 1971  # containers use 1904 or 1970 as "unknown"
FFPROBE_TIMEOUT = 20


class Metadata(NamedTuple):
    date: Optional[datetime] = None  # naive, local time of the capture
    camera: Optional[str] = None  # safe to use as a folder name


def clean_name(value) -> Optional[str]:
    """Lowercase and keep only characters that are safe in a folder name on every OS."""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"[^\w.-]", "", value.replace(" ", "").lower()).strip(".")
    return cleaned or None


def camera_name(make, model) -> Optional[str]:
    """
    'Canon' + 'Canon EOS 60D' -> 'canoneos60d'; 'Apple' + 'iPhone 12' -> 'apple_iphone12'.
    Only the first word of the make is used: 'OLYMPUS IMAGING CORP.' -> 'olympus'.
    """
    if isinstance(make, str):
        make = make.split()[0] if make.split() else None
    make, model = clean_name(make), clean_name(model)
    if make and model and not model.startswith(make):
        return f"{make}_{model}"
    return model or make


def _valid(date: Optional[datetime]) -> Optional[datetime]:
    return date if date and date.year >= MIN_VALID_YEAR else None


def parse_exif_date(value) -> Optional[datetime]:
    if isinstance(value, bytes):
        value = value.decode("ascii", errors="ignore")
    if not isinstance(value, str):
        return None
    try:
        return _valid(datetime.strptime(value.strip("\x00 ")[:19], EXIF_DATE_FORMAT))
    except ValueError:  # includes the '0000:00:00 00:00:00' placeholder
        return None


def exif_metadata(exif) -> Metadata:
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
        date = parse_exif_date(source.get(tag))
        if date:
            break
    return Metadata(date, camera_name(exif.get(ExifTags.Base.Make), exif.get(ExifTags.Base.Model)))


def image_metadata(path: str) -> Metadata:
    try:
        with Image.open(path) as img:
            return exif_metadata(img.getexif())
    except Exception as err:  # not an image, truncated, corrupt...
        logging.debug("[-] No EXIF for %s: %s", path, err)
        return Metadata()


@lru_cache(maxsize=1)
def _ffprobe() -> Optional[str]:
    found = shutil.which("ffprobe")
    if not found:
        logging.warning("[-] ffprobe not found: videos will use the file modification date and no camera name")
    return found


def _video_date(tags: dict) -> Optional[datetime]:
    try:
        apple = tags.get("com.apple.quicktime.creationdate")
        if apple:  # local time with the offset of the place where it was shot
            return _valid(datetime.strptime(apple, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None))
        created = tags.get("creation_time")
        if created:  # UTC
            return _valid(datetime.fromisoformat(created).astimezone().replace(tzinfo=None))
    except ValueError:
        pass
    return None


def video_metadata(path: str) -> Metadata:
    ffprobe = _ffprobe()
    if not ffprobe:
        return Metadata()
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-print_format", "json", "-show_entries", "format_tags", "-i", path],
            capture_output=True,
            text=True,
            timeout=FFPROBE_TIMEOUT,
            check=True,
        ).stdout
        tags = {k.lower(): v for k, v in json.loads(out).get("format", {}).get("tags", {}).items()}
    except (OSError, subprocess.SubprocessError, ValueError) as err:
        logging.debug("[-] ffprobe failed for %s: %s", path, err)
        return Metadata()
    make = tags.get("com.apple.quicktime.make") or tags.get("make")
    model = tags.get("com.apple.quicktime.model") or tags.get("model")
    return Metadata(_video_date(tags), camera_name(make, model))


def read_metadata(path: str) -> Metadata:
    if os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS:
        return video_metadata(path)
    return image_metadata(path)
