import rich_click as click

from nicegui import app, ui
from pathlib import Path
from uuid import uuid4

from notely import editor_ui
from notely.file_manager import FileManager, file_manager, defaults

file_manager: FileManager


@click.group()
def main(): ...


@main.group()
def server(): ...


@server.command()
@click.argument("directory", required=False)
@click.option("-p", "--port", type=int, default=2626)
@click.option("-d", "--default-name", type=str, default=defaults.name)
def start(directory, port, default_name):
    file_manager.directory = directory
    file_manager.default_name = default_name

    print("Server is starting up! Backend logic initialized.")
    ui.run(
        title="Notely", port=port, show=False, storage_secret=str(uuid4()), reload=False
    )


@server.command()
def stop():
    app.shutdown()


if __name__ in ("__main__", "__mp_main__"):
    main()
