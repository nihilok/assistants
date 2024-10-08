import os
import subprocess
import tempfile


def get_text_from_default_editor(initial_text=None):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
        temp_file_path = temp_file.name

    if initial_text:
        with open(temp_file_path, "w") as text_file:
            text_file.write(initial_text)

    # Open the editor for the user to input text
    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, temp_file_path])

    # Read the contents of the file after the editor is closed
    with open(temp_file_path, "r") as file:
        text = file.read()

    # Remove the temporary file
    os.remove(temp_file_path)

    return text
