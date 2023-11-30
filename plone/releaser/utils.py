def buildout_marker_to_pip_marker(marker):
    """Translate a Buildout marker to a pip marker.

    Example:

        [versions:python38]
        package = 1.0

    This translates to:

        package==1.0; python_version == "3.8"

    The Buildout markers are defined here:
    https://github.com/buildout/buildout/blob/3.0.1/src/zc/buildout/buildout.py#L1724

    The pip markers are defined in PEP-508:
    https://peps.python.org/pep-0508/#environment-markers

    It seems hard to translate *all* possible markers.
    But we can do the ones used in the Plone core development buildout.
    Even with those, I do not see a 100% correct translation between the two.

    Buildout supports the pip markers natively since version 3.0.0, so you can write:

        [versions:python_version == "3.8"]
        package = 1.0

    See https://github.com/buildout/buildout/pull/622
    """
    if not marker:
        return marker

    # Python versions
    if marker.startswith("python"):
        if marker.startswith("python_version"):
            # already a pip marker
            return marker
        if marker == "python2":
            return 'python_version < "3"'
        if marker == "python3":
            return 'python_version >= "3"'
        version = marker[len("python") :]
        major = version[0]
        minor = version[1:]
        return f'python_version == "{major}.{minor}"'

    # Python implementations
    if marker in ("cpython", "pypy", "jython", "ironpython"):
        # Buildout checks sys.version.lower().
        # pip uses the equivalent of sys.implementation.name.
        return f'implementation_name == "{marker}"'

    # system platforms
    # Buildout mostly uses str(sys.platform).lower() and then has a mapping to more
    # common names.  For pip, platform_system seems best in most cases.
    if marker == "linux":
        return 'platform_system == "Linux"'
    if marker == "macosx":
        return 'platform_system == "Darwin"'
    if marker == "windows":
        return 'platform_system == "Windows"'
    if marker == "solaris":
        return 'platform_system == "SunOS"'
    if marker == "posix":
        return 'os_name == "posix"'
    if marker == "cygwin":
        return 'sys_platform == "cygwin"'

    # We are missing a few, like bits64 and big_endian.
    # Or this is an invalid marker.
    # Or this already is a pip marker.
    return marker


def update_contents(
    contents, line_check, newline, filename, start_check=None, stop_check=None
):
    """Update contents to have a new line if needed.

    * contents is some file contents
    * line_check is a function we call to check if a line matches.
    * newline is the line with which we replace the matched line.
      This can be None to signal that the old line should be removed
    * filename is used for reporting.
    * start_check is an optional function we call to check if we should start
      trying to match.
    * stop_check is an optional function we call to check if we should stop
      trying to match.

    Returns the new contents.
    """
    lines = []
    found = False
    content_lines = contents.splitlines()
    while content_lines:
        line = content_lines.pop(0)
        line = line.rstrip()
        if start_check is not None:
            if start_check(line):
                # We start searching now.  Disable the start_check.
                start_check = None
            lines.append(line)
            continue
        if stop_check is not None and stop_check(line):
            # Put this line back.  We will handle this line and the other
            # remaining lines outside of this loop.
            content_lines.insert(0, line)
            break
        if not line_check(line):
            lines.append(line)
            continue
        # We have a match.
        if found:
            # This is a duplicate, ignore the line.
            continue
        found = True
        # Include this line only if we want it enabled.
        if newline is None:
            print(f"{filename}: '{line}' removed.")
        elif line == newline:
            lines.append(line)
            print(f"{filename}: '{newline}' already there.")
        else:
            lines.append(newline)
            print(f"{filename}: have set '{newline}'.")

    if not found:
        if newline is None:
            print(f"{filename}: line not found.")
        else:
            if lines and not lines[-1]:
                # Insert before this last empty line.
                lines.insert(-1, newline)
            else:
                lines.append(newline)
            print(f"{filename}: '{newline}' added.")

    if content_lines:
        lines.extend(content_lines)

    result = "\n".join(lines)
    if not result.endswith("\n"):
        result += "\n"
    return result
