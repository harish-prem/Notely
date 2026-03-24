# backend.py
from nicegui import ui
import editor_ui
import file_manager



def startup():
    file_manager.change_directory('resources')
    print("Server is starting up! Backend logic initialized.")




if __name__ in {"__main__", "__mp_main__"}:
    startup()
    ui.run(title="Notely", port=2626,show=False)
