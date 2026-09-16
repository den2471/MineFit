
class InvalidDependency(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidVersion(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidProject(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidApiResponse(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ServiceNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class NoEnvVariable(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)