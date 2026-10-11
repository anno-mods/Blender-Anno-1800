import bpy

from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty,CollectionProperty
from bpy.types import Operator, AddonPreferences
from bpy.types import Object as BlenderObject
from bpy_extras.object_utils import AddObjectHelper

from ..anno_objects import MainFile, Model, Propcontainer, Prop, Cloth, Decal, SubFile, ClothMaterial
from ..material import Material
from ..shaders.default_shader import AnnoDefaultShader
from ..shaders.prop_decal_shader import DecalPropShader
from ..shaders.prop_decaldetail_shader import DecalDetailPropShader
from ..shaders.prop_pbr_shader import SimplePBRPropShader
from ..shaders.prop_terrain_shader import TerrainPropShader
from ..shaders.prop_plant_shader import PlantPropShader
from ..shaders.prop_grass_shader import GrassPropShader
from ..shaders.decal_shader import DecalShader
from ..shaders.cutout_shader import CutoutShader
from ..shaders.cloth_shader import ClothShader
from ..shaders.mockup_shader import MockupShader
from ..shaders.destruct_shader import DestructShader
from ..shaders.water_shader import LiquidShader
from ..shaders.glass_shader import GlassShader

class generic_cfg_object(Operator, AddObjectHelper):
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

class cfg_mainfile(generic_cfg_object):
    bl_idname = "mesh.add_anno_mainfile"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = MainFile()

class cfg_model(generic_cfg_object):
    bl_idname = "mesh.add_anno_model"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Model()

class cfg_propcontainer(generic_cfg_object):
    bl_idname = "mesh.add_anno_propcontainer"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Propcontainer()

class cfg_prop(generic_cfg_object):
    bl_idname = "mesh.add_anno_prop"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Prop()

class cfg_cloth(generic_cfg_object):
    bl_idname = "mesh.add_anno_cloth"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Cloth()

class cfg_decal(generic_cfg_object):
    bl_idname = "mesh.add_anno_decal"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = Decal()

class cfg_subfile(generic_cfg_object):
    bl_idname = "mesh.add_anno_subfile"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TargetObject = SubFile()

class cfg_menu(bpy.types.Menu):
    bl_idname="add.anno_objects"
    bl_label="Anno Objects"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            cfg_mainfile.bl_idname,
            text="Empty MainFile",
            icon='FILE_BLANK'
        )
        layout.operator(
            cfg_subfile.bl_idname,
            text="Empty SubFile",
            icon='APPEND_BLEND'
        )
        layout.operator(
            cfg_model.bl_idname,
            text="Empty Model",
            icon='MESH_CUBE'
        )
        layout.operator(
            cfg_propcontainer.bl_idname,
            text="Empty Propcontainer",
            icon='FILE_VOLUME'
        )
        layout.operator(
            cfg_decal.bl_idname,
            text="Empty Decal",
            icon='MESH_PLANE'
        )
        layout.operator(
            cfg_cloth.bl_idname,
            text="Empty Cloth",
            icon='MOD_CLOTH'
        )
        #layout.operator(
        #    cfg_prop.bl_idname,
        #    text="Empty Prop",
        #    icon='PLUGIN'
        #)


class shader_menu(bpy.types.Menu):
    bl_idname="add.anno_shaders"
    bl_label="Anno Shaders"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            shader_decal.bl_idname,
            text="Decal (1)",
            icon='FILE_BLANK'
        )        
        layout.operator(
            shader_cloth.bl_idname,
            text="Model | Cloth (0)",
            icon='FILE_BLANK'
        )       
        layout.operator(
            shader_glass.bl_idname,
            text="Model | Glass (2)",
            icon='FILE_BLANK'
        )      
        layout.operator(
            shader_mine_cutout.bl_idname,
            text="Model | Mine Cutout (4)",
            icon='FILE_BLANK'
        )             
        layout.operator(
            shader_cutout.bl_idname,
            text="Model | Cutout (5)",
            icon='FILE_BLANK'
        )          
        layout.operator(
            shader_destruct.bl_idname,
            text="Model | Destruction (6)",
            icon='FILE_BLANK'
        )         
        layout.operator(
            shader_destruct.bl_idname,
            text="Model | Liquid (7)",
            icon='FILE_BLANK'
        ) 
        layout.operator(
            shader_default.bl_idname,
            text="Model | Default (8)",
            icon='FILE_BLANK'
        )
        layout.operator(
            shader_mockup.bl_idname,
            text="Model | Mockup (18)",
            icon='FILE_BLANK'
        ) 
        layout.operator(
            shader_prop_simple_pbr.bl_idname,
            text="Prop | SimplePBR",
            icon='FILE_BLANK'
        ) 
        layout.operator(
            shader_prop_decal.bl_idname,
            text="Prop | Decal",
            icon='FILE_BLANK'
        ) 
        layout.operator(
            shader_prop_decal_detail.bl_idname,
            text="Prop | Decal Detail",
            icon='FILE_BLANK'
        )
        layout.operator(
            shader_prop_terrain.bl_idname,
            text="Prop | Terrain",
            icon='FILE_BLANK'
        )
        layout.operator(
            shader_prop_grass.bl_idname,
            text="Prop | Grass",
            icon='FILE_BLANK'
        )
        layout.operator(
            shader_prop_plant.bl_idname,
            text="Prop | Plant",
            icon='FILE_BLANK'
        )

