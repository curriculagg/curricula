"""This module provides output capture for testing binaries.

We can capture all output of programs run under this process by
temporarily replacing stdout and stderr with our own pipes, running
the program, and putting the original file descriptors back. All we
have to do to recover the output is read the pipes.

https://stackoverflow.com/questions/9488560/capturing-print-output-from-shared-library-called-from-python-with-ctypes-module
"""


import contextlib
import fcntl
import os


def _nonblocking(fd: int):
    """Change flags on a pipe to prevent blocking.

    If we don't disable blocking on the pipe descriptors, reading
    from the pipes after running our subprogram hangs.
    """

    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    return fd


@contextlib.contextmanager
def capturing() -> (int, int):
    """Capture stdout and stderr temporarily."""

    # Create pipes to use as stdout and stderr
    new_stdout_read, new_stdout_write = os.pipe()
    new_stderr_read, new_stderr_write = os.pipe()

    # Make copies of original
    original_stdout_write = os.dup(1)
    original_stderr_write = os.dup(2)

    # Replace with our pipes
    os.dup2(new_stdout_write, 1)
    os.dup2(new_stderr_write, 2)

    yield _nonblocking(new_stdout_read), _nonblocking(new_stderr_read)

    # Put back
    os.dup2(original_stdout_write, 1)
    os.dup2(original_stderr_write, 2)


def read(fd: int) -> str:
    """Read until the pipe is empty."""

    buffer = bytes()
    while True:
        try:
            buffer += os.read(fd, 1024)
        except OSError:
            break
    return buffer.decode()


def capture(call, *args) -> (int, str, str):
    """Capture the stdout and stderr of a function call."""

    with capturing() as (stdout, stderr):
        code = call(*args)
    return code, read(stdout), read(stderr)
