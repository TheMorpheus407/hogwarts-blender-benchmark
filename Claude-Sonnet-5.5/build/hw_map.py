"""Plan-view contour map renderer (numpy -> PNG through bpy.data.images).  Planning aid only."""
import numpy as np
import bpy
import hw_terrain as T
import hw_layout as L


def save_map(path, x0, x1, y0, y1, step=1.0, scale=3, polys=(), lines=(), points=(), res=1.0, contour=4.0):
    xs = np.arange(x0, x1 + step, step)
    ys = np.arange(y0, y1 + step, step)
    X, Y = np.meshgrid(xs, ys)
    z, s, amount, inside = T.height(X, Y, res)
    img = np.zeros(z.shape + (3,), dtype=np.float32)
    # hypsometric tint
    zn = np.clip((z + 10.0) / 80.0, 0, 1)
    img[..., 0] = 0.25 + 0.55 * zn
    img[..., 1] = 0.40 + 0.40 * zn
    img[..., 2] = 0.30 + 0.35 * zn
    water = z < 0.0
    img[water] = np.array([0.12, 0.25, 0.42])
    # shading
    gy, gx = np.gradient(z, step)
    sh = np.clip(0.75 + 0.35 * (-gx * 0.6 + gy * 0.4) / 2.0, 0.4, 1.3)
    img *= sh[..., None]
    # contours
    k = np.floor(z / contour)
    edge = (k != np.roll(k, 1, 0)) | (k != np.roll(k, 1, 1))
    major = np.floor(z / (contour * 5))
    edge_m = (major != np.roll(major, 1, 0)) | (major != np.roll(major, 1, 1))
    img[edge] *= 0.55
    img[edge_m] = np.array([0.05, 0.05, 0.05])

    def to_px(px, py):
        return (np.asarray(px) - x0) / step, (np.asarray(py) - y0) / step

    def draw_line(pts, col, closed=False):
        pts = np.asarray(pts, float)
        if closed:
            pts = np.vstack([pts, pts[:1]])
        for a, b in zip(pts[:-1], pts[1:]):
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) / step * 2) + 2
            t = np.linspace(0, 1, n)
            px = a[0] + (b[0] - a[0]) * t
            py = a[1] + (b[1] - a[1]) * t
            ix, iy = to_px(px, py)
            m = (ix >= 0) & (ix < img.shape[1]) & (iy >= 0) & (iy < img.shape[0])
            img[iy[m].astype(int), ix[m].astype(int)] = col
    for poly, col in polys:
        draw_line(poly, col, closed=True)
    for ln, col in lines:
        draw_line(ln, col)
    for (px, py, col) in points:
        ix, iy = to_px(px, py)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                jx, jy = int(ix) + dx, int(iy) + dy
                if 0 <= jx < img.shape[1] and 0 <= jy < img.shape[0]:
                    img[jy, jx] = col
    img = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
    h, w = img.shape[:2]
    im = bpy.data.images.new('tmp_map', w, h, alpha=False)
    rgba = np.concatenate([np.clip(img, 0, 1), np.ones((h, w, 1), np.float32)], axis=2)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)
    return dict(shape=(h, w), zmin=float(z.min()), zmax=float(z.max()))
