from matplotlib.font_manager import findfont, FontProperties
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from .img import img_to_ansi, resize_image

class Layer:
    def __init__(self):
        self._transform = np.eye(3)

    def set_transform(self, matrix):
        m = np.asarray(matrix)
        if m.shape == (2, 3):
            self._transform = np.vstack([m, [0, 0, 1]])
        elif m.shape == (3, 3):
            self._transform = m
        else:
            raise ValueError("Transform must be 2x3 or 3x3 matrix.")

    def render_layer(self, arr):
        h, w, _ = arr.shape
        ys, xs = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
        us = (xs + 0.5) / w
        vs = (ys + 0.5) / h
        ones = np.ones_like(us)
        uv1 = np.stack([us, vs, ones], axis=-1)
        inv = np.linalg.inv(self._transform)
        mapped = uv1 @ inv.T
        mapped_u = mapped[..., 0]
        mapped_v = mapped[..., 1]
        # Instead of discarding, pass to self.sample:
        self.render_uv(arr, mapped_u, mapped_v)

    def render_uv(self, arr, u, v):
        # By default, call sample per-pixel (slow, but always correct).
        h, w, _ = arr.shape
        for y in range(h):
            for x in range(w):
                arr[y, x] = self.sample(u[y, x], v[y, x], arr)
        # Subclasses can override render_uv for vectorized/fast implementations.

    def sample(self, u, v, arr):
        """Subclasses MUST override: sample at normalized (u, v) in [0,1]."""
        raise NotImplementedError

class BackgroundLayer(Layer):
    def __init__(self, color=(0,0,0,255)):
        super().__init__()
        self.color = np.array(color, dtype=np.uint8)
    def sample(self, u, v, arr):
        return self.color

class ImageLayer(Layer):
    def __init__(self, img):
        super().__init__()
        self.img = np.array(img.convert("RGBA"))
        self.h, self.w = self.img.shape[:2]
    def render_uv(self, arr, u, v):
        # u, v are arrays of shape (H, W) with floats in [0, 1]
        iy = np.clip((v * self.h).astype(int), 0, self.h - 1)
        ix = np.clip((u * self.w).astype(int), 0, self.w - 1)
        arr[:] = self.img[iy, ix]

class Compositor:
    def __init__(self, width, height, layers):
        self.width = width
        self.height = height
        self.layers = layers

    def render(self):
        arr = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        for layer in self.layers:
            tmp = np.zeros_like(arr)
            layer.render_layer(tmp)
            # "Over" alpha compositing
            src_rgb = tmp[..., :3].astype(np.float32)
            src_a = tmp[..., 3:4].astype(np.float32) / 255
            dst_rgb = arr[..., :3].astype(np.float32)
            dst_a = arr[..., 3:4].astype(np.float32) / 255
            out_a = src_a + dst_a * (1 - src_a)
            out_rgb = (src_rgb * src_a + dst_rgb * dst_a * (1 - src_a)) / np.clip(out_a, 1e-8, 1)
            arr[..., :3] = out_rgb.astype(np.uint8)
            arr[..., 3] = (out_a * 255).astype(np.uint8)[..., 0]
        return arr

def Rotate(theta, cx=0.5, cy=0.5):
    # Rotate theta radians about (cx, cy)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    T1 = np.array([[1, 0, -cx],
                   [0, 1, -cy],
                   [0, 0,  1]], dtype=float)
    R = np.array([[cos_t, -sin_t, 0],
                  [sin_t,  cos_t, 0],
                  [0,      0,     1]], dtype=float)
    T2 = np.array([[1, 0, cx],
                   [0, 1, cy],
                   [0, 0, 1]], dtype=float)
    return T1 @ R @ T2

img_layer = ImageLayer(img=Image.open("./src/img/google.png"))
img_layer.set_transform(Rotate(np.pi / 4, cx=0.5, cy=0.5))
bg_layer = BackgroundLayer(color=(255, 255, 255, 255))
comp = Compositor(
    80,
    24,
    [
        bg_layer,
        img_layer,
    ]
)

result = comp.render()
result_img = Image.fromarray(result, 'RGBA')
result_img = resize_image(result_img, 24)
print("\n".join(img_to_ansi(result_img)))

