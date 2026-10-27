"""Evaluate EGO's non-clamped B-spline directly from its transmitted knots."""
import numpy as np


def sample_spline(control_points, knots, degree, count=120):
    points = np.asarray(control_points, dtype=float)
    knots = np.asarray(knots, dtype=float)
    degree = int(degree)
    if (points.ndim != 2 or points.shape[1] != 3 or degree < 1 or
            len(points) <= degree or len(knots) != len(points) + degree + 1 or
            not np.isfinite(points).all() or not np.isfinite(knots).all() or
            np.any(np.diff(knots) < 0) or knots[degree] >= knots[len(points)]):
        raise ValueError("Invalid B-spline control points, degree, or knot vector")
    times = np.linspace(knots[degree], knots[len(points)], max(2, count))
    output = []
    for t in times:
        k = min(len(points)-1, max(degree, int(np.searchsorted(knots, t, side="right"))-1))
        work = points[k-degree:k+1].copy()
        for r in range(1, degree+1):
            for j in range(degree, r-1, -1):
                left, right = knots[k-degree+j], knots[k+1+j-r]
                alpha = (t-left)/(right-left) if right > left else 0.0
                work[j] = (1-alpha)*work[j-1] + alpha*work[j]
        output.append(work[degree])
    return times - knots[degree], np.array(output)
