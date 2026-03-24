from pathlib import Path
from datetime import datetime
import os
import re

cd = Path('')

def get_files():
    files = []
    for item in cd.iterdir():
        files.append(item.name[:-3])
    return files

def get_time_ago(name):
    doc = read_file(name)
    timestamp = doc["data"][1]
    try:
        ts = float(timestamp)
        diff = datetime.now().timestamp() - ts
        if diff < 60:
            return "Just now"
        if diff < 3600:
            return f"{int(diff // 60)}m ago"
        if diff < 86400:
            return f"{int(diff // 3600)}h ago"
        return f"{int(diff // 86400)}d ago"
    except (ValueError, TypeError):
        return "Unknown"

def change_directory(directory):
    global cd
    cd = Path(directory)

def create_file(name="untitled"):
    files = get_files()
    final_name = name
    counter = 1

    # Loop to find a unique name
    while final_name in files:
        final_name = f"{name}({counter})"
        counter += 1

    try:
        # Use Unix timestamp for metadata lines 1 and 2
        now_ts = str(datetime.now().timestamp())

        with open(f"{cd}/{final_name}.md", 'w') as file:
            # Metadata: Line 1 (Created), Line 2 (Modified)
            file.write(f"{now_ts}\n{now_ts}\n---\n{final_name}\n---\n")

        return final_name  # Return this so the UI knows where to go
    except IOError as e:
        print(f"An error occurred: {e}")
        return None

def rename_file(old_name, new_name):
    if old_name == new_name:
        return new_name

    files = get_files()
    final_name = new_name
    counter = 1
    while final_name in files:
        final_name = f"{new_name}({counter})"
        counter += 1

    try:
        # Just move the file, don't open/write it here!
        Path(f"{cd}/{old_name}.md").rename(f"{cd}/{final_name}.md")
        return final_name
    except Exception as e:
        print(f"Rename failed: {e}")
        return old_name


def read_file(name):
    fileinfo = {"data": [], "title": name, "oldTitle": name, "content": ""}
    path = Path(f"{cd}/{name}.md")
    if not path.exists(): return fileinfo

    with open(path, 'r') as file:
        # Loop 1: Metadata (Everything until the first ---)
        for line in file:
            clean_line = line.rstrip('\n')
            if clean_line == "---":
                break
            fileinfo["data"].append(clean_line)

        # Loop 2: Title (The single line between the first and second ---)
        for line in file:
            clean_line = line.rstrip('\n')
            if clean_line == "---":
                break
            fileinfo["title"] = clean_line
            fileinfo["oldTitle"] = clean_line

        # Loop 3: The rest is content
        fileinfo["content"] = file.read()

    return fileinfo

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', name)

def save_file(doc):
    # 1. Handle name changes/conflicts first
    actual_name = rename_file(doc['oldTitle'], doc['title'])

    # 2. Update the 'Modified' timestamp (Index 1)
    # We ensure the list has at least 2 items so we don't get an IndexError
    while len(doc['data']) < 2:
        doc['data'].append(str(datetime.now().timestamp()))

    # Update only the second line (Modified Date)
    doc['data'][1] = str(datetime.now().timestamp())

    # 3. Write the whole structure
    path = Path(f"{cd}/{actual_name}.md")
    with open(path, 'w') as f:
        # Write EVERY line in the data list until the separator
        for item in doc['data']:
            f.write(f"{item}\n")
        f.write("---\n")

        # Title Section
        f.write(f"{actual_name}\n")
        f.write("---\n")

        # Content Section
        f.write(doc['content'])

    return actual_name

def del_file(name):
    if os.path.exists(f"{cd}/{name}.md"):
        os.remove(f"{cd}/{name}.md")

def get_system_mtime(name):
    path = Path(f"{cd}/{name}.md")
    return path.stat().st_mtime if path.exists() else 0