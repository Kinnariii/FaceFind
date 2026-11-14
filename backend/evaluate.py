"""
Evaluation for your report: precision / recall / F1 vs. similarity threshold, with and without CLAHE.

Folder layout:
  eval/selfies/       1-3 images of the test person
  eval/photos/        test event photos
  eval/labels.csv     filename,present      (present = 1 if the person is in the photo, else 0)

Run:  python evaluate.py --dir eval
Output: eval/results.png and eval/results.csv
"""
import argparse
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app import cv


def best_sim(bgr, user_emb, clahe):
    faces = cv.extract_faces(bgr, clahe)
    return max((float(user_emb @ f["emb"]) for f in faces), default=-1.0)


def read(path):
    with open(path, "rb") as fh:
        return cv.to_bgr(cv.load_image(fh.read()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="eval")
    a = ap.parse_args()

    labels = {r["filename"]: int(r["present"]) for r in csv.DictReader(open(os.path.join(a.dir, "labels.csv")))}
    selfies = [read(os.path.join(a.dir, "selfies", f)) for f in sorted(os.listdir(os.path.join(a.dir, "selfies")))]
    photos = {f: read(os.path.join(a.dir, "photos", f)) for f in labels}
    y = np.array([labels[f] for f in photos])
    thresholds = np.arange(0.20, 0.71, 0.025)

    plt.figure(figsize=(9, 4))
    rows = [["clahe", "threshold", "precision", "recall", "f1"]]
    for clahe in (False, True):
        emb = cv.user_embedding(selfies, clahe)
        sims = np.array([best_sim(im, emb, clahe) for im in photos.values()])
        P, R, F = [], [], []
        for t in thresholds:
            pred = sims >= t
            tp = int((pred & (y == 1)).sum())
            fp = int((pred & (y == 0)).sum())
            fn = int((~pred & (y == 1)).sum())
            p = tp / (tp + fp) if tp + fp else 1.0
            r = tp / (tp + fn) if tp + fn else 0.0
            f = 2 * p * r / (p + r) if p + r else 0.0
            P.append(p); R.append(r); F.append(f)
            rows.append([clahe, round(float(t), 3), round(p, 3), round(r, 3), round(f, 3)])
        i = int(np.argmax(F))
        print(f"CLAHE={clahe}: best F1={F[i]:.3f} at threshold {thresholds[i]:.3f} (P={P[i]:.3f}, R={R[i]:.3f})")
        plt.subplot(1, 2, 1 + int(clahe))
        plt.plot(thresholds, P, label="precision")
        plt.plot(thresholds, R, label="recall")
        plt.plot(thresholds, F, label="F1", linestyle="--")
        plt.title(f"CLAHE {'on' if clahe else 'off'}")
        plt.xlabel("cosine threshold")
        plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(a.dir, "results.png"), dpi=150)
    csv.writer(open(os.path.join(a.dir, "results.csv"), "w", newline="")).writerows(rows)
    print("Saved results.png and results.csv")


if __name__ == "__main__":
    main()
