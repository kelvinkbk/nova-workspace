from tools.filesystem import list_project_files, read_project_file


def test_list_project_files_returns_project_files():
    result = list_project_files()
    assert isinstance(result, str)
    assert "core" in result or "database" in result
    assert ".venv" not in result
    assert "__pycache__" not in result


def test_read_project_file_reads_workspace_file():
    result = read_project_file("README.md")

    assert isinstance(result, str)


def test_read_project_file_rejects_path_traversal():
    result = read_project_file("../README.md")

    assert result == "File denied: path is outside the NOVA workspace."


def test_read_project_file_rejects_directories():
    result = read_project_file("core")

    assert result == "File denied: core is not a file."


def test_read_project_file_handles_missing_file():
    result = read_project_file("does-not-exist.txt")

    assert result == "File not found: does-not-exist.txt"
