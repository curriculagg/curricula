import os
import pwd
from typing import Callable

from . import Extra
from ..library import process
from ...library.log import log


def demote_user(user_uid: int, user_gid: int):
    """Set the user of the process."""

    # os.setgid(user_gid)
    os.setuid(user_uid)


class Sandbox(Extra):
    """Sandbox tools for the grader."""

    user_demotion_enabled: bool
    user_demotion_username: str
    user_demotion_step: Callable[[], None]

    def __init__(self):
        """Initialize the sandbox."""

        self.user_demotion_enabled = False

    def enable_user_demotion(self, *, username: str = "grader"):
        """Add a setup step that demotes the process user."""

        self.user_demotion_enabled = True
        self.user_demotion_username = username

    def apply(self):
        """Enable configuration."""

        if self.user_demotion_enabled:
            log.debug("enabling user demotion")
            record = pwd.getpwnam(self.user_demotion_username)
            self.user_demotion_step = lambda: demote_user(record.pw_uid, record.pw_gid)
            process.process_setup_steps.append(self.user_demotion_step)

    def revert(self):
        """Revert changes."""

        if self.user_demotion_enabled:
            log.debug("reverting user demotion")
            process.process_setup_steps.remove(self.user_demotion_step)
