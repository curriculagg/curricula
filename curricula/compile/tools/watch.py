from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

import time

from pathlib import Path

from ..compilation import CurriculaTarget, Configuration


class TargetHandler(FileSystemEventHandler):
    """Rebuilds when something changes."""

    target: CurriculaTarget

    def __init__(self, target: CurriculaTarget):
        """Set target."""

        self.target = target

    def on_any_event(self, event: FileSystemEvent):
        """Rebuild with the src_path as modified."""

        self.target.compile(paths_modified={event.src_path})


def watch(assignment_path: Path, artifacts_path: Path, custom_template_path: Path = None, **options):
    """Recompile when a file changes."""

    configuration = Configuration(
        assignment_path=assignment_path,
        artifacts_path=artifacts_path,
        custom_template_path=custom_template_path,
        options=options)
    target = CurriculaTarget(configuration)

    handler = TargetHandler(target)

    observer = Observer()
    observer.schedule(handler, str(assignment_path), recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