def add_anno_object_menu(self, context):
    self.layout.menu(
        cfg_menu.bl_idname,
        text="Anno Objects",
        icon='FILE_BLEND')

def add_anno_shader_menu(self, context):
    self.layout.menu(
        shader_menu.bl_idname,
        text="Anno Shaders",
        icon='FILE_BLEND')

class shader_default(bpy.types.Operator):
    bl_idname = "node.add_anno_shader"
    bl_label  = "Add Default Anno Shader"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = AnnoDefaultShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_prop_simple_pbr(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_prop_simple_pbr"
    bl_label  = "Add Prop:SimplePBR Anno Shader"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = SimplePBRPropShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_prop_decal(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_prop_decal"
    bl_label  = "Add Prop:Decal Anno Shader"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = DecalPropShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_prop_decal_detail(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_prop_decal_detail"
    bl_label  = "Add Prop:DecalDetail Anno Shader"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = DecalDetailPropShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_prop_terrain(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_prop_terrain"
    bl_label  = "Add Prop:DecalDetail Anno Shader"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = TerrainPropShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_prop_grass(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_prop_grass"
    bl_label  = "Add Prop:DecalDetail Anno Shader"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = GrassPropShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_prop_plant(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_prop_plant"
    bl_label  = "Add Prop:DecalDetail Anno Shader"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = PlantPropShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}


# todo (Taube) this is broken, reimplement this operator for actual cloth when shaders are rewritten.
class shader_cloth(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_cloth"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = ClothShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_cutout(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_cutout"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = CutoutShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}


class shader_mine_cutout(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_mine_cutout"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = MineCutoutShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_decal(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_decal"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = DecalShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_mockup(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_mockup"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = MockupShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_destruct(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_destruct"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = DestructShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}

class shader_water(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_water"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = LiquidShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}
    
class shader_glass(bpy.types.Operator):
    bl_idname = "node.add_anno_shader_glass"
    bl_label  = "Add Custom Node Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == "NODE_EDITOR"

    def execute(self, context):
        node_tree = context.object.active_material.node_tree
        my_group = GlassShader().add_anno_shader(node_tree.nodes)
        return {"FINISHED"}


classes = (
    cfg_mainfile,
    cfg_model,
    cfg_subfile,
    cfg_propcontainer,
    cfg_prop,
    cfg_cloth,
    cfg_decal,
    cfg_menu,
    shader_menu,
    shader_default,
    shader_prop_simple_pbr,
    shader_prop_decal_detail,
    shader_prop_decal,
    shader_prop_terrain,
    shader_prop_grass,
    shader_prop_plant,
    shader_cloth,
    shader_cutout,
    shader_mine_cutout,
    shader_decal,
    shader_mockup,
    shader_destruct,
    shader_water,
    shader_glass
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_MT_add.append(add_anno_object_menu)
    bpy.types.NODE_MT_add.append(add_anno_shader_menu)

def unregister():
    from bpy.utils import unregister_class
    bpy.types.VIEW3D_MT_add.remove(add_anno_object_menu)
    bpy.types.NODE_MT_add.remove(add_anno_shader_menu)
    for cls in classes:
        unregister_class(cls)
        