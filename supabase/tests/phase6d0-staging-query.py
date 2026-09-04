"""Fixed-staging Management API transport for synthetic SQL tests. Secrets never leave memory."""
import ctypes
from ctypes import wintypes
import json
import re
import sys
import urllib.request
import urllib.error

class Credential(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME), ("BlobSize", wintypes.DWORD),
                ("Blob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]

def credential():
    adv = ctypes.WinDLL("Advapi32.dll")
    entries = ctypes.POINTER(ctypes.POINTER(Credential))()
    count = wintypes.DWORD()
    if not adv.CredEnumerateW("Supabase*", 0, ctypes.byref(count), ctypes.byref(entries)):
        raise RuntimeError("cli_credential_unavailable")
    try:
        if count.value != 1:
            raise RuntimeError("cli_credential_ambiguous")
        row = entries[0].contents
        blob = ctypes.string_at(row.Blob, row.BlobSize)
        token = blob.decode("utf-16-le" if b"\x00" in blob else "utf-8").strip("\x00")
        if not re.fullmatch(r"sbp_[A-Za-z0-9_\-]+", token):
            raise RuntimeError("cli_credential_format_unexpected")
        return token
    finally:
        adv.CredFree(entries)

def main():
    query = sys.stdin.read()
    if not query or len(query) > 100000:
        raise RuntimeError("test_query_invalid")
    req = urllib.request.Request(
        "https://api.supabase.com/v1/projects/mokxyyullfhkfalopbzd/database/query",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": "Bearer " + credential(), "Content-Type": "application/json",
                 "User-Agent": "FitMetZorge-Staging-Security-Test/6D0", "Accept": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            rows = json.loads(response.read())
        print(json.dumps({"ok": True, "rows": rows, "error": ""}))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        match = re.search(r"invitation_used_expired_or_revoked|workspace_conflict_reload_required|deadlock_detected|statement_timeout", body)
        print(json.dumps({"ok": False, "rows": [], "status": error.code,
                          "error": match.group(0) if match else "management_query_rejected"}))

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        safe = str(error) if isinstance(error, RuntimeError) else "management_transport_unavailable"
        print(json.dumps({"ok": False, "rows": [], "error": safe}))
