from . import GraderConfiguration
from ...library import process
from ...log import log

try:
    import pwd
except ImportError:
    pwd = None
    log.warning("pwd module is unavailable on this platform")


class SandboxConfiguration(GraderConfiguration):
    """Sandbox tools for the grader."""

    user_demotion_enabled: bool
    user_demotion_username: str

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

            try:
                record = pwd.getpwnam(self.user_demotion_username)
            except KeyError:
                log.error("grader system account not available")
                return

            process.config.enable_demote_user(record.pw_uid, record.pw_gid)

    def revert(self):
        """Revert changes."""

        if self.user_demotion_enabled:
            log.debug("reverting user demotion")
            process.config.disable_demote_user()
