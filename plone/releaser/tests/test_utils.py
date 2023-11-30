from plone.releaser.utils import update_contents

import pathlib


TESTS_DIR = pathlib.Path(__file__).parent
INPUT_DIR = TESTS_DIR / "input"
# Sample buildout versions.cfg
VERSIONS = (INPUT_DIR / "versions.cfg").read_text()


def test_buildout_marker_to_pip_marker():
    from plone.releaser.utils import buildout_marker_to_pip_marker as trans

    assert trans("") == ""
    assert trans("unknown") == "unknown"
    assert trans('python_version == "3.8"') == 'python_version == "3.8"'
    assert trans('platform_system == "Linux"') == 'platform_system == "Linux"'
    assert trans("python2") == 'python_version < "3"'
    assert trans("python3") == 'python_version >= "3"'
    assert trans("python27") == 'python_version == "2.7"'
    assert trans("python38") == 'python_version == "3.8"'
    assert trans("python313") == 'python_version == "3.13"'
    assert trans("pypy") == 'implementation_name == "pypy"'
    assert trans("linux") == 'platform_system == "Linux"'
    assert trans("macosx") == 'platform_system == "Darwin"'
    assert trans("windows") == 'platform_system == "Windows"'


def test_update_contents_empty():
    assert update_contents("\n", lambda x: True, "", "") == "\n"


def test_update_contents_newline_at_end():
    assert update_contents("", lambda x: True, "", "") == "\n"


def test_update_contents_versions_match(capsys):
    def line_check(line):
        return line.startswith("package =")

    result = update_contents(VERSIONS, line_check, "package = 2.0", "file")
    assert "package = 2.0" in result
    assert "package = 1.0" not in result
    captured = capsys.readouterr()
    assert captured.out.strip() == "file: have set 'package = 2.0'."


def test_update_contents_versions_add_at_end(capsys):
    def line_check(line):
        return line.startswith("new =")

    result = update_contents(VERSIONS, line_check, "new = 2.0", "file")
    assert "new = 2.0" in result
    assert "new = 2.0" == result.splitlines()[-1]
    captured = capsys.readouterr()
    assert captured.out.strip() == "file: 'new = 2.0' added."


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
