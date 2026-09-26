"""Mejora y recorte de la foto de autor para la web personal.

Pipeline reproducible:
  1. Mejora: denoise suave, balance gris-mundo atenuado, CLAHE ligero,
     unsharp sutil restringido a la zona de la cara.
  2. Upscale 2x con Lanczos.
  3. Fondo fuera con U2Net (onnx) + refinado del alpha: erosion del halo,
     borde desvanecido y limpieza de islas.
  4. Recorte a cabeza y torso (~68% superior del sujeto) y export WebP
     RGBA <= 250 KB.

Uso:
  /data/users/julio/.conda/envs/deep/bin/python enhance_photo.py
"""

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

SRC = "/tmp/opencode/old_author.jpg"
MODEL = "/tmp/opencode/models/u2net.onnx"
OUT = Path("/data/users/julio/Notes/01-Projects/personal-web/site/public/assets/img/julio-cutout.webp")
PREVIEW = Path("/tmp/opencode/enhanced-preview.png")
PREVIEW_BG = (13, 11, 26)  # #0d0b1a en RGB
MAX_KB = 250

# ---------------------------------------------------------------- mejora


def gray_world(img: np.ndarray, strength: float = 0.5) -> np.ndarray:
    """Balance de blancos gris-mundo, mezclado al `strength` para no virar la piel."""
    b, g, r = cv2.split(img.astype(np.float32))
    mean = (b.mean() + g.mean() + r.mean()) / 3.0
    balanced = cv2.merge([
        np.clip(b * mean / max(b.mean(), 1e-6), 0, 255),
        np.clip(g * mean / max(g.mean(), 1e-6), 0, 255),
        np.clip(r * mean / max(r.mean(), 1e-6), 0, 255),
    ])
    return cv2.addWeighted(balanced, strength, img.astype(np.float32), 1 - strength, 0).astype(np.uint8)


def enhance(img: np.ndarray) -> np.ndarray:
    # Denoise suave: h bajo para no plastificar la piel.
    out = cv2.fastNlMeansDenoisingColored(img, None, h=3, hColor=3, templateWindowSize=7, searchWindowSize=21)

    out = gray_world(out, strength=0.4)

    # Contraste local ligero solo en luminancia.
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(8, 8))
    out = cv2.cvtColor(cv2.merge([clahe.apply(l), a, b]), cv2.COLOR_LAB2BGR)

    # Unsharp sutil restringido al tercio superior (cara/ojos), con fundido.
    blur = cv2.GaussianBlur(out, (0, 0), 2.0)
    sharp = cv2.addWeighted(out, 1.35, blur, -0.35, 0)
    h = out.shape[0]
    weight = np.zeros(out.shape[:2], np.float32)
    weight[: int(h * 0.45)] = 1.0
    weight = cv2.GaussianBlur(weight, (0, 0), h * 0.06)[..., None]
    return (sharp.astype(np.float32) * weight + out.astype(np.float32) * (1 - weight)).astype(np.uint8)


# ---------------------------------------------------------------- U2Net


def u2net_alpha(img: np.ndarray) -> np.ndarray:
    """Mascara de salencia U2Net en [0,1] al tamano de `img`."""
    h, w = img.shape[:2]
    size = 320
    tmp = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    tmp = cv2.cvtColor(tmp, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    tmp = (tmp - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    tmp = np.transpose(tmp, (2, 0, 1))[np.newaxis].astype(np.float32)

    session = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    pred = session.run(None, {session.get_inputs()[0].name: tmp})[0][0, 0]
    pred = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
    return cv2.resize(pred, (w, h), interpolation=cv2.INTER_LINEAR)


def refine_alpha(alpha: np.ndarray) -> np.ndarray:
    """Erosiona el halo del borde y desvanece: binariza, quita islas, erosiona y suaviza."""
    hard = (alpha > 0.5).astype(np.uint8)

    # Conservar solo la componente conexa mayor (el sujeto).
    n, labels, stats, _ = cv2.connectedComponentsWithStats(hard, 8)
    if n > 1:
        hard = (labels == (1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    hard = cv2.morphologyEx(hard, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    # Erosion: mete el borde unos px hacia dentro para tragarse el halo del fondo.
    eroded = cv2.erode(hard, np.ones((5, 5), np.uint8), iterations=1).astype(np.float32)
    soft = cv2.GaussianBlur(eroded, (0, 0), 2.5)
    # Curva suave para que el borde caiga rapido pero sin escalon.
    return np.clip(soft, 0, 1) ** 1.5


# ---------------------------------------------------------------- recorte y export


def crop_head_torso(rgba: np.ndarray) -> np.ndarray:
    """Recorta al bbox del sujeto, se queda con el ~68% superior y da margen lateral."""
    alpha = rgba[:, :, 3]
    ys, xs = np.where(alpha > 16)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()

    y_cut = y0 + int((y1 - y0 + 1) * 0.68)
    band = alpha[y0:y_cut]
    xs_band = np.where(band.max(axis=0) > 16)[0]
    x0, x1 = xs_band.min(), xs_band.max()

    mx = int((x1 - x0) * 0.04)
    my = int((y_cut - y0) * 0.04)
    x0 = max(0, x0 - mx)
    x1 = min(rgba.shape[1] - 1, x1 + mx)
    y0 = max(0, y0 - my)
    return rgba[y0:y_cut, x0 : x1 + 1]


def save_webp(rgba: np.ndarray, path: Path, max_kb: int) -> int:
    im = Image.fromarray(rgba, "RGBA")
    for q in (90, 85, 80, 75, 70, 60, 50):
        im.save(path, "WEBP", quality=q, method=6)
        kb = path.stat().st_size // 1024
        if kb <= max_kb:
            return kb
    return kb


def main() -> None:
    img = cv2.imread(SRC)
    img = enhance(img)
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)

    alpha = refine_alpha(u2net_alpha(img))
    rgba = np.dstack([cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (alpha * 255).astype(np.uint8)])
    rgba = crop_head_torso(rgba)

    kb = save_webp(rgba, OUT, MAX_KB)
    print(f"cutout {OUT} {rgba.shape[1]}x{rgba.shape[0]} {kb} KB")

    a = rgba[:, :, 3:4].astype(np.float32) / 255.0
    bg = np.zeros_like(rgba[:, :, :3], np.float32)
    bg[:] = PREVIEW_BG
    comp = (rgba[:, :, :3].astype(np.float32) * a + bg * (1 - a)).astype(np.uint8)
    Image.fromarray(comp, "RGB").save(PREVIEW)
    print(f"preview {PREVIEW}")


if __name__ == "__main__":
    main()
