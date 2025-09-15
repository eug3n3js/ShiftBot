class SeleniumBaseException(Exception):
    def __init__(self, message: str = "Selenium error occurred"):
        self.message = message
        super().__init__(self.message)


class SeleniumDriverCreationException(SeleniumBaseException):
    def __init__(self, message: str = "Failed to create WebDriver"):
        super().__init__(message)


class SeleniumDockerConnectionException(SeleniumDriverCreationException):
    def __init__(self, message: str = "Failed to connect to Docker Selenium Hub"):
        super().__init__(message)


class SeleniumLocalDriverException(SeleniumDriverCreationException):
    def __init__(self, message: str = "Failed to create local Chrome driver"):
        super().__init__(message)


class SeleniumLoginException(SeleniumBaseException):
    def __init__(self, message: str = "Login failed"):
        super().__init__(message)


class SeleniumPageLoadException(SeleniumLoginException):
    def __init__(self, message: str = "Failed to load login page"):
        super().__init__(message)


class SeleniumElementNotFoundException(SeleniumLoginException):
    def __init__(self, element_name: str = "element", message: str = None):
        if message is None:
            message = f"Failed to find {element_name}"
        super().__init__(message)
        self.element_name = element_name


class SeleniumLoginCredentialsException(SeleniumLoginException):
    def __init__(self, message: str = "Invalid login credentials"):
        super().__init__(message)


class SeleniumParsingException(SeleniumBaseException):
    def __init__(self, message: str = "Parsing failed"):
        super().__init__(message)


class SeleniumShiftsParsingException(SeleniumParsingException):
    def __init__(self, message: str = "Failed to parse shifts"):
        super().__init__(message)


class SeleniumCommandTimeoutException(SeleniumBaseException):
    def __init__(self, command_type: str = None, timeout_seconds: float = None):
        message = f"Command: {command_type} timeout after {timeout_seconds} seconds" \
            if timeout_seconds else f"Command: {command_type} timeout"
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class SeleniumCommandException(SeleniumBaseException):
    def __init__(self, command_type: str = None, message: str = None):
        if message is None:
            message = f"Command failed: {command_type}" if command_type else "Command execution failed"
        super().__init__(message)
        self.command_type = command_type


class SeleniumWebDriverException(SeleniumBaseException):
    def __init__(self, message: str = "WebDriver error"):
        super().__init__(message)


class SeleniumWebDriverNotReadyException(SeleniumWebDriverException):
    def __init__(self, message: str = "WebDriver is not ready"):
        super().__init__(message)
