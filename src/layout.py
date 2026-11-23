import os
import string
from datetime import datetime
from typing import Optional


class FolderTemplate:
    """
    Decides the sub folder of every file from a template such as '{date}/{camera}' or '{year}/{month}/{camera}'.

    Fields: year (2015), month (03), day (01), date (2015-03-01) and camera (olympus_stylus1).
    Empty parts (a file without camera information) are dropped, so '{date}/{camera}' becomes just '2015-03-01'.
    """

    FIELDS = ("year", "month", "day", "date", "camera")
    DEFAULT = "{date}/{camera}"

    def __init__(self, template: str = DEFAULT):
        for _, name, spec, conversion in string.Formatter().parse(template):
            if name is None:
                continue
            if name not in self.FIELDS or spec or conversion:
                raise ValueError(f"Unknown or malformed field '{{{name}}}'. Valid fields: {', '.join(self.FIELDS)}")
        self.template = template

    def render(self, date: datetime, camera: Optional[str]) -> str:
        """Relative folder with the separators of this OS, without a trailing separator ('' for the root)."""
        values = {
            "year": f"{date:%Y}",
            "month": f"{date:%m}",
            "day": f"{date:%d}",
            "date": f"{date:%Y-%m-%d}",
            "camera": camera or "",
        }
        rendered = self.template.format(**values).replace("\\", "/")
        parts = [p for p in rendered.split("/") if p.strip() and p not in (".", "..")]
        return os.path.join(*parts) if parts else ""
