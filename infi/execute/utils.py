import os
import fcntl

def make_fd_non_blocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

def quote(s):
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    if " " in s:
        s = '"{0}"'.format(s)
    else:
        s = s.replace("'", "\\'")
    return s

