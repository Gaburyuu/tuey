from textual.app import App, ComposeResult
from textual.widgets import Button, Static, DataTable, TabbedContent, TabPane
from textual.containers import VerticalScroll, Horizontal
import asyncio
from .tasks import run_task, get_queue_count

class TextualUI(App):
    CSS = "Button { margin: 1; }"

    def __init__(self, registry, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self.argument_panels = {}  # Track mounted argument widgets (shared instances)

    def compose(self) -> ComposeResult:
        yield TabbedContent(
            TabPane(self.create_main_page(), title="Functions"),
            TabPane(self.create_log_page(), title="Logs")
        )

    def create_main_page(self):
        container = VerticalScroll()
        container.mount(Static("Textual API Dashboard", classes="title"))
        for func_name, meta in self.registry.all_functions().items():
            func_panel = Horizontal()
            # Run button with color styling (for demo, we simply set the label)
            btn = Button(func_name, id=f"{func_name}")
            func_panel.mount(btn)
            # Display queued count
            queue_count = get_queue_count(func_name)
            func_panel.mount(Static(f"Queued: {queue_count}", id=f"queue-{func_name}"))
            # Add argument widgets if provided (reuse instances so they appear only once)
            if meta["argument_widgets"]:
                arg_container = Horizontal()
                for arg_name, widget in meta["argument_widgets"].items():
                    # Mount widget if not already mounted.
                    if arg_name not in self.argument_panels:
                        self.argument_panels[arg_name] = widget
                        arg_container.mount(Static(arg_name))
                        arg_container.mount(widget)
                func_panel.mount(arg_container)
            # Rerun button (will check cache and use cached result if available)
            func_panel.mount(Button("Rerun", id=f"rerun-{func_name}"))
            container.mount(func_panel)
        return container

    def create_log_page(self):
        self.log_table = DataTable()
        self.log_table.add_columns("Function", "Arguments", "Status", "Result", "Queue Count")
        return self.log_table

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id.startswith("run-"):
            func_name = button_id.replace("run-", "")
            meta = self.registry.get(func_name)
            if meta:
                func = meta["func"]
                output_func = meta["output_func"]
                # Gather arguments from the provided widgets (assume each widget has a .value attribute)
                args = []
                if meta["argument_widgets"]:
                    for arg_name, widget in meta["argument_widgets"].items():
                        args.append(widget.value)
                else:
                    args = []
                # Run the task via Huey
                result = await run_task(func, tuple(args), func_name)
                # Process output
                output_func(result)
                queue_count = get_queue_count(func_name)
                self.log_table.add_row(func_name, str(args), "Completed", str(result), str(queue_count))
        elif button_id.startswith("rerun-"):
            func_name = button_id.replace("rerun-", "")
            meta = self.registry.get(func_name)
            if meta:
                func = meta["func"]
                output_func = meta["output_func"]
                args = []
                if meta["argument_widgets"]:
                    for arg_name, widget in meta["argument_widgets"].items():
                        args.append(widget.value)
                else:
                    args = []
                # run_task checks cache and returns cached result if available.
                result = await run_task(func, tuple(args), func_name)
                output_func(result)
                queue_count = get_queue_count(func_name)
                self.log_table.add_row(func_name, str(args), "Rerun", str(result), str(queue_count))

    async def update_ui(self):
        while True:
            # Periodically refresh the queue count for each function.
            for func_name, meta in self.registry.all_functions().items():
                queue_count = get_queue_count(func_name)
                try:
                    widget = self.query_one(f"#queue-{func_name}", Static)
                    widget.update(f"Queued: {queue_count}")
                except Exception:
                    pass
            await asyncio.sleep(5)

    async def on_mount(self) -> None:
        self.run_worker(self.update_ui())
