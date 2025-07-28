"""
ComfyUI Handler Custom Exceptions
"""


class ComfyUIError(Exception):
    """Base ComfyUI exception"""
    pass


class ComfyUIConnectionError(ComfyUIError):
    """ComfyUI connection error"""
    pass


class ComfyUITimeoutError(ComfyUIError):
    """ComfyUI timeout error"""
    pass


class ComfyUITaskError(ComfyUIError):
    """ComfyUI task execution error"""
    def __init__(self, message: str, prompt_id: str = None, node_errors: dict = None):
        super().__init__(message)
        self.prompt_id = prompt_id
        self.node_errors = node_errors or {}


class ComfyUIValidationError(ComfyUIError):
    """ComfyUI request validation error"""
    pass


class ComfyUIServerError(ComfyUIError):
    """ComfyUI server error"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code 