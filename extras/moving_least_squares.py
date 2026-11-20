"""Pure NumPy replacement for CHROMAS's Cython module `moving_least_squares`.

Implements the similarity variant of moving least squares image deformation
(Schaefer et al. 2006) with the same signature and behaviour as the bundled
Cython extension: similarity(p, q, v, alpha) -> (len(v), 2) float32.
Slower than the compiled version, but needs no C compiler.
"""
import numpy as np

_EPS = float(np.finfo(np.float32).eps)


def similarity(p, q, v, alpha=1.0, chunk=2048):
    p = np.asarray(p, dtype=np.float32)
    q = np.asarray(q, dtype=np.float32)
    v = np.asarray(v, dtype=np.float32)
    assert p.ndim == 2 and p.shape[1] == 2
    assert q.shape == p.shape
    assert v.ndim == 2 and v.shape[1] == 2
    p64, q64 = p.astype(np.float64), q.astype(np.float64)
    out = np.empty((v.shape[0], 2), dtype=np.float32)
    for s in range(0, v.shape[0], chunk):
        vv = v[s:s + chunk].astype(np.float64)               # (m, 2)
        d = np.sqrt(((vv[:, None, :] - p64[None, :, :]) ** 2).sum(-1))  # (m, n)
        near = d <= _EPS
        hit = near.any(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = np.where(near, 0.0, d ** (-alpha))            # (m, n)
            ws = w.sum(axis=1, keepdims=True)
            p_star = (w @ p64) / ws                           # (m, 2)
            q_star = (w @ q64) / ws
            p_hat = p64[None, :, :] - p_star[:, None, :]      # (m, n, 2)
            q_hat = q64[None, :, :] - q_star[:, None, :]
            f0 = (w * (q_hat[..., 0] * p_hat[..., 0] + q_hat[..., 1] * p_hat[..., 1])).sum(1)
            f1 = (w * (q_hat[..., 0] * p_hat[..., 1] - q_hat[..., 1] * p_hat[..., 0])).sum(1)
            mus = (w * (p_hat ** 2).sum(-1)).sum(1)
            vh = vv - p_star
            fx = (f0 * vh[:, 0] + f1 * vh[:, 1]) / mus + q_star[:, 0]
            fy = (f0 * vh[:, 1] - f1 * vh[:, 0]) / mus + q_star[:, 1]
        res = np.stack([fx, fy], axis=1)
        if hit.any():                                         # v coincides with a control point
            res[hit] = q64[near[hit].argmax(axis=1)]
        out[s:s + chunk] = res.astype(np.float32)
    return out
