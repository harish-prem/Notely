# editor_ui.py

import re
import inspect

from nicegui import app, ui

import auth
from file_manager import FileManager, file_manager
import asyncio
from datetime import datetime
import base64
from pathlib import Path

file_manager: FileManager


@ui.page("/")
async def landing_page():
    
    user_id = await auth.logged_in_as()
    if not user_id:
        auth.login()
        return

    user_fm = file_manager.for_user(user_id)

    # 1. State container
    state = {
        "search_query": "",
        "search_tags": [],
        "sort_by": "Date Edited",
        "sort_order": "Desc"
    }
    


    # tags
    current_edit = {"original_name": ""}
    tag_dialog = ui.dialog()

    with tag_dialog, ui.card().classes('w-[400px] shadow-xl rounded-lg'):
        ui.label('Manage Document').classes('text-xl font-bold mb-1 text-gray-800')


        dialog_filename = ui.input('Filename').classes('w-full mb-4 font-mono text-gray-700')

        def handle_new_tag(e):
            new_val = e.args[0] if isinstance(e.args, (list, tuple)) else e.args

            if not new_val or not str(new_val).strip():
                return

            new_val = str(new_val).strip()

            if new_val not in tag_input.options:
                tag_input.options.append(new_val)

            current_tags = list(tag_input.value or [])
            if new_val not in current_tags:
                current_tags.append(new_val)
                tag_input.value = current_tags

            tag_input.run_method('updateInputValue', '')
            tag_input.update()

        tag_input = ui.select(
            options=["Draft", "Work", "Personal", "Todo"],
            multiple=True,
            value=[],
            with_input=True,
            new_value_mode='add',
            label="Select or type a new tag..."
        ).props('use-chips').classes('w-full mb-6')

        tag_input.on('new-value', handle_new_tag)

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=tag_dialog.close).props('flat text-color=gray-500')

            def on_save():
                orig_name = current_edit["original_name"]

                new_name = dialog_filename.value.strip() or orig_name


                doc_state = user_fm.read_file(orig_name)

                doc_state["title"] = new_name
                doc_state["data"]["tags"] = [str(t) for t in tag_input.value if t and str(t).strip()]

                user_fm.save_file(user_fm.get_file(orig_name), doc_state)

                tag_dialog.close()
                document_grid.refresh()

            ui.button('Save', on_click=on_save).props('color=green text-color=white')

    def open_tag_dialog(filename, current_tags):
        current_edit["original_name"] = filename
        dialog_filename.value = filename

        all_t = {"Draft", "Work", "Personal", "Todo"}
        for f in get_file_previews():
            for t in f['tags']:
                all_t.add(t)

        tag_input.options = sorted(list(all_t))
        tag_input.set_value(list(current_tags) if current_tags else [])
        tag_dialog.open()

    # files

    def handle_export(filename):
        pdf_bytes = user_fm.export_pdf(filename)
        b64 = base64.b64encode(pdf_bytes).decode()
        ui.run_javascript(f""" 
                    const a = document.createElement("a");
                    a.href = "data:application/pdf;base64, {b64}";
                    a.download = "{filename}.pdf"
                    a.click();
                """)

    async def handle_create():
        if state["search_query"] == "":
            file = user_fm.create_file()
        else:
            file = user_fm.create_file(state["search_query"])

        ui.navigate.to(f"/editor/{file}")
        
            
        # document_grid.refresh()

    def handle_delete(filename):
        user_fm.del_file(filename)
        document_grid.refresh()

    def get_file_previews():
        previews = []
        for filename in user_fm.files:
            last_edited = user_fm.get_time_ago(filename)
            mtime = user_fm.get_system_mtime(filename)
            ctime = user_fm.get_system_ctime(filename)

            ctime_display = datetime.fromtimestamp(ctime).strftime("%b %d, %Y") if ctime > 0 else "Unknown"

            fileinfo = user_fm.read_file(filename)
                

            # Extract tags safely
            raw_tags = fileinfo.get("data", {}).get("tags", []) if fileinfo.get("data") else []
            tags = raw_tags if isinstance(raw_tags, list) else [raw_tags]
            tags = [str(t).strip() for t in tags if t]

            # Create snippet
            raw_html = fileinfo.get("content", "")
            clean_text = re.sub(r'<[^>]+>', '', raw_html).strip()
            snippet = clean_text if clean_text else "Empty document..."
            snippet = snippet[0:57]+"..." if len(snippet) > 60 else snippet

            previews.append({
                "name": filename,
                "time_ago": last_edited,
                "mtime": mtime,
                "ctime": ctime,
                "ctime_display": ctime_display,
                "tags": tags,
                "snippet": snippet
            })
        return previews

    # ui elements

    @ui.refreshable
    def document_grid():
        available_files = get_file_previews()

        # Sync the global tag filter options
        all_tags = set()
        for f in available_files:
            for t in f['tags']:
                all_tags.add(t)
        tag_filter_dropdown.options = sorted(list(all_tags))
        tag_filter_dropdown.update()

        # Filter by Search Query
        if state["search_query"]:
            query = state["search_query"].lower()
            available_files = [f for f in available_files if query in f['name'].lower()]

        # Filter by Selected Tags
        if state["search_tags"]:
            available_files = [
                f for f in available_files
                if all(req_tag in f['tags'] for req_tag in state["search_tags"])
            ]

        # Sort files
        is_descending = state["sort_order"] == "Desc"
        if state["sort_by"] == "Name":
            available_files.sort(key=lambda x: x['name'].lower(), reverse=is_descending)
        elif state["sort_by"] == "Date Edited":
            available_files.sort(key=lambda x: x['mtime'], reverse=is_descending)
        elif state["sort_by"] == "Date Created":
            available_files.sort(key=lambda x: x['ctime'], reverse=is_descending)

        # Render Grid
        with ui.element('div').classes(
                "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 w-full max-w-6xl px-4"):

            # New Document Button
            with ui.card().classes(
                    "w-full h-48 flex flex-col items-center justify-center cursor-pointer bg-white border-2 border-dashed border-gray-300 hover:border-green-500 hover:bg-green-50 transition-all shadow-sm").on(
                    "click", handle_create):
                ui.icon("add_circle_outline", size="3rem").classes("text-green-600 mb-2")
                ui.label("New Document").classes("text-lg font-bold text-gray-700")

            # File Cards
            for file_data in available_files:
                with ui.card().classes(
                        "w-full h-48 flex flex-col justify-between cursor-pointer bg-white hover:shadow-lg transition-shadow border border-gray-200 relative").on(
                        "click", lambda e, f=file_data['name']: ui.navigate.to(f"/editor/{f}")):

                    with ui.column().classes("w-full gap-2"):
                        with ui.row().classes("w-full justify-between items-start flex-nowrap"):
                            ui.label(file_data['name']).classes("text-xl font-bold text-gray-800 truncate")

                            with ui.button(icon='more_vert').props('flat round dense').classes(
                                    'text-gray-400 hover:text-gray-800 -mt-1 -mr-2').on('click.stop', lambda e: None):
                                with ui.menu():
                                    ui.menu_item('Manage File', on_click=lambda e, f=file_data['name'],
                                                                                t=file_data['tags']: open_tag_dialog(f,
                                                                                                                     t)).classes(
                                        'text-blue-600 font-medium')
                                    ui.menu_item('Export PDF',
                                                 on_click=lambda e, f=file_data['name']: handle_export(f)).classes(
                                        'text-purple-600 font-medium')
                                    ui.menu_item('Delete',
                                                 on_click=lambda e, f=file_data['name']: handle_delete(f)).classes(
                                        'text-red-600 font-medium')

                        # Tag Chips
                        if file_data['tags']:
                            with ui.row().classes("flex-wrap gap-1 mb-1"):
                                for tag in file_data['tags'][:3]:
                                    ui.label(tag).classes(
                                        "text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider")
                                if len(file_data['tags']) > 3:
                                    ui.label(f"+{len(file_data['tags']) - 3}").classes(
                                        "text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-bold")

                        ui.label(file_data['snippet']).classes("text-sm text-gray-500 line-clamp-3 leading-snug")

                    with ui.row().classes(
                            "w-full items-center mt-auto border-t border-gray-100 pt-3 gap-1.5 flex-nowrap"):
                        ui.icon("info_outline", size="1rem").classes("text-gray-400 shrink-0")
                        ui.label(f"Created {file_data['ctime_display']} • Edited {file_data['time_ago']}").classes(
                            "text-xs font-medium text-gray-400 truncate flex-1 min-w-0"
                        )

    # layout
    ui.query(".nicegui-content").classes("p-0")

    with ui.column().classes("w-full min-h-screen items-center py-12 bg-gray-50"):
        with ui.row().classes("w-full max-w-6xl px-4 items-center justify-between mb-4"):
            ui.label("My Documents").classes("text-4xl font-extrabold text-gray-800 tracking-tight")
            if not auth.NO_AUTH:
                ui.button("Logout", icon="logout", on_click=auth.logout).props('outline color=red')

        with ui.row().classes("w-full max-w-6xl px-4 mb-8 justify-between items-center gap-4 flex-wrap sm:flex-nowrap"):
            with ui.row().classes("flex-grow flex-nowrap items-center gap-2"):
                ui.input(placeholder="Search documents...", on_change=document_grid.refresh).bind_value(state,
                                                                                                        "search_query").props(
                    'outlined dense clearable').classes("flex-grow min-w-[200px] bg-white")

                global tag_filter_dropdown
                tag_filter_dropdown = ui.select(
                    options=[],
                    multiple=True,
                    with_input=True,
                    label="Filter Tags",
                    on_change=document_grid.refresh
                ).bind_value(state, "search_tags").props('use-chips dense clearable').classes("w-56 bg-white")

            with ui.row().classes("items-center gap-2 w-full sm:w-auto flex-nowrap"):
                ui.select(options=["Date Edited", "Date Created", "Name"], on_change=document_grid.refresh).bind_value(
                    state, "sort_by").props('outlined dense').classes("w-40 bg-white")

                def toggle_order(e):
                    state["sort_order"] = "Asc" if state["sort_order"] == "Desc" else "Desc"
                    e.sender.icon = 'arrow_upward' if state["sort_order"] == "Asc" else 'arrow_downward'
                    document_grid.refresh()

                ui.button(icon='arrow_downward', on_click=toggle_order).props(
                    'outline color=grey-5 text-color=grey-9').classes("bg-white h-[40px] px-3 shadow-none")

        document_grid()

