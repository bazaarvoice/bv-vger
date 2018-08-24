def preprocessor_error_handling(method):
    def method_wrapper(*args, **kwargs):
        response = method(*args, **kwargs)
        if response:
            raise LambdaPreprocessorError(response)

    return method_wrapper


class LambdaPreprocessorError(Exception):
    pass


class LambdaPreprocessor(object):
    def __init__(self, event):
        self.event = event
        self.param = {}

