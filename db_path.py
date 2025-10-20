# pip install pyobjc
import sqlite3
from pathlib import Path

from Foundation import (
    NSFileManager,
    NSBundle,
    NSApplicationSupportDirectory,
    NSUserDomainMask,
)

def db_path(filename: str, dev_env: bool) -> Path:
    """
    Resolve ~/Library/Application Support/<bundle id>/<filename>
    using Cocoa APIs (works in sandbox & non-sandbox).
    Ensures the app subdirectory exists.
    """
    
    if dev_env:
        return Path(filename)

    fm = NSFileManager.defaultManager()

    # 1) Base Application Support directory
    base_url, err = fm.URLForDirectory_inDomain_appropriateForURL_create_error_(
        NSApplicationSupportDirectory,
        NSUserDomainMask,
        None,   # appropriateForURL
        True,   # create if missing
        None,   # error** (returned separately)
    )
    if base_url is None:
        raise OSError(f"Unable to get Application Support dir: {err}")

    # 2) Bundle identifier (fallback if missing)
    bundle_id = NSBundle.mainBundle().bundleIdentifier()
    if not bundle_id:
        bundle_id = "felipediasazevedo.mediaext"

    # 3) App-specific folder under Application Support
    app_dir_url = base_url.URLByAppendingPathComponent_isDirectory_(bundle_id, True)

    ok, err = fm.createDirectoryAtURL_withIntermediateDirectories_attributes_error_(
        app_dir_url, True, None, None
    )
    # In PyObjC, createDirectory... returns (True, None) on success but may already exist.
    # If it *already exists*, ok is True and err is None—so no special case needed.
    if not ok:
        raise OSError(f"Unable to create app support subdir: {err}")

    # 4) Final DB URL
    db_url = app_dir_url.URLByAppendingPathComponent_isDirectory_(filename, False)
    return Path(str(db_url.path()))

if __name__ == "__main__":
    import sys
    dev = "--dev" in sys.argv
    db_path = db_path("media.db", dev)
    print("DB path:", db_path)

