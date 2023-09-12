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
