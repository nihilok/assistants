import os
import pytest
from assistants.cli.fs import FilesystemService

@pytest.fixture
def temp_dir():
    tmp_dir = "/tmp/test_fs_service"
    os.makedirs(tmp_dir, exist_ok=True)
    yield tmp_dir
    import shutil
    shutil.rmtree(tmp_dir)

@pytest.mark.parametrize(
    "input_path,expected_output",
    [
        (lambda tmp: os.path.join(tmp, "d"), lambda tmp: os.path.join(tmp, "dir")),
        (lambda tmp: os.path.join(tmp, "dir1"), lambda tmp: os.path.join(tmp, "dir1")),
        (lambda tmp: os.path.join(tmp, "file"), lambda tmp: os.path.join(tmp, "file")),
        (lambda tmp: os.path.join(tmp, "file2"), lambda tmp: os.path.join(tmp, "file2.txt")),
        (lambda tmp: os.path.join(tmp, "nonexistent"), lambda tmp: os.path.join(tmp, "nonexistent")),
    ]
)
def test_filesystem_service_auto_complete_path(temp_dir, input_path, expected_output):
    # Create some test files and directories
    os.makedirs(os.path.join(temp_dir, "dir1"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "dir2"), exist_ok=True)
    with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
        f.write("test")
    with open(os.path.join(temp_dir, "file2.txt"), "w") as f:
        f.write("test")

    # Evaluate lambdas to get actual paths
    input_val = input_path(temp_dir)
    expected_val = expected_output(temp_dir)

    # Run the test
    fs_service = FilesystemService()
    assert fs_service.auto_complete_path(input_val) == expected_val
