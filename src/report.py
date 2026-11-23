import logging
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class CopyReport:
    """Outcome of a run: what was copied (or moved) and every conflict or failure found on the way."""

    total: int = 0
    copied: int = 0
    renamed: List[Tuple[str, str]] = field(default_factory=list)  # (source, final target)
    duplicates: List[Tuple[str, str]] = field(default_factory=list)  # (source, identical file already there)
    failed: List[Tuple[str, str]] = field(default_factory=list)  # (source, error)
    dry_run: bool = False
    move: bool = False

    @property
    def written(self) -> int:
        return self.copied + len(self.renamed)

    def log(self) -> None:
        verb = "move" if self.move else "copy"
        done = ("Would " + verb) if self.dry_run else ("Moved" if self.move else "Copied")
        logging.info(" ")
        logging.info("------------------------")
        logging.info("  Final Report %s", "(dry run: nothing was written)" if self.dry_run else "")
        logging.info("------------------------")
        logging.info(" Files to process      : %d", self.total)
        logging.info(" %-21s : %d", done + " (total)", self.written)
        logging.info(" Renamed (name clash)  : %d", len(self.renamed))
        logging.info(" Skipped (duplicates)  : %d", len(self.duplicates))
        logging.info(" Failed                : %d", len(self.failed))
        self._log_section("Renamed because the name was already taken by a different file", self.renamed, "->")
        left = " (left in the source folder)" if self.move else ""
        self._log_section("Not copied because an identical file already exists" + left, self.duplicates, "==")
        self._log_section("Failed", self.failed, ":")
        logging.info(" ")

    @staticmethod
    def _log_section(title: str, items: List[Tuple[str, str]], sep: str) -> None:
        if items:
            logging.warning(" %s:", title)
            for source, other in items:
                logging.warning("   %s %s %s", source, sep, other)
