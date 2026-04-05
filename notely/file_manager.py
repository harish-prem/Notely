import re
import yaml

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
                return "just now"
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
        self.get_file(name).touch()
        return name

    def rename_file(self, old_name, new_name):
        if old_name == new_name:
            return new_name

        new_name = self.get_name(new_name)

        try:
            # Just move the file, don't open/write it here!
            self.get_file(old_name).rename(self.get_file(new_name))

            return new_name
        except Exception as e:
            print(f"Rename failed: {e}")
            return old_name

    def read_file(self, name):
        fileinfo = {"data": {}, "title": name, "content": ""}
        file = self.get_file(name)
        if not file.exists():
            return fileinfo

        writing_data = False
        data = ""
        content = ""

        with file.open("r") as f:
            for index, line in enumerate(f):
                clean_line = line.rstrip("\n")
                if clean_line == "---":
                    # TODO: Optimize with boolean algebra.
                    if index:
                        writing_data = False
                    elif not writing_data:
                        writing_data = True

                if writing_data:
                    data += line
                else:
                    content += line

            fileinfo["data"] = yaml.safe_load(data)
            fileinfo["content"] = mdit.render(content)

        return fileinfo

    @cache
    def sanitize_filename(self, name):
        return re.sub(r'[<>:"/\\|?*]', "", name)

    def save_file(self, file, doc):
        # 1. Handle name changes/conflicts first
        actual_name = self.rename_file(file.stem, doc["title"])

        # 2. Write the whole structure
        split_doc = doc["content"].split("<br>")
        split_length = len(split_doc)
        with self.get_file(actual_name).open("w") as f:
            for index, line in enumerate(split_doc):
                if line == "</div><div>":
                    f.write("\n")
                elif line:
                    if index:
                        f.write("\n")
                    f.write("\n".join(filter(None, md(line).split("\n"))))
                    if (index + 1) == split_length:
                        f.write("\n")

        return actual_name

    def del_file(self, name):
        self.get_file(name).unlink(missing_ok=True)

    def get_system_mtime(self, name):
        file = self.get_file(name)
        return file.stat().st_mtime if file.exists() else 0

    def get_system_ctime(self, name):
        file = self.get_file(name)
        return file.stat().st_ctime if file.exists() else 0


file_manager: FileManager = FileManager()
