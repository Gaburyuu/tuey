from textual.widgets import Input

class NumberWidget(Input):
    """
    A simple numeric input widget.
    Assumes that the user enters an integer.
    """
    def __init__(self, placeholder: str = "Enter a number", **kwargs):
        super().__init__(**kwargs)
        self.placeholder = placeholder

    @property
    def value(self) -> int:
        try:
            return int(self.text)
        except ValueError:
            return 0  # default or you can raise an error if preferred

class TextInputWidget(Input):
    """
    A simple text input widget.
    """
    def __init__(self, placeholder: str = "Enter text", **kwargs):
        super().__init__(**kwargs)
        self.placeholder = placeholder

    @property
    def value(self) -> str:
        return self.text
