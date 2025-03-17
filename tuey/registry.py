class Registry:
    def __init__(self):
        self._functions = {}  # key: function name, value: metadata dict

    def add(self, func, *, color="default", output_func=print, argument_widgets=None):
        self._functions[func.__name__] = {
            "func": func,
            "color": color,
            "output_func": output_func,
            "argument_widgets": argument_widgets or {}
        }

    def get(self, name: str):
        return self._functions.get(name)

    def all_functions(self):
        return self._functions
