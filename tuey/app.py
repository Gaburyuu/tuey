from .registry import Registry
from .ui import TextualUI

class TextualAPI:
    def __init__(self):
        self.registry = Registry()
        self.ui = TextualUI(self.registry)

    def register(self, *, color="default", output_func=print, argument_widgets=None):
        """
        Decorator to register a function.
        - color: styling for the function button in the UI.
        - output_func: how to process/display the output.
        - argument_widgets: a dict mapping argument names to pre-created Textual widgets.
        """
        def decorator(func):
            self.registry.add(func, color=color, output_func=output_func, argument_widgets=argument_widgets)
            return func
        return decorator

    def run(self):
        self.ui.run()

app = TextualAPI()
