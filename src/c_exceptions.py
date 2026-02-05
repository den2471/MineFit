
class InvalidDependency(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidVersion(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidProject(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidApiResponce(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)