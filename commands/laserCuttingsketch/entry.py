import json
import adsk.core
import os
from ...lib import fusion360utils as futil
from ... import config
from ...lib.nesting import sort_bodies, get_big_faces
from ...lib.special_utils.fusion_tools import Sketch, Edge, full_obj_collection, SketchCurve
from geometry import Point, P0, PX, PY, PZ
app = adsk.core.Application.get()
ui = app.userInterface

# TODO ********************* Change these names *********************
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_laser_cutting'
CMD_NAME = 'Laser Cutting'
CMD_Description = 'create a sketch for laser cutting'
IS_PROMOTED = False

# Using "global" variables by referencing values from /config.py
PALETTE_ID = config.sample_palette_id

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Event handler that is called when the user clicks the command button in the UI.
# To have a dialog, you create the desired command inputs here. If you don't need
# a dialog, don't create any inputs and the execute event will be immediately fired.
# You also need to connect to any command related events here.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # TODO Create the event handlers you will need for this instance of the command
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    # Create the user interface for your command by adding different inputs to the CommandInputs object
    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO ******************************** Define your UI Here ********************************
     
    select_body_input = inputs.addSelectionInput('select_body_input', 'Bodies', 'Select bodies to cut')
    select_body_input.addSelectionFilter("SolidBodies")
    select_body_input.setSelectionLimits(0)

    select_plane_input = inputs.addSelectionInput('select_plane_input', 'Sketch Plane', 'Select plane for sketch')
    select_plane_input.addSelectionFilter("ConstructionPlanes")

    tab_space_input = inputs.addFloatSpinnerCommandInput('tab_space_input', "tab spacing", "mm", 1, 200, 5, 70)
    tap_width_input = inputs.addFloatSpinnerCommandInput('tap_width_input', "tab spacing", "mm", 0.5, 5, 0.5, 1)
    kerf_width_input = inputs.addFloatSpinnerCommandInput('kerf_width_input', "kerf width", "mm", -0.5, 0.5, 0.01, 0.06)


# This function will be called when the user hits the OK button in the command dialog
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug
    futil.log(f'{CMD_NAME} Command Execute Event')

    inputs = args.command.commandInputs

    # TODO ******************************** Your code here ********************************
    
    # Get a reference to your command's inputs
    select_body_input: adsk.core.SelectionCommandInput = inputs.itemById('select_body_input')
    select_plane_input: adsk.core.SelectionCommandInput = inputs.itemById('select_plane_input')
    tab_space_input: adsk.core.FloatSpinnerCommandInput = inputs.itemById('tab_space_input')
    tap_width_input: adsk.core.FloatSpinnerCommandInput = inputs.itemById('tap_width_input')
    kerf_width_input: adsk.core.FloatSpinnerCommandInput = inputs.itemById('kerf_width_input')


    faces = get_big_faces(select_body_input)

    sketch_plane = select_plane_input.selection(0).entity
    

    osketch = Sketch.get_or_create(app.activeDocument.design.activeComponent, "laser_sketch", sketch_plane)

    length = 0
    
    for i, face in enumerate(faces):
        print(f"Face {i} of {len(faces)}")
        curves = []
        directions = []
        for ploop in face.loops:
            ### Project and Offset Edges
            p, p2 = ploop.boundingBox.maxPoint, ploop.boundingBox.minPoint
            ps = Point([Point(p.x, p.y, p.z), Point(p2.x, p2.y, p2.z)]).mean()
            d = adsk.core.Point3D.create(**ps.to_dict())

            edges = full_obj_collection([edge for edge in ploop.edges])

            projected_curves = osketch.project(edges)# [osketch.project(edge)[0] for edge in ploop.edges]
            
            offset_curves = osketch.offset(
                projected_curves, #full_obj_collection(projected_curves),
                osketch.modelToSketchSpace(d),
                kerf_width_input.value if not ploop.isOuter else - kerf_width_input.value
            )
            
            for curve in projected_curves:
                curve.deleteMe()

            for curve in offset_curves:
                for _ in range(curve.geometricConstraints.count):
                    if curve.geometricConstraints[0].isDeletable:
                        curve.geometricConstraints[0].deleteMe()
            

            ### Create cutting tabs

            length = 0
            longest = None
            ntabs = 0
            for curve in offset_curves:
                length += curve.length * 10
                this_curves_tabs = []
                poff = 10
                while length > ntabs * tab_space_input.value * 10:
                    #print(f"length={length}, ntabs={ntabs}")
                    if curve.length *10 > poff+10:

                        ps = Edge.p3d_at_l(curve.geometry, 0.1*poff-tap_width_input.value)
                        pe = Edge.p3d_at_l(curve.geometry, 0.1*poff)
                        
                        this_curves_tabs += [
                            Edge.p3d_at_l(curve.geometry, 0.1*poff-tap_width_input.value),
                            Edge.p3d_at_l(curve.geometry, 0.1*poff)
                        ]
                        ntabs +=1
                        poff += tab_space_input.value * 10
                    else:
                        break
                if len(this_curves_tabs) > 0:
                    cut_curves = SketchCurve.split_at_p3ds(curve, this_curves_tabs)
                    SketchCurve.delete_alternate(cut_curves)
                      
                if ntabs == 0:
                    if longest is None:
                        longest = curve
                    else:
                        if curve.length > longest.length:
                            longest = curve

            if ntabs == 0:
                if longest.length > tap_width_input.value:
                    pm = Edge.p3d_at_r(longest.geometry, 0.5)
                    tabs = [
                        Edge.offset_p3d(longest.geometry, pm, - tap_width_input.value / 2),
                        Edge.offset_p3d(longest.geometry, pm, tap_width_input.value / 2)
                    ]
                    cut_curves = SketchCurve.split_at_p3ds(longest, tabs)
                    SketchCurve.delete_alternate(cut_curves)

    osketch.areConstraintsShown = False
    osketch.areDimensionsShown = False
    osketch.areProfilesShown = False

# This function will be called when the command needs to compute a new preview in the graphics window
def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    futil.log(f'{CMD_NAME} Command Preview Event')


# This function will be called when the user changes anything in the command dialog
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')
