"""Preinflate 2D column cells once instead of dilating every Z sample in EGO."""
import math
import numpy as np
from scipy.ndimage import binary_dilation

def inflate_columns(cells,res,radius,circular):
    cells=np.asarray(cells,dtype=int)
    if not len(cells):return np.empty((0,2),int)
    steps=int(math.ceil(radius/res));lo=cells.min(0)-steps;hi=cells.max(0)+steps
    mask=np.zeros(tuple(hi-lo+1),bool);mask[tuple((cells-lo).T)]=True
    x,y=np.mgrid[-steps:steps+1,-steps:steps+1]
    structure=np.hypot(x,y)*res<=radius+math.sqrt(.5)*res if circular else np.ones(x.shape,bool)
    inflated=binary_dilation(mask,structure=structure)
    return np.argwhere(inflated)+lo
