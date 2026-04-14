import rich_click as click

from nicegui import app, ui
from pathlib import Path
from uuid import uuid4

import auth 
import editor_ui 
from file_manager import file_manager, defaults


@click.group()
def main(): ...


@main.group()
def server(): ...


@server.command()
@click.argument("directory", required=False)
@click.option("-p", "--port", type=int, default=80)
@click.option("-d", "--default-name", type=str, default=defaults.name)
def start(directory, port, default_name):
    file_manager.directory = directory
    file_manager.default_name = default_name

    print("Server is starting up! Backend logic initialized.")
    ui.run(
        title="Notely", port=port, show=False, storage_secret=str(uuid4()), reload=False
    )

if __name__ in ("__main__", "__mp_main__"):
    main()
