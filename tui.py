from prompt_toolkit import Application, print_formatted_text, HTML
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.application.current import get_app


def cprint(text: str):
    print_formatted_text(HTML(text))

def get_tui(handler):
    # Create key bindings
    kb = KeyBindings()
    
    @kb.add('c-c')
    def _(event):
        "Pressing Ctrl-C will clear the input"
        event.current_buffer.text = ""
    
    @kb.add('c-d')
    def _(event):
        "Pressing Ctrl-D will exit the application"
        event.app.exit()
    
    # Single-line input widget
    input_field = TextArea(height=1, prompt="> ", multiline=False)

    def in_handler(buff):
        handler(input_field.text)

    # When Enter is pressed, exit the app and return the text as the result.
    input_field.accept_handler = in_handler
    
    # Create window with the input_field
    
    return Application(
        layout=Layout(input_field, focused_element=input_field),
        key_bindings=kb,
        full_screen=False
    )