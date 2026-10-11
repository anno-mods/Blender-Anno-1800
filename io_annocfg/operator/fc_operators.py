import bpy

from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty,CollectionProperty
from bpy.types import Operator, AddonPreferences
from bpy.types import Object as BlenderObject
from bpy_extras.object_utils import AddObjectHelper
import xml.etree.ElementTree as ET

from ..anno_objects import Cf7Dummy, Cf7DummyGroup, Cf7File, MainFile, get_anno_object_class

def get_cf7file_ancestor(obj):
    # run through the object hierarchy to find a cf7file
    t_parent = obj.parent 
    print(get_anno_object_class(t_parent))
    print(t_parent)
    while t_parent and get_anno_object_class(t_parent) != Cf7File:
        print(get_anno_object_class(t_parent))    
        t_parent = t_parent.parent
    
    if(get_anno_object_class(t_parent) == Cf7File):
        return t_parent 
    
    return None

class generic_fc_object(Operator, AddObjectHelper):
    bl_idname = "mesh.add_anno_cfgobj"
    bl_options = {'REGISTER', 'UNDO'}
    bl_label = "Add Anno Object"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = ""
        self.TargetObject : AnnoObject = MainFile()

    def draw(self, context):
        layout = self.layout

    def execute(self, context):
        self.parent = context.active_object
        obj = self.TargetObject.from_default()
        if self.parent:
            obj.parent = self.parent
        return {'FINISHED'}
    
class fc_object_with_id(generic_fc_object):
    def execute(self, context):
        self.parent = context.active_object
        obj = self.TargetObject.from_default()
        if self.parent:
            obj.parent = self.parent
            cf7_par = get_cf7file_ancestor(obj)

            if(cf7_par is None):
                return { 'FINISHED' }

            id = cf7_par.dynamic_properties.get_int("IdCounter")
            cf7_par.dynamic_properties.set("IdCounter", str(id + 1), replace = True)
            obj.dynamic_properties.set("Id", str(id + 1), replace = True)

        return {'FINISHED'}

class fc_file(generic_fc_object):
    """Adds a new Fc File"""
    bl_idname = "mesh.add_anno_feedbackfile"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Cf7File()

    def execute(self, context):
        self.parent = context.active_object
        obj = self.TargetObject.from_default()
        if self.parent:
            obj.parent = self.parent

        obj.name = "FCFile"
        return {'FINISHED'}

class fc_Dummy(fc_object_with_id):
    """Creates a new Dummy inside the selected DummyGroup"""
    bl_idname = "mesh.add_anno_dummy"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Cf7Dummy()
    
    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        return get_anno_object_class(context.active_object) == Cf7DummyGroup

class fc_DummyGroup(fc_object_with_id):
    """Creates a new DummyGroup inside the selected fc file or DummyGroup"""
    bl_idname = "mesh.add_anno_dummygroup"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Cf7DummyGroup()

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        
        o_class =  get_anno_object_class(context.active_object) 
        return o_class == Cf7DummyGroup or o_class == Cf7File

class fc_menu(bpy.types.Menu):
    bl_idname="add.anno_fc_objects"
    bl_label="Anno Feedback Objects"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            fc_file.bl_idname,
            text="FC File",
            icon='FILE_BLANK'
        )
        layout.operator(
            fc_Dummy.bl_idname,
            text="Dummy",
            icon='FILE_BLANK'
        )
        layout.operator(
            fc_DummyGroup.bl_idname,
            text="DummyGroup",
            icon='APPEND_BLEND'
        )

def add_anno_fc_menu(self, context):
    self.layout.menu(
        fc_menu.bl_idname,
        text="Anno Feedback",
        icon='FILE_BLEND')

classes = (
    fc_menu,
    fc_file,
    fc_Dummy,
    fc_DummyGroup,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_MT_add.append(add_anno_fc_menu)

def unregister():
    from bpy.utils import unregister_class
    bpy.types.VIEW3D_MT_add.remove(add_anno_fc_menu)
    for cls in classes:
        unregister_class(cls)
        