from email.message import Message

from ftpd_transfer.app import DEFAULT_REMOTE_FOLDER, filename_from_response, sanitize_remote_folder


def test_sanitize_remote_folder_defaults():
    assert sanitize_remote_folder("") == DEFAULT_REMOTE_FOLDER
    assert sanitize_remote_folder(None) == DEFAULT_REMOTE_FOLDER


def test_sanitize_remote_folder_normalizes_slashes():
    assert sanitize_remote_folder("cias") == "/cias"
    assert sanitize_remote_folder("/roms/nds/") == "/roms/nds"


def test_filename_from_response_uses_content_disposition():
    headers = Message()
    headers["Content-Disposition"] = 'attachment; filename="homebrew.zip"'
    assert filename_from_response("https://example.com/download", headers) == "homebrew.zip"


def test_filename_from_response_uses_url_path():
    headers = Message()
    assert filename_from_response("https://example.com/files/test%20file.3dsx", headers) == "test file.3dsx"
