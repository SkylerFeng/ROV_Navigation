"""Explicit known pool collider prior shared by both fixed-depth maps.
Never supplies target truth or marks unobserved space free.
"""
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def load_static_xy(config):
    path=config.get('static_collision_prior')
    if not path:return np.empty((0,2))
    with np.load(ROOT/path,allow_pickle=False) as data:
        xy=np.asarray(data['xy'],float)
        if xy.ndim!=2 or xy.shape[1]!=2 or not np.isfinite(xy).all():raise ValueError('Invalid static collision prior')
        if not np.isclose(float(data['res']),.1):raise ValueError('Static prior must use 0.1 m cells')
    return xy[(np.abs(xy[:,0])<8)&(np.abs(xy[:,1])<6)]
def seed_grid(grid,xy):
    # EGO cloudCallback uses a square XY dilation, not a circular one.
    if len(xy):grid.inflation_metric="chessboard"
    cells=np.floor((xy-grid.origin)/grid.res).astype(int)
    cells=cells[(cells>=0).all(1)&(cells<grid.shape).all(1)]
    if len(cells):grid.occupied[tuple(cells.T)]=True
    grid.free &= ~grid.occupied
    grid._safe=None
