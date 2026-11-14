"""Google Drive access through a service account. Share the event folder with the service account's email."""
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from .config import SERVICE_ACCOUNT_FILE


def service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_images(svc, folder_id: str) -> list:
    """All images under folder_id, including sub-folders."""
    out, stack = [], [folder_id]
    while stack:
        fid, page = stack.pop(), None
        while True:
            r = svc.files().list(
                q=f"'{fid}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000, pageToken=page,
                supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            for f in r.get("files", []):
                if f["mimeType"] == "application/vnd.google-apps.folder":
                    stack.append(f["id"])
                elif f["mimeType"].startswith("image/"):
                    out.append(f)
            page = r.get("nextPageToken")
            if not page:
                break
    return out


def download(svc, file_id: str) -> bytes:
    req = svc.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()
