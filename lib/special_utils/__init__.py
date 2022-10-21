from geometry import Point, Transformation, Quaternion


from .create_geom import *


def tag_methods():
    
    Transformation.fusion_matrix3d = create_matrix3d
    Point.fusion_sketch_point = create_sketch_point
    Point.fusion_sketch_points = create_sketch_points

    Transformation.from_matrix3d = staticmethod(parse_matrix3d)
    
    #Rib.parse_parameters = staticmethod(parse_rib_parms)
#
    #Panel.parse_fusion_parms = staticmethod(parse_panel_parms)
    #Panel.dump_fusion_parms = dump_panel_parameters