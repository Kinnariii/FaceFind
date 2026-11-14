# FaceFind

Log in with a selfie, pick an event, and get every photo you appear in, sorted into
**Only you / With one person / Small group / Group photos**.

Stack: FastAPI + SQLite, InsightFace (RetinaFace detector + ArcFace embeddings), Google Drive API, React (Vite).

## 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then edit SECRET_KEY
uvicorn app.main:app --reload --port 8000
```
First run downloads the `buffalo_l` model (~300 MB) into `~/.insightface`.
If `pip install insightface` fails on Windows, install "Microsoft C++ Build Tools" first.

## 2. Frontend

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173 (proxies /api to port 8000)
```

## 3. First run

1. Register at `/register`. **The first account becomes admin.**
2. Open *Manage events* and add an event.
   - **Quick test (no Google setup):** source = "Folder on this server", path = a folder of photos on your machine.
   - **Drive:** see below.
3. Click *Process photos* and watch the progress bar. Then open the event from *Events*.
4. Register a second account to test that other people get their own photos.

## Google Drive setup (service account)

1. Google Cloud Console → create a project → enable **Google Drive API**.
2. IAM & Admin → Service Accounts → create one → Keys → Add key → JSON.
3. Save the file as `backend/service_account.json` (it is git-ignored).
4. In Drive, **share the event folder with the service account's email** (Viewer is enough).
5. Folder ID = the last part of the folder URL: `drive.google.com/drive/folders/<THIS_PART>`.

## Tuning and evaluation

- `MATCH_THRESHOLD` (default 0.40) is the cosine-similarity cut-off. Lower = more recall, more false matches.
- `USE_CLAHE=1` applies contrast enhancement before detection. Use `evaluate.py` to measure whether it helps.

```bash
cd backend
# eval/selfies/*.jpg, eval/photos/*.jpg, eval/labels.csv  (filename,present)
python evaluate.py --dir eval
```
Produces precision/recall/F1 vs threshold plots for CLAHE on/off. Put these in your report,
and set `MATCH_THRESHOLD` to the best-F1 value.

## How it works

| Step | Where | What |
|---|---|---|
| Preprocess | `cv.load_image`, `cv.enhance` | EXIF fix, resize to 1600px, CLAHE on L channel |
| Detect + align + embed | `cv.extract_faces` | RetinaFace + ArcFace -> 512-d unit vectors |
| Index | `indexer.py` | Per photo: store resized copy, thumbnail, every face's embedding and box |
| Match | `main.match_user` | Cosine similarity of user vector vs all faces in the event |
| Categorise | `cv.categorize` | Count faces at least 25% the area of the user's face (ignores background crowd) |

## Known limits (mention in your report)
- Any logged-in user can view photos of an event by id; access control is per event, not per person.
- Indexing is single-threaded, ~0.5-2 s per photo on CPU.
- Heavy occlusion, sunglasses, extreme angles and very small faces reduce recall.

## Ideas to extend
Face clustering (DBSCAN) for "browse by person", blur filtering via `cv.blur_score`, duplicate removal with perceptual hashing, Login with Google, FAISS for 100k+ faces.
