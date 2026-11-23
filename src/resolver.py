import os
import threading
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

COPIED = "copied"
RENAMED = "renamed"
DUPLICATE = "duplicate"


@dataclass(frozen=True)
class Resolution:
    """target is None when the file must be skipped: other is then the identical file that already exists."""

    target: Optional[str]
    status: str
    other: str


class TargetResolver:
    """
    Decides the final path of every file and guarantees that nothing is overwritten, even with many threads.

    * Same name, same content   -> duplicate, skipped.
    * Same name, other content  -> numeric suffix (img_1.jpg).
    * skip_duplicates           -> same content under any name (anywhere in this run) is skipped too.
    """

    def __init__(
        self,
        same_content: Callable[[str, str], bool],
        size_of: Optional[Callable[[str], Optional[int]]] = None,
        skip_duplicates: bool = False,
    ):
        self._same_content = same_content
        self._size_of = size_of
        self._skip_duplicates = skip_duplicates
        self._lock = threading.Lock()
        self._owners: Dict[str, str] = {}  # target path -> source that owns it in this run
        self._by_size: Dict[int, List[Tuple[str, str]]] = defaultdict(list)  # size -> [(source, target)]

    def reserve(self, image: str, directory: str, name: str) -> Resolution:
        with self._lock:
            duplicate = self._find_same_content_anywhere(image)
            if duplicate:
                return Resolution(None, DUPLICATE, duplicate)
            stem, ext = os.path.splitext(name)
            attempt = 0
            while True:
                candidate = name if attempt == 0 else f"{stem}_{attempt}{ext}"
                target = os.path.join(directory, candidate)
                owner = self._owners.get(target)
                if owner is None and not os.path.exists(target):
                    self._owners[target] = image
                    self._index(image, target)
                    return Resolution(target, RENAMED if attempt else COPIED, target)
                existing = owner or target
                if self._same_content(image, existing):
                    return Resolution(None, DUPLICATE, target)
                attempt += 1

    def release(self, target: str) -> None:
        """Frees a reservation whose copy failed."""
        with self._lock:
            self._owners.pop(target, None)
            for entries in self._by_size.values():
                entries[:] = [e for e in entries if e[1] != target]

    def _size(self, image: str) -> Optional[int]:
        return self._size_of(image) if (self._skip_duplicates and self._size_of) else None

    def _find_same_content_anywhere(self, image: str) -> Optional[str]:
        size = self._size(image)
        if size is not None:
            for source, target in self._by_size.get(size, []):
                if self._same_content(image, source):
                    return target
        return None

    def _index(self, image: str, target: str) -> None:
        size = self._size(image)
        if size is not None:
            self._by_size[size].append((image, target))
