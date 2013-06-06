Introduction
------------
infi.execute is a utility for running processes in various ways. It provides several facilities, most of which are simply convenience wrappers over existing stdlib functionality.

Features
--------

Runners
========
A *runner* abstracts a destination for executing commands. *infi.execute* exposes the LocalRunner class for running commands locally, and the SSHRunner for running commands through ssh.

Runners support the *popen* method, which replicates the basic subprocess.Popen interface, but also support extensions on top of it (see below).

execute
=======
*execute* is a family of functions to perform the popular task of executing commands while capturing their stdout and stderr streams, possibly supplying a custom stdin stream. This is most useful for shell commands or system commands. *execute* is another method of the *Runner* class, making use of the *popen* method.

*execute_async* is another flavor, returning an async result that can be waited upon.
