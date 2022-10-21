#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback
import math


def face_distance(self, other):
    x = self.centroid.x - other.centroid.x
    y = self.centroid.y - other.centroid.y
    z = self.centroid.z - other.centroid.z
    return math.sqrt((self.geometry.normal.x * x)**2 + (self.geometry.normal.y * y)**2 + (self.geometry.normal.z * z)**2)


def get_nesting_info(body):
    biggest_face = None
    second_biggest_face = None

    for f in body.faces:
        if f.geometry.__class__.__name__ == "Plane":
            if biggest_face is not None:
                if f.area > biggest_face.area:
                    second_biggest_face = biggest_face
                    biggest_face = f
                elif second_biggest_face is None:
                    second_biggest_face = f
                elif f.area > second_biggest_face.area:
                    second_biggest_face = f
            else:
                biggest_face = f

    thickness = face_distance(biggest_face, second_biggest_face) * 10
    
    print(f"thickness: {thickness}, area: {biggest_face.area}")

    return biggest_face, round(thickness, 0)



def sort_bodies(parent, bodies):

    thicknesses = {}

    # get the bodies and thicknesses
    for b in bodies:
        biggest_face, thickness = get_nesting_info(b)
        mat_description = f"{b.material.name} {thickness}"
        try:
            thicknesses[mat_description].append((b, biggest_face))
        except KeyError:
            thicknesses[mat_description] = [(b, biggest_face)]
    

    #group the bodies into components
    for grp, bodies in thicknesses.items():
        new_occ = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        new_occ.component.name = grp
        nbs = [b.moveToComponent(new_occ) for b, f in bodies]
#        faces = [get_nesting_info(b)[0] for b in nbs]               
        #app.userInterface.activeSelections.clear()
        #for f in faces:
        #    app.userInterface.activeSelections.add(f)



def get_big_faces(select_input):
    return [get_nesting_info(select_input.selection(i).entity)[0] for i in range(select_input.selectionCount)]

