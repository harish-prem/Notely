# editor_ui.py

import re

from datetime import datetime
from nicegui import ui

from .file_manager import FileManager, file_manager

file_manager: FileManager


# Landing Screen
@ui.page("/")
def landing_page():

    def handle_create():
        file_manager.create_file()
        ui.navigate.to("/")

    # it had a weird white border so thats why this is here
    ui.query(".nicegui-content").classes("p-0")

    with ui.column().classes("w-full min-h-screen items-center py-12 bg-gray-100"):
        ui.label("Select a Document").classes("text-3xl font-bold text-gray-800 mb-6")

        available_files = file_manager.files

        # Added 'px-4' here so the cards don't scrape the absolute edge of a small browser window
        with ui.column().classes("gap-3 w-full max-w-3xl px-4"):
            # 2. FIXED THE BUTTON
            # Using props('outline color=green') guarantees the Quasar button formats the text correctly
            ui.button("+ Create New Document", on_click=handle_create).props(
                "outline color=green"
            ).classes("w-full mb-4 bg-white text-lg font-bold shadow-sm")

            if not available_files:
                ui.label("No files found.").classes(
                    "text-gray-500 italic text-center w-full py-8"
                )

            for filename in available_files:
                last_edited = file_manager.get_time_ago(filename)

                with (
                    ui.card()
                    .classes(
                        "w-full p-4 flex-row justify-between items-center cursor-pointer hover:bg-gray-200 transition-colors shadow-sm"
                    )
                    .on("click", lambda f=filename: ui.navigate.to(f"/editor/{f}"))
                ):
                    ui.label(filename).classes("text-lg font-semibold text-gray-800")
                    ui.label(f"Last edited {last_edited}").classes(
                        "text-sm text-gray-500 font-medium"
                    )


@ui.page("/editor/{filename}")
def render_editor(filename: str):
    file = file_manager.get_file(filename)

    # 1. STATE
    doc_state = file_manager.read_file(filename)
    last_sync_mtime = file_manager.get_system_mtime(filename)
    last_editor_mtime = datetime.now().timestamp()

    # 2. LOGIC

    def delete():
        file_manager.del_file(doc_state["title"])
        ui.navigate.history.replace(f"/")
        ui.navigate.to("/")

    def save(e=None):
        nonlocal file
        nonlocal last_sync_mtime

        # Only save if the editor content is newer than the file content
        if last_editor_mtime > last_sync_mtime:
            # 1. Get raw content from the UI
            raw_content = text_editor.value
            if not raw_content:
                raw_content = ""

            sanitized = raw_content

            # 2. Update internal state
            doc_state["content"] = sanitized
            doc_state["title"] = re.sub(r'[<>:"/\\|?*]', "", doc_state["title"])

            # 3. Save to disk
            actual_name = file_manager.save_file(file, doc_state)

            # 4. ONLY update the UI if we actually changed the string.
            # If the user just hit 'Enter', the browser's <div><br></div> is fine,
            # so we leave it alone.
            if text_editor.value != sanitized:
                text_editor.set_value(sanitized)

            # 5. Handle renaming
            if actual_name != file.stem:
                file = file_manager.get_file(actual_name)
                ui.navigate.history.replace(f"/editor/{actual_name}")

            last_sync_mtime = file_manager.get_system_mtime(actual_name)

    def on_editor_change(e):
        nonlocal last_editor_mtime
        last_editor_mtime = datetime.now().timestamp()
        doc_state.update({"content": e.value})

    # 3. LAYOUT
    autosave_timer = ui.timer(5.0, save)

    ui.query(".nicegui-content").classes("p-0")
    ui.add_css(".q-editor__toolbar { display: none !important; }")

    # header
    with ui.header().classes(
        "bg-white border-b border-gray-200 py-2 px-4 items-center flex-row gap-6"
    ):
        # home button
        ui.button(on_click=lambda: ui.navigate.to("/")).classes(
            "w-10 h-10 bg-[#F5F5DC]"
        ).props("square unelevated")
        # title field
        title_box = (
            ui.input()
            .bind_value(doc_state, "title")
            .props('dense input-class="text-2xl font-bold text-gray-800"')
            .classes("w-64")
        )

        # save and delete buttons
        with ui.row().classes("gap-1"):
            ui.button("Save", on_click=save, color="blue").props("flat size=sm")
            ui.button("Delete", on_click=delete, color="red").props("flat size=sm")

        title_box.on("keydown.ctrl.s.capture.prevent.stop", save)
        title_box.on("keydown.meta.s.capture.prevent.stop", save)

    # body
    with ui.column().classes("w-full min-h-screen items-center bg-gray-100 py-8"):
        text_editor = (
            ui.editor(
                value=doc_state["content"],
                on_change=on_editor_change,
            )
            .props("borderless autogrow")
            .classes(
                "w-full max-w-4xl bg-white text-lg px-10 py-5 min-h-[100vh] shadow-md"
            )
        )

        text_editor.on("keydown.ctrl.s.capture.prevent.stop", save)
        text_editor.on("keydown.meta.s.capture.prevent.stop", save)
