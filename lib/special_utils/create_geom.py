import adsk.core, adsk.fusion, adsk.cam, traceback

from geometry import Transformation, Point, Quaternion
from itertools import chain
from .fusion_tools import full_obj_collection
import numpy as np

def create_matrix3d(self: Transformation):
    matr =  adsk.core.Matrix3D.create()
    matd = (self * 0.1).to_matrix()[0,:,:].T.tolist()

    if matr.setWithArray(list(chain(*matd))):
        return matr
    else:
        raise Exception("couldnt set the transformation")


def parse_matrix3d(mat3d) -> Transformation:
    mat=np.array(mat3d.asArray())
    rotmat=np.stack([mat[:3], mat[4:7], mat[9:12]], axis=1).T
    return Transformation(
        Point(mat[4], mat[8], mat[12]),
        Quaternion.from_rotation_matrix(rotmat)
    )

def create_sketch_point(self: Point):
    return adsk.core.Point3D.create(*(self * 0.1).data[0,:].tolist())


def create_sketch_points(self: Point):
    return full_obj_collection([create_sketch_point(p) for p in self])