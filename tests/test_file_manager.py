from notely.file_manager import FileManager
import json
import os
import time
from hypothesis import assume, given, strategies as st
from pathlib import Path
from pytest import fixture

forbidden_text = []

# Adapted From:
# Answer: https://stackoverflow.com/a/31976060
# User: https://stackoverflow.com/users/278842/christopher-oezbek
if os.name == "nt":
    forbidden_chars = ["<", ">", ":", '"', "/", "|", "?", "*"]
    forbidden_text.extend(
        (
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        )
    )
elif os.name == "darwin":
    forbidden_chars = [":", "/"]
else:
    forbidden_chars = ["/"]

# Adapted From:
# Answer: https://stackoverflow.com/a/3031026
# User: https://stackoverflow.com/users/235698/mark-tolonen
char_strat = st.characters(codec="utf-8").filter(
    lambda c: not (json.dumps(c).startswith('"\\') or (c in forbidden_chars))
)

name_strat = st.one_of(
    st.integers(),
    char_strat,
    st.text(alphabet=char_strat).filter(
        lambda t: not (json.dumps(t).startswith('"\\') or (t in forbidden_text))
    ),
).map(lambda suffix: f"file_{suffix}")

content_strat = st.text(alphabet=st.characters(codec="utf-8").filter(
    lambda c: not json.dumps(c).startswith('"\\')
))

@fixture
def file_manager(tmp_path):
    return FileManager(tmp_path)

# UT-01-CB: create_file()
@given(name=name_strat)
def test_create_file(name: int | str, file_manager: FileManager):
    file: Path = file_manager.get_file(name)
    assume(not file.exists())
    file_manager.create_file(name)
    assert file.exists()

# UT-02-CB: del_file()
@given(name=name_strat)
def test_delete_file(name: int | str, file_manager: FileManager):
    file: Path = file_manager.get_file(name)
    assume(not file.exists())
    file.touch()
    file_manager.del_file(name)
    assert not file.exists()

# UT-03-CB: save_file()
@given(name=name_strat, content=content_strat)
def test_save_file(name: int | str, content: str, file_manager: FileManager):
    file: Path = file_manager.get_file(name)
    assume(not file.exists())
    file_manager.create_file(name)
    doc = {"title": str(name), "content": f"<p>{content}</p>", "data": {}}
    file_manager.save_file(file, doc)
    assert file.exists()

# UT-04-CB: read_file()
@given(name=name_strat, content=content_strat)
def test_read_file(name: int | str, content: str, file_manager: FileManager):
    file: Path = file_manager.get_file(name)
    assume(not file.exists())
    file.touch()
    file.write_text(content)
    result = file_manager.read_file(str(name))
    assert "title" in result
    assert "content" in result
    assert "data" in result

# UT-05-CB: rename_file()
@given(old_name=name_strat, new_name=name_strat)
def test_rename_file(old_name: int | str, new_name: int | str, file_manager: FileManager):
    old_file: Path = file_manager.get_file(old_name)
    assume(not old_file.exists())
    new_file: Path = file_manager.get_file(new_name)
    assume(not new_file.exists())
    old_file.touch()
    file_manager.rename_file(old_name, new_name)
    if old_name != new_name:
        assert not old_file.exists()
    assert new_file.exists()

# UT-06-TB: get_name() with duplicate file
def test_get_name_duplicate(file_manager: FileManager):
    file_manager.create_file("untitled")
    result = file_manager.get_name("untitled")
    assert result == "untitled(1)"

# UT-07-TB: get_time_ago()
def test_get_time_ago(file_manager: FileManager):
    name = file_manager.create_file("untitled")
    file = file_manager.get_file(name)
    fifteen_minutes_ago = time.time() - (15 * 60)
    os.utime(file, (fifteen_minutes_ago, fifteen_minutes_ago))
    result = file_manager.get_time_ago(name)
    assert result == "15m ago"

# UT-08-OB: files property
def test_files_property(file_manager: FileManager):
    for i in range(5):
        file_manager.create_file(f"note_{i}")
    assert len(file_manager.files) == 5

# UT-09-CB: export_pdf()
def test_export_pdf(file_manager: FileManager):
    name = file_manager.create_file("untitled")
    file = file_manager.get_file(name)
    file.write_text("hello world")
    result = file_manager.export_pdf(name)
    assert isinstance(result, bytearray)
    assert result.startswith(b"%PDF")

# IT-01-TB: create_file() and FileManager
def test_it_create_file(file_manager: FileManager):
    name = file_manager.create_file("untitled")
    file = file_manager.get_file(name)
    assert file.exists()
    assert file.suffix == ".md"

# IT-02-TB: save_file() and FileManager
def test_it_save_file(file_manager: FileManager):
    name = file_manager.create_file("untitled")
    file = file_manager.get_file(name)
    doc = {"title": "untitled", "content": "<p>new content</p>", "data": {}}    
    file_manager.save_file(file, doc)
    result = file_manager.read_file(name)
    assert "new content" in result["content"]

# IT-03-CB: read_file() and FileManager
def test_it_read_file(file_manager: FileManager):
    name = file_manager.create_file("untitled")
    file = file_manager.get_file(name)
    file.write_text("test content")
    result = file_manager.read_file(name)
    assert result["title"] == name
    assert "content" in result
    assert "data" in result

# IT-04-TB: del_file() and FileManager
def test_it_delete_file(file_manager: FileManager):
    name = file_manager.create_file("untitled")
    file = file_manager.get_file(name)
    assert file.exists()
    file_manager.del_file(name)
    assert not file.exists()

# IT-05-TB: export_pdf() and FileManager
def test_it_export_pdf(file_manager: FileManager):
    name = file_manager.create_file("untitled")
    file = file_manager.get_file(name)
    file.write_text("**bold** and *italic* content")
    result = file_manager.export_pdf(name)
    assert isinstance(result, bytearray)
    assert result.startswith(b"%PDF")
