import json, os
from pathlib import Path
from app.db import SessionLocal
from app.models import Event
from app.config import SERVICE_ACCOUNT_FILE

db = SessionLocal()
for e in db.query(Event):
    print(f"\n[{e.id}] {e.name}  source={e.source}  folder={e.folder!r}")
    if e.source == "local":
        p = Path(e.folder)
        print("  exists:", p.exists(), " is_dir:", p.is_dir())
        files = [x for x in p.rglob("*") if x.is_file()] if p.exists() else []
        print("  files found:", len(files), [x.name for x in files[:5]])
    else:
        print("  service account file exists:", os.path.exists(SERVICE_ACCOUNT_FILE))
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            continue
        print("  folder must be shared with:", json.load(open(SERVICE_ACCOUNT_FILE))["client_email"])
        from app import drive
        svc = drive.service()
        try:
            meta = svc.files().get(fileId=e.folder, fields="id,name,mimeType", supportsAllDrives=True).execute()
            print("  folder visible:", meta)
        except Exception as ex:
            print("  CANNOT SEE FOLDER:", ex)
            continue
        print("  images found:", len(drive.list_images(svc, e.folder)))