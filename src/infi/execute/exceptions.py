class ExecutionError(Exception):
    def __init__(self, result):
        super(ExecutionError, self).__init__("Execution of %r failed!\nresult=%s\nstdout=%r\nstderr=%r" % (result._command,
                                                                                                           result.get_returncode(),
                                                                                                           result.get_stdout(),
                                                                                                           result.get_stderr()))
        self.result = result


class CommandTimeout(ExecutionError):
    pass
