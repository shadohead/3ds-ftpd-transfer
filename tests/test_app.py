from email.message import Message
import zipfile

from ftpd_transfer.app import (
    CHEAT_DATABASE_NAME,
    DEFAULT_REMOTE_FOLDER,
    TWILIGHT_CHEAT_REMOTE_FOLDER,
    filename_from_response,
    prepare_usrcheat_database,
    sanitize_remote_folder,
)


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


def test_twilight_cheat_destination():
    assert TWILIGHT_CHEAT_REMOTE_FOLDER == "/_nds/TWiLightMenu/extras"


def test_prepare_usrcheat_database_renames_dat(tmp_path):
    source = tmp_path / "custom-name.dat"
    source.write_bytes(b"cheats")

    prepared, cleanup_dir = prepare_usrcheat_database(str(source))

    assert prepared.endswith(CHEAT_DATABASE_NAME)
    assert open(prepared, "rb").read() == b"cheats"
    assert cleanup_dir is not None


def test_prepare_usrcheat_database_extracts_zip(tmp_path):
    source = tmp_path / "usrcheat.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("folder/usrcheat.dat", b"cheats")

    prepared, cleanup_dir = prepare_usrcheat_database(str(source))

    assert prepared.endswith(CHEAT_DATABASE_NAME)
    assert open(prepared, "rb").read() == b"cheats"
    assert cleanup_dir is not None
