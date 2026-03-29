import re

from collections import namedtuple
from datetime import datetime
from functools import cache
from markdownify import markdownify as md
from markdown_it import MarkdownIt
from pathlib import Path

mdit = MarkdownIt()

Defaults = namedtuple("Defaults", "directory,name")
defaults = Defaults(Path.home() / "Documents" / "Notely", "untitled")


class FileManager:
    @property
    def directory(self) -> Path:
        return self._directory

    @directory.setter
    def directory(self, value):
        if value:
            self._directory = (
                value if isinstance(value, Path) else Path(value).resolve()
            )
        else:
            self._directory = defaults.directory
        self._directory.mkdir(exist_ok=True)

    def __init__(
        self,
        directory: str | Path | None = defaults.directory,
        default_name: str = defaults.name,
    ):
        self.directory: Path = directory

        self.default_name: str = default_name
        self.ext = ".md"

    @property
    def files(self) -> list[str]:
        return [file.stem for file in self.directory.iterdir()]

    def get_time_ago(self, name: str):

        timestamp = self.get_system_mtime(name)

        try:
            diff = datetime.now().timestamp() - float(timestamp)
            if diff < 60:
                return "Just now"
            if diff < 3600:
                return f"{int(diff // 60)}m ago"
            if diff < 86400:
                return f"{int(diff // 3600)}h ago"
            return f"{int(diff // 86400)}d ago"
        except (ValueError, TypeError) as e:
            print(f"Getting time ago failed: {e}")
            return "Unknown"

    def __hash__(self):
        return hash((self.directory, self.default_name, self.ext))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                (self.directory == other.directory)
                and (self.default_name == other.default_name)
                and (self.ext == other.ext)
            )
        return False

    @cache
    def get_file(self, name: str):
        return self.directory / (name + self.ext)

    def file_exists(self, name):
        if isinstance(name, Path):
            return name.exists()
        return self.get_file(name).exists()

    def get_name(self, name):
        files: list[str] = self.files
        final_name: str = name
        counter: int = 1

        # Loop to find a unique name
        while final_name in files:
            final_name = f"{name}({counter})"
            counter += 1

        return final_name

    def create_file(self, name=None):
        name = self.get_name(name or self.default_name)

        try:
            (self.directory / (name + self.ext)).write_text(
                # Metadata: Line 1 (Created), Line 2 (Modified)
                # f"{now_ts}\n{now_ts}\n---\n{name}\n---\n"
                f"---\n{name}\n---\n"
            )

            return name  # Return this so the UI knows where to go
        except IOError as e:
            print(f"An error occurred: {e}")

    def rename_file(self, old_name, new_name):
        if old_name == new_name:
            return new_name

        new_name = self.get_name(new_name)

        try:
            # Just move the file, don't open/write it here!
            (self.directory / (old_name + self.ext)).rename(
                self.directory / (new_name + self.ext)
            )

            return new_name
        except Exception as e:
            print(f"Rename failed: {e}")
            return old_name

    def read_file(self, name):
        fileinfo = {"data": [], "title": name, "oldTitle": name, "content": ""}
        path = Path(f"{self.directory}/{name}.md")
        if not path.exists():
            return fileinfo

        with open(path, "r") as file:
            # Loop 1: Metadata (Everything until the first ---)
            for line in file:
                clean_line = line.rstrip("\n")
                if clean_line == "---":
                    break
                fileinfo["data"].append(clean_line)

            # Loop 2: Title (The single line between the first and second ---)
            for line in file:
                clean_line = line.rstrip("\n")
                if clean_line == "---":
                    break
                fileinfo["title"] = clean_line
                fileinfo["oldTitle"] = clean_line

            # Loop 3: The rest is content
            fileinfo["content"] = mdit.render(file.read())

        return fileinfo

    @cache
    def sanitize_filename(self, name):
        return re.sub(r'[<>:"/\\|?*]', "", name)

    def save_file(self, doc):
        # 1. Handle name changes/conflicts first
        actual_name = self.rename_file(doc["oldTitle"], doc["title"])

        # 2. Update the 'Modified' timestamp (Index 1)
        # We ensure the list has at least 2 items so we don't get an IndexError
        while len(doc["data"]) < 2:
            doc["data"].append(str(datetime.now().timestamp()))

        # Update only the second line (Modified Date)
        doc["data"][1] = str(datetime.now().timestamp())

        # 3. Write the whole structure
        file = self.directory / (actual_name + self.ext)
        with file.open("w") as f:
            # Write EVERY line in the data list until the separator
            for item in doc["data"]:
                f.write(f"{item}\n")
            f.write("---\n")

            # Title Section
            f.write(f"{actual_name}\n")
            f.write("---\n")

            # Content Section
            f.write(md(doc["content"]))

        return actual_name

    def del_file(self, name):
        (self.directory / (name + self.ext)).unlink(missing_ok=True)

    def get_system_mtime(self, name):
        file = self.directory / (name + self.ext)
        return file.stat().st_mtime if file.exists() else 0


file_manager: FileManager = FileManager()
