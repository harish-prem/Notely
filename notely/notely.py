import rich_click as click
from nicegui import app, ui
from . import editor_ui
from .file_manager import FileManager
from uuid import uuid4


@click.group()
def main(): ...


@main.group()
def server(): ...


@server.command()
@click.argument(
    "directory", required=False, default="resources", type=click.Path(exists=True)
)
@click.option("-p", "--port", type=int, default=2626)
@click.option("-d", "--default-name", type=str, default="untitled")
def start(directory, port, default_name):
    print("Server is starting up! Backend logic initialized.")
    ui.run(
        title="Notely", port=port, show=False, storage_secret=str(uuid4()), reload=False
    )

    # Adapted From: https://github.com/zauberzeug/nicegui/discussions/2324#discussioncomment-8066258
    app.storage.user.update(
        file_manager=FileManager(directory=directory, default_name=default_name)
    )


@server.command()
def stop():
    app.shutdown()


if __name__ in ("__main__", "__mp_main__"):
    main()
