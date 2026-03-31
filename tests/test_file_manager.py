from notely.file_manager import FileManager
import json
import os
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


@fixture
def file_manager(tmp_path):
    return FileManager(tmp_path)


@given(name=name_strat)
def test_create_file(name: int | str, file_manager: FileManager):
    file: Path = file_manager.get_file(name)
    assume(not file.exists())
    file_manager.create_file(name)
    assert file.exists()


@given(name=name_strat)
def test_delete_file(name: int | str, file_manager: FileManager):
    file: Path = file_manager.get_file(name)
    assume(not file.exists())
    file.touch()
    file_manager.del_file(name)
    assert not file.exists()


@given(old_name=name_strat, new_name=name_strat)
def test_rename_file(
    old_name: int | str, new_name: int | str, file_manager: FileManager
):
    old_file: Path = file_manager.get_file(old_name)
    assume(not old_file.exists())
    new_file: Path = file_manager.get_file(new_name)
    assume(not new_file.exists())
    old_file.touch()
    file_manager.rename_file(old_name, new_name)
    if old_name != new_name:
        assert not old_file.exists()
    assert new_file.exists()