@ui.page("/editor/{filename}")
async def render_editor(filename: str):
    user_id = await auth.logged_in_as()
    if not user_id:
        ui.notify("You do not have access to this note.", color="negative")
        return

    user_fm = file_manager.for_user(user_id)
    file = user_fm.get_file(filename)

    if not user_fm.file_exists(filename):
        ui.navigate.to('/')
        return

    # 1. STATE
    doc_state = user_fm.read_file(filename)

    last_sync_mtime = user_fm.get_system_mtime(filename)
    last_editor_mtime = datetime.now().timestamp()

    # 2. LOGIC

    def delete():
        try:
            user_fm.del_file(doc_state["title"])
        except PermissionError:
            ui.notify("You do not have access to delete this note.", color="negative")
            return
        ui.navigate.history.replace(f"/")
        ui.navigate.to("/")

    def save(e=None):
        nonlocal file
        nonlocal last_sync_mtime

        # 1. Get raw content from the UI
        raw_content = text_editor.value
        if not raw_content:
            raw_content = ""

        # 2. Update internal state
        doc_state["content"] = raw_content
        actual_name = doc_state["title"] = re.sub(r'[<>:"/\\|?*]', "", doc_state["title"])

        # Only save if the editor content is newer than the file content
        if (actual_name != file.stem) or (last_editor_mtime > last_sync_mtime):
            # 3. Save to disk
            actual_name = user_fm.save_file(file, doc_state)

            # 4. ONLY update the UI if we actually changed the string.
            # If the user just hit 'Enter', the browser's <div><br></div> is fine,
            # so we leave it alone.
            if text_editor.value != raw_content:
                text_editor.set_value(raw_content)

            # 5. Handle renaming
            if actual_name != file.stem:
                file = file_manager.get_file(actual_name)
                ui.navigate.history.replace(f"/editor/{actual_name}")

            last_sync_mtime = file_manager.get_system_mtime(actual_name)

    def export_pdf():
        pdf_bytes = user_fm.export_pdf(filename)
        b64 = base64.b64encode(pdf_bytes).decode()
        ui.run_javascript(f""" 
            const a = document.createElement("a");
            a.href = "data:application/pdf;base64, {b64}";
            a.download = "{filename}.pdf"
            a.click();
        """)

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
            ui.button("Export PDF", on_click=export_pdf, color="purple").props("flat size=sm")

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
