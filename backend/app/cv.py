"""Computer-vision core: preprocessing, face detection, ArcFace embeddings, categorisation."""
import io
import cv2
import numpy as np
from PIL import Image, ImageOps
from .config import MAX_SIDE, DET_SIZE, MIN_FACE_RATIO

_app = None


def _model():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=-1, det_size=(DET_SIZE, DET_SIZE))
    return _app


def load_image(data: bytes) -> Image.Image:
    """Decode, fix EXIF rotation, downscale."""
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im).convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    return im


def to_bgr(im: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def enhance(bgr: np.ndarray) -> np.ndarray:
    """CLAHE on the L channel: helps dim, uneven event lighting without shifting colour."""
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def blur_score(bgr: np.ndarray) -> float:
    """Variance of Laplacian: low value = blurry."""
    return float(cv2.Laplacian(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())


def extract_faces(bgr: np.ndarray, use_clahe: bool = True, min_score: float = 0.6):
    """Returns list of dicts: emb (512,), bbox (x1,y1,x2,y2), score. Largest face first."""
    img = enhance(bgr) if use_clahe else bgr
    out = []
    for f in _model().get(img):
        if f.det_score < min_score:
            continue
        out.append({
            "emb": f.normed_embedding.astype(np.float32),
            "bbox": [int(v) for v in f.bbox],
            "score": float(f.det_score),
        })
    out.sort(key=lambda d: area(d["bbox"]), reverse=True)
    return out


def area(b) -> int:
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def user_embedding(selfies_bgr: list, use_clahe: bool = True):
    """Average embedding over selfies (largest face in each). None if no face found."""
    embs = []
    for im in selfies_bgr:
        faces = extract_faces(im, use_clahe)
        if faces:
            embs.append(faces[0]["emb"])
    if not embs:
        return None
    m = np.mean(embs, axis=0)
    return (m / np.linalg.norm(m)).astype(np.float32)


CATEGORIES = ["only_you", "with_one_person", "small_group", "group_photo"]


def categorize(all_bboxes: list, user_bbox) -> str:
    """Count only faces comparable in size to the user's, so background crowd doesn't inflate the count."""
    ua = area(user_bbox)
    n = sum(1 for b in all_bboxes if area(b) >= MIN_FACE_RATIO * ua)
    n = max(n, 1)
    if n == 1:
        return "only_you"
    if n == 2:
        return "with_one_person"
    if n <= 6:
        return "small_group"
    return "group_photo"
