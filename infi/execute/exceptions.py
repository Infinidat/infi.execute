class ExecutionError(Exception):
    def __init__(self, result):
        super(ExecutionError, self).__init__("Execution of %r failed!\nresult=%s\nstdout=%r\nstderr=%r" % (result._command,
                                                                                                           result.result,
                                                                                                           result.stdout,
                                                                                                           result.stderr))
        self.result = result
class CommandTimeout(ExecutionError):
    pass
