from plone.releaser.utils import update_contents

import pathlib


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
# Sample buildout versions.cfg
VERSIONS = (INPUT_DIR / "versions.cfg").read_text()


def test_update_contents_empty():
    assert update_contents("\n", lambda x: True, "", "") == "\n"


def test_update_contents_newline_at_end():
    assert update_contents("", lambda x: True, "", "") == "\n"


def test_update_contents_versions_match():
    def line_check(line):
        return line.startswith("package =")

    result = update_contents(VERSIONS, line_check, "package = 2.0", "")
    assert "package = 2.0" in result
    assert "package = 1.0" not in result


def test_update_contents_versions_add_at_end():
    def line_check(line):
        return line.startswith("new =")

    result = update_contents(VERSIONS, line_check, "new = 2.0", "")
    assert "new = 2.0" in result
    assert "new = 2.0" == result.splitlines()[-1]


def test_update_contents_versions_add_before_markers():
    def line_check(line):
        return line.startswith("new =")

    def stop_check(line):
        # If we see this line, we should stop trying to match.
        return line.startswith("[versions:")

    result = update_contents(
        VERSIONS, line_check, "new = 2.0", "", stop_check=stop_check
    )
    assert "new = 2.0" in result
    assert result.index("new = 2.0") < result.index("[versions:")
    lines = result.splitlines()
    new_index = lines.index("new = 2.0")
    # We have left a blank line.
    assert lines[new_index + 1] == ""
    assert lines[new_index + 2] == "[versions:python312]"


def test_update_contents_versions_removes_duplicates():
    def line_check(line):
        return line.startswith("duplicate =")

    result = update_contents(VERSIONS, line_check, "duplicate = 2.0", "")
    assert "duplicate = 2.0" in result
    assert result.count("duplicate =") == 1
