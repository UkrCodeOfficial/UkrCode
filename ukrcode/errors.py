class UkrCodeError(Exception):
    """Помилка виконання або синтаксису UkrCode."""

    def __init__(self, message: str, line: int | None = None, column: int | None = None):
        location = f" (рядок {line}, колонка {column})" if line else ""
        super().__init__(f"Помилка{location}: {message}")
        self.message = message
        self.line = line
        self.column = column