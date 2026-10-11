import xml.etree.ElementTree as ET
import mathutils
from ..utils import to_data_path, data_path_to_absolute_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences
import bpy
import subprocess
import logging 

log = logging.getLogger("ShaderComponents")

def texture_quality_suffix():
    return "_"+IO_AnnocfgPreferences.get_texture_quality()

class AbstractLink: 
    def __init__(self, default_value = None, is_invalid = False):
        self.socket_type = ""
        self.link_key = ""
        self.is_invalid = is_invalid 
        self.default_value = default_value

    def has_socket(self):
        return self.socket_type is not "NoSocket"

    def has_default_value(self):
        return self.default_value is not None

    # todo pass in only the shader node to the material.
    def to_xml(self, parent, blender_material):
        return None

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        return 

    # called by the shader after the interface socket was created in the node group
    def setup_socket(self, node_group, interface_socket):
        return

    def finalize_shader(self, node_group):
        return

    def get_input(self, blender_material):
        group = [n for n in blender_material.node_tree.nodes if n.bl_idname == "ShaderNodeGroup"]
        return group[0].inputs.get(self.link_key)

class StaticFakeLink(AbstractLink):
    def __init__(self, link_key, flag_key, static_value : str, is_invalid = False):
        super().__init__(static_value, is_invalid)
        self.socket_type = "NoSocket"
        self.link_key = link_key
        self.flag_key = flag_key

    def to_xml(self, parent : ET.Element, blender_material):
        flag = ET.SubElement(parent, self.flag_key)
        flag.text = self.default_value

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        return 

class FlaglessTextureLink(AbstractLink):
    def __init__(self, link_key, texture_key, is_invalid = False, default_value = None, alpha_link = None):
        super().__init__(default_value, is_invalid)
        self.socket_type = "NodeSocketColor"
        self.texture_key = texture_key
        self.link_key = link_key
        self.alpha_link = alpha_link
    
    def has_alpha_link(self):
        return self.alpha_link is not None

    def to_xml(self, parent : ET.Element, blender_material):
        # get links
        links = blender_material.node_tree.links 
        # there should only ever be one link where the key is equal to the socketname.
        link = [l for l in links if self.link_key == l.to_socket.name]

        if len(link) == 0:
            log.warning(f"Missing texture link at {self.texture_key}, linked to {self.link_key}")
            return
        
        texture_node = link[0].from_node
        filepath_full = os.path.realpath(bpy.path.abspath(texture_node.image.filepath, library=texture_node.image.library))
        texture_path = to_data_path(filepath_full)
        #Rename "data/.../some_diff_0.png" to "data/.../some_diff.psd"
        extension = ".psd"
        texture_path = Path(texture_path.as_posix().replace(texture_quality_suffix()+".", ".")).with_suffix(extension)

        tex = ET.SubElement(parent, self.texture_key)
        tex.text = str(texture_path)

    def to_blender(self, shader, material_node : ET.Element, blender_material):      
        texture_xmlnode = material_node.find(self.texture_key)
        if texture_xmlnode is None:
            return

        texture_node = blender_material.node_tree.nodes.new('ShaderNodeTexImage')

        texture_path = Path(texture_xmlnode.text)
        texture = self.get_texture(texture_path)

        if texture is not None: 
            texture_node.image = texture
            if "Norm" in self.texture_key or "Metal" in self.texture_key or "Height" in self.texture_key:
                    texture_node.image.colorspace_settings.name = 'Non-Color'

        texture_node.name = self.texture_key
        texture_node.label = self.texture_key

        # create link: 
        blender_material.node_tree.links.new(shader.inputs[self.link_key], texture_node.outputs["Color"])

        if self.has_alpha_link():
            blender_material.node_tree.links.new(shader.inputs[self.alpha_link], texture_node.outputs["Alpha"])

    def get_texture(self, texture_path: Path):
        """Tries to find the texture texture_path with ending "_0.png" (quality setting can be changed) in the list of loaded textures.
        Otherwise loads it. If it is not existing but the corresponding .dds exists, converts it first.

        Args:
            texture_path (str): f.e. "data/.../texture_diffuse.psd"

        Returns:
            [type]: The texture or None.
        """
        if texture_path == Path(""):
            return None
        texture_path = Path(texture_path)
        texture_path = Path(texture_path.parent, texture_path.stem + texture_quality_suffix()+".dds")
        png_file = texture_path.with_suffix(".png")
        fullpath = data_path_to_absolute_path(texture_path)
        png_fullpath = data_path_to_absolute_path(png_file)
        image = bpy.data.images.get(str(png_file.name), None)
        if image is not None:
            image_path_full = os.path.normpath(bpy.path.abspath(image.filepath, library=image.library))
            if str(image_path_full) == str(png_fullpath):
                return image
        if not png_fullpath.exists():
            success = self.convert_to_png(fullpath)
            if not success:
                print("Failed to convert texture", fullpath)
                return None
        image = bpy.data.images.load(str(png_fullpath))
        return image

    def convert_to_png(self, fullpath: Path) -> bool:
        """Converts the .dds file to .png. Returns True if successful, False otherwise.

        Args:
            fullpath (str): .dds file

        Returns:
            bool: Successful
        """
        if not IO_AnnocfgPreferences.get_path_to_texconv().exists():
            return False
        if not fullpath.exists():
            return False
        try:
            proc_args = f"\"{IO_AnnocfgPreferences.get_path_to_texconv()}\" -ft PNG -sepalpha -y -o \"{fullpath.parent}\" \"{fullpath}\""
            subprocess.call(proc_args)
        except:
            return False
        return fullpath.with_suffix(".png").exists()
      

class TextureLink(FlaglessTextureLink): 
    def __init__(self, link_key, flag_key, texture_key, is_invalid = False, default_value = None, alpha_link = None):
        super().__init__(link_key, texture_key, is_invalid, default_value, alpha_link)
        self.flag_key = flag_key 

    def to_xml(self, parent : ET.Element, blender_material):
        super().to_xml(parent, blender_material)

        flag = ET.SubElement(parent, self.flag_key)

        # export a flag that states whether the material is connected
        tex_node = parent.find(self.texture_key)

        # if the texture is not there, export 0
        if ((tex_node is None) or (tex_node.text is None) or (tex_node.text == "")):
            flag.text = "0"
            return
        flag.text = "1"

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        flag = material_node.find(self.flag_key)
        if flag is None:
            return
        if (flag.text == "1"):
            super().to_blender(shader, material_node, blender_material)

class FlagLink(AbstractLink): 
    def __init__(self, link_key, flag_key, is_invalid = False, default_value = None):
        super().__init__(default_value, is_invalid)
        self.socket_type = "NodeSocketBool"
        self.flag_key = flag_key
        self.link_key = link_key
        
    def to_xml(self, parent : ET.Element, blender_material):
        input = self.get_input(blender_material)
        value = False 
        if(input is not None):
            value = input.default_value

        flag = ET.SubElement(parent, self.flag_key)
        flag.text = "1" if value else "0"

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        input = self.get_input(blender_material)
        subnode = material_node.find(self.flag_key)
        input.default_value = True if subnode is not None and subnode.text == "1" else False

class FloatLink(AbstractLink): 
    def __init__(self, link_key, flag_key, is_invalid = False, default_value = None):
        super().__init__(default_value, is_invalid)
        self.socket_type = "NodeSocketFloat"
        self.flag_key = flag_key
        self.link_key = link_key

    def to_xml(self, parent : ET.Element, blender_material):
        input = self.get_input(blender_material)
        value = 0.0
        if(input is not None):
            value = input.default_value

        flag = ET.SubElement(parent, self.flag_key)
        flag.text = str(round(value, 6))

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        input = self.get_input(blender_material)
        subnode = material_node.find(self.flag_key)
        if subnode is None:
            input.default_value = 0.0 
        try:
            input.default_value = float(subnode.text)
        except: 
            input.default_value = self.default_value if self.has_default_value() else 0.0

class IntegerLink(AbstractLink): 
    def __init__(self, link_key, flag_key, is_invalid = False, default_value = None):
        super().__init__(default_value, is_invalid)
        self.socket_type = "NodeSocketInt"
        self.flag_key = flag_key
        self.link_key = link_key

    def to_xml(self, parent : ET.Element, blender_material):
        input = self.get_input(blender_material)
        value = 0
        if(input is not None):
            value = input.default_value

        flag = ET.SubElement(parent, self.flag_key)
        flag.text = str(round(value, 6))

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        input = self.get_input(blender_material)
        if input is None: 
            return 
        subnode = material_node.find(self.flag_key)
        if subnode is None:
            input.default_value = 0
        try:
            input.default_value = int(subnode.text)
        except: 
            input.default_value = self.default_value if self.has_default_value() else 0

class StringLink(AbstractLink): 
    def __init__(self, link_key, flag_key, is_invalid = False, default_value = None):
        super().__init__(default_value, is_invalid)
        self.socket_type = "NodeSocketString"
        self.flag_key = flag_key
        self.link_key = link_key

    def to_xml(self, parent : ET.Element, blender_material):
        input = self.get_input(blender_material)
        value = ""
        if(input is not None):
            value = input.default_value

        flag = ET.SubElement(parent, self.flag_key)
        flag.text = str(round(value, 6))

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        input = self.get_input(blender_material)
        subnode = material_node.find(self.flag_key)
        if subnode is None:
            input.default_value = ""
        try:
            input.default_value = subnode.text
        except: 
            input.default_value = self.default_value if self.has_default_value() else ""

class EnumLink(AbstractLink): 
    # NodeSocketMenu gets its items from the Menu Switch node it is connected to inside the group.
    MENU_SWITCH_IDNAMES = ("ShaderNodeMenuSwitch", "GeometryNodeMenuSwitch")

    def __init__(self, link_key, flag_key, options, is_invalid = False, default_value = None):
        # options: list of values, or dict {displayed value: exported value}
        if isinstance(options, dict):
            self.mapping = dict(options)
        else:
            self.mapping = {option: option for option in options}
        self.options = list(self.mapping.keys())
        if default_value is None and len(self.options) > 0:
            default_value = self.options[0]
        super().__init__(default_value, is_invalid)
        self.socket_type = "NodeSocketMenu"
        self.flag_key = flag_key
        self.link_key = link_key

    def setup_socket(self, node_group, interface_socket):
        menu_switch = None
        for idname in self.MENU_SWITCH_IDNAMES:
            try:
                menu_switch = node_group.nodes.new(type = idname)
                break
            except RuntimeError:
                continue
        if menu_switch is None:
            log.warning("Menu Switch node is not available in this Blender version, cannot create items for '%s'.", self.link_key)
            return

        menu_switch.label = self.link_key
        menu_switch.enum_items.clear()
        for option in self.options:
            menu_switch.enum_items.new(option)

        group_input = node_group.nodes.new(type = "NodeGroupInput")
        node_group.links.new(group_input.outputs[self.link_key], menu_switch.inputs["Menu"])

    # Blender greys out menu sockets that do not influence the group output.
    # Route the menu switch through a neutral Mix Shader (both inputs identical) in front of the output.
    def finalize_shader(self, node_group):
        menu_switch = next((n for n in node_group.nodes 
            if n.bl_idname in self.MENU_SWITCH_IDNAMES and n.label == self.link_key), None)
        group_output = next((n for n in node_group.nodes if n.bl_idname == "NodeGroupOutput"), None)
        if menu_switch is None or group_output is None:
            return
        shader_input = group_output.inputs.get("Shader")
        if shader_input is None or not shader_input.is_linked:
            return

        source = shader_input.links[0].from_socket
        mix = node_group.nodes.new(type = "ShaderNodeMixShader")
        mix.label = self.link_key + " (keeps menu active)"
        mix.location = (group_output.location.x - 200, group_output.location.y)
        node_group.links.new(source, mix.inputs[1])
        node_group.links.new(source, mix.inputs[2])
        node_group.links.new(menu_switch.outputs[0], mix.inputs[0])
        node_group.links.new(mix.outputs[0], shader_input)

    def to_xml(self, parent : ET.Element, blender_material):
        input = self.get_input(blender_material)
        value = self.default_value if self.has_default_value() else ""
        if input is not None and input.default_value:
            value = input.default_value

        flag = ET.SubElement(parent, self.flag_key)
        flag.text = str(self.mapping.get(value, value))

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        input = self.get_input(blender_material)
        if input is None: 
            return 
        value = self.default_value if self.has_default_value() else None
        subnode = material_node.find(self.flag_key)
        if subnode is not None and subnode.text is not None:
            displayed = next((d for d, e in self.mapping.items() if str(e) == subnode.text), None)
            if displayed is not None:
                value = displayed
        if value is None:
            return
        try:
            input.default_value = value
        except TypeError:
            log.warning("Could not set menu value '%s' for '%s'.", value, self.link_key)

class ColorLink(AbstractLink): 
    def __init__(self, link_key, flag_key, is_invalid = False, default_value = None):
        super().__init__(default_value, is_invalid)
        self.socket_type = "NodeSocketColor"
        self.flag_key = flag_key
        self.link_key = link_key

        self.color_keys = ["r", "g", "b"]
    
    def to_xml(self, parent : ET.Element, blender_material):
        input = self.get_input(blender_material)
        value = (0.0, 0.0, 0.0, 0.0)
        if(input is not None):
            value = input.default_value

        for i, val in enumerate(self.color_keys):
            r = ET.SubElement(parent, self.flag_key + "." + val)
            r.text = str(round(value[i], 6))

    def to_blender(self, shader, material_node : ET.Element, blender_material):
        input = self.get_input(blender_material)

        color_arr = [0.0, 0.0, 0.0, 1.0]

        issue = False

        for i, val in enumerate(self.color_keys):
            subnode = material_node.find(self.flag_key + "." + val)
            if issue:
                continue
            if subnode is None:
                color_arr[i] = 0.0
            try:
                color_arr[i] = float(subnode.text)
            except: 
                issue = True
                color_arr = self.default_value if self.has_default_value() else [0.0, 0.0, 0.0, 1.0]

        print(self.link_key + " | " + self.flag_key)
        print(color_arr)

        input.default_value = tuple(color_arr)
        
class AbstractShaderComponent:
    def __init__():
        self.component_properties = {}
        self.links = []

class DefaultPropComponent(AbstractShaderComponent): 
    def __init__(self):
        self.links = [
            TextureLink("cMetallic", "METALLIC_TEX_ENABLED", "cModelMetallicTex"),
            FloatLink("Metalness Factor", "cMetallic"),
            FloatLink("AO Factor", "cAmbientOcclusion"),
            FlagLink("TerrainTint", "cUseTerrainTinting"),
            FlagLink("TerrainGrit", "cUseTerrainGrit"),
            TextureLink("cSeperateAO", "SEPARATE_AO_TEXTURE", "cSeparateAOTex"),
            TextureLink("Specular Occlusion", "SPEC_OCCLUSION_TEX_ENABLED", "cModelSpecOcclusionTex"),
            FlagLink("Specular uses 2nd UV set", "SPEC_OCCLUSION_USE_2ND_UV")
        ]


class VertexFormatShaderComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            IntegerLink("NumBonesPerVertex", "NumBonesPerVertex", 0),
            EnumLink("VertexFormat", "VertexFormat", 
                     { "Standard (P4h_N4b_G4b_B4b_T2h)": "P4h_N4b_G4b_B4b_T2h", 
                      "Joints (P4h_N4b_G4b_B4b_T2h_I4b)": "P4h_N4b_G4b_B4b_T2h_I4b", 
                      "Weighted Joints (P4h_N4b_G4b_B4b_T2h_I4b_W4b)": "P4h_N4b_G4b_B4b_T2h_I4b_W4b", 
                      "4 Weighted Joins (P4h_N4b_G4b_B4b_T2h_I4b_I4b_I4b_I4b_W4b_W4b_W4b_W4b)": "P4h_N4b_G4b_B4b_T2h_I4b_I4b_I4b_I4b_W4b_W4b_W4b_W4b" })
        ]

class ShortDefaultVertexFormatShaderComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            IntegerLink("NumBonesPerVertex", "NumBonesPerVertex", 0),
            EnumLink("VertexFormat", "VertexFormat", 
                     { "Standard (P4h_N4b_G4b_B4b_T2h)": "P4h", 
                      "Joints (P4h_N4b_G4b_B4b_T2h_I4b)": "P4h_N4b_G4b_B4b_T2h_I4b", 
                      "Weighted Joints (P4h_N4b_G4b_B4b_T2h_I4b_W4b)": "P4h_N4b_G4b_B4b_T2h_I4b_W4b", 
                      "4 Weighted Joins (P4h_N4b_G4b_B4b_T2h_I4b_I4b_I4b_I4b_W4b_W4b_W4b_W4b)": "P4h_N4b_G4b_B4b_T2h_I4b_I4b_I4b_I4b_W4b_W4b_W4b_W4b" })
        ]

class DefaultShaderFakeComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            TextureLink("cMetallic", "METALLIC_TEX_ENABLED", "cModelMetallicTex"),
            TextureLink("cSeperateAO", "SEPARATE_AO_TEXTURE", "cSeparateAOTex"),
            FlagLink("TerrainTint", "cUseTerrainTinting")
        ]

class CommonShaderComponent(AbstractShaderComponent): 
    def __init__(self):
        self.links = [
            StaticFakeLink("Common", "Common", "Common"),
            TextureLink("cDiffuse", "DIFFUSE_ENABLED", "cModelDiffTex", alpha_link="Alpha"),  
            FloatLink("Alpha", "", is_invalid=True, default_value=1.0),
            TextureLink("cNormal", "NORMAL_ENABLED", "cModelNormalTex", alpha_link="Glossiness"),
            FloatLink("Glossiness", "", is_invalid=True),
            ColorLink("cDiffuseMultiplier", "cDiffuseColor", default_value=(1.0, 1.0, 1.0, 1.0)),
            FloatLink("Gloss Factor", "cGlossinessFactor", default_value=1.0),
            FloatLink("Opacity", "cOpacity", default_value=1.0)
        ]

class DyeMaskTexScrollShaderComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            FloatLink("Texture Scroll Speed", "cTexScrollSpeed", default_value=0.0),
            TextureLink("cDyeMask", "DYE_MASK_ENABLED", "cDyeMask")
        ]

class AdditionalPBRShaderComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            TextureLink("cHeight", "HEIGHT_MAP_ENABLED", "cHeightMap"),
            FloatLink("Parallax Scale", "cParallaxScale", default_value=1.0),
            FlagLink("Parallax Mapping", "PARALLAX_MAPPING_ENABLED", default_value=True),
            FlagLink("Self Shadowing", "SELF_SHADOWING_ENABLED"),
            FlagLink("Cutout Water", "WATER_CUTOUT_ENABLED")
        ]

class TerrainAdaptionShaderComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [            
            StaticFakeLink("TerrainAdaption", "TerrainAdaption", "TerrainAdaption"),
            FlagLink("Adapt to Terrain", "ADJUST_TO_TERRAIN_HEIGHT"),
            FlagLink("Use Vertex Colors", "VERTEX_COLORED_TERRAIN_ADAPTION"),
            FlagLink("Absolute TerrainAdaption", "ABSOLUTE_TERRAIN_ADAPTION")
        ]

class EnvironmentShaderComponent(AbstractShaderComponent): 
    def __init__(self): 
        self.links = [
            StaticFakeLink("Environment", "Environment", "Environment"),
            FlagLink("Use Local Environment Box", "cUseLocalEnvironmentBox", default_value=True),
            FloatLink("BBox Min X", "cEnvironmentBoundingBox.x", default_value=0.0),
            FloatLink("BBox Min Y", "cEnvironmentBoundingBox.y", default_value=0.0),          
            FloatLink("BBox Max X", "cEnvironmentBoundingBox.z", default_value=0.0),
            FloatLink("BBox Max Y", "cEnvironmentBoundingBox.w", default_value=4.0),        
        ]

class GlowShaderComponent(AbstractShaderComponent): 
    def __init__(self):
        self.links = [
            StaticFakeLink("Glow", "Glow", "Glow"),
            FlagLink("Enable Glow", "GLOW_ENABLED"),
            ColorLink("cEmissiveColor", "cEmissiveColor", default_value=(2.0, 2.0, 2.0, 1.0)),
            TextureLink("cNightGlow", "NIGHT_GLOW_ENABLED", "cNightGlowMap")
        ]
class PropShadowsComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            FlagLink("Linear Shadow Interpolation", "LINEAR_SHADOW_INTERPOLATION_ENABLED"),
            FloatLink("Shadow Bias", "cModelShadowBias", default_value=0.0),            
            FlagLink("Exclude from SSR", "EXCLUDE_FROM_SSR_ENABLED"),
            FlagLink("Late Pre-Depth", "LATE_PRE_DEPTH")
        ]

class PropBasicDiffuseComponent(AbstractShaderComponent): 
    def __init__(self):
        self.links = [
            FlaglessTextureLink("cDiffuse", "cPropDiffuseTex", alpha_link="Alpha"),
            FloatLink("Alpha", "", is_invalid=True, default_value=1.0),
            ColorLink("cDiffuseMultiplier", "cDiffuseColor", default_value=(1.0, 1.0, 1.0, 1.0)),            
            FloatLink("AlphaRef", "cAlphaRef"),
        ]

class PropBasicDiffNormComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            FlaglessTextureLink("cDiffuse", "cPropDiffuseTex", alpha_link="Alpha"),
            FloatLink("Alpha", "", is_invalid=True, default_value=1.0),
            FlaglessTextureLink("cNormal", "cPropNormalTex", alpha_link="Glossiness"),
            FloatLink("Glossiness", "", is_invalid=True),
            ColorLink("cDiffuseMultiplier", "cDiffuseColor", default_value=(1.0, 1.0, 1.0, 1.0)),
        ]

class PropPlantDiffNormComponent(AbstractShaderComponent): 
    def __init__(self):
        self.links = [
            StaticFakeLink("Common", "Common", "Common"),
            TextureLink("cDiffuse", "DIFFUSE_ENABLED", "cPropDiffuseTex", alpha_link="Alpha"),  
            FloatLink("Alpha", "", is_invalid=True, default_value=1.0),
            TextureLink("cNormal", "NORMAL_ENABLED", "cPropNormalTex", alpha_link="Glossiness"),
            FloatLink("Glossiness", "", is_invalid=True),
            ColorLink("cDiffuseMultiplier", "cDiffuseColor", default_value=(1.0, 1.0, 1.0, 1.0)),
        ]

class PropDecalComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [          
            ColorLink("cSpecular", "cSpecularColor", default_value=(1.0, 1.0, 1.0, 1.0)),
            FloatLink("cOpacity", "cOpacity", default_value=1.0),
            FloatLink("Glossiness Factor", "cGlossinessFactor", default_value=1.0),
            FlagLink("Terrain Tint", "cUseTerrainTinting"),
            FlagLink("Terrain Grit", "cUseTerrainGrit"),
            FlagLink("Align on Water", "cAlignOnWater"),
            FloatLink("Depth Bias", "cDepthBias", default_value=1.0)
        ]

class TerrainMaterialComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("TerrainMaterial", "TerrainMaterial", "TerrainMaterial"),
            FlagLink("Enable Terrain Material", "ENABLE_TERRAIN_MATERIAL"),
            FlaglessTextureLink("cTerrainDiff", "cPropTerrainDiffuseTex"),
            FlaglessTextureLink("cTerrainNorm", "cPropTerrainNormalTex"),
            FloatLink("TerrainTex Repeat", "cTerrainTexRepetition", default_value=4.0),
            FlagLink("Mix Terrain With Diff", "cMixTerrainTexWithDiffuse"),
            FloatLink("Mix Contrast", "cDiffuseTerrainMixContrast"),
            FlagLink("Grit Effect", "cGritEffect"),
            FlagLink("Grit Slope Threshold", "cGritEffectSlopeThreshold"),
        ]

class TerrainIntegrationComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("TerrainIntegration", "TerrainIntegration", "TerrainIntegration"),
            FlagLink("Aligh to Terrain Normal", "cAlignToTerrainNormal"),
            FlagLink("Terrain Tint", "cUseTerrainTinting"),
            FlagLink("Terrain Grit", "cUseTerrainGrit"),
            FloatLink("Grit Skirt Height", "cGritSkirtHeight"),
            FlagLink("Adapt to Terrain Normal", "cAdaptToTerrainNormal"),
            FloatLink("Normal Skirt Height", "cNormalSkirtHeight"),
        ]

class GrassAdditionalComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            FlagLink("Disable Alpha TO Coverage", "DISABLE_ALPHA_TO_COVERAGE"),
            FloatLink("Trunk Wind Deflection", "cTrunkWindDeflection"),
            FloatLink("Leaf Wind Deflection", "cLeafWindDeflection"),
            StaticFakeLink("TerrainAdaption", "TerrainIntegration", ""),
            FlagLink("Aligh to Terrain Normal", "cAlignToTerrainNormal"),
            FlagLink("Terrain Tint", "cUseTerrainTinting"),
            FloatLink("Terrain Tint Intensity", "cTerrainTintIntensity"),
            FlagLink("Use Terrain Grit", "cUseTerrainGrit"),
            FlagLink("Scale by Vertex Luminance", "SCALE_BY_VERTEX_LUMINANCE"),
        ]

class PropTerrainAdaptionComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("TerrainAdaption", "TerrainIntegration", ""),
            FlagLink("Aligh to Terrain Normal", "cAlignToTerrainNormal"),
        ]

class PropBackfaceComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("BackFace", "BackFace", "BackFace"),
            FlagLink("Double Sided", "DOUBLE_SIDED"),
        ]

class PropTransparencyComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("Transparency", "Transparency", "Transparency"),
            FloatLink("Alpha Ref", "cAlphaRef"),
            FloatLink("Shadow Alpha Ref", "cShadowAlphaRef"),
        ]

class PropWindComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("Wind", "Wind", "Wind"),
            FlagLink("Enable Wind", "FARM_FIELD_WIND"),
            FloatLink("Wind Color Boost", "cWindColorBoost")
        ]

class PropTiledTintComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("TiledTint", "TiledTint", "TiledTint"),
            FlagLink("Enable Tiled Tint", "PROP_TINT_ENABLED"),
            FloatLink("TiledTint Tiling", "cPropTintTiling", default_value=1.0),
            FloatLink("TiledTint Intensity", "cPropTintIntensity", default_value=1.0)
        ]

class PropShadowNoiseComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("ShadowNoise", "ShadowNoise", "ShadowNoise"),
            FlagLink("Enable Shadownoise", "ENABLE_SHADOW_NOISE"),
            FloatLink("Noise", "cShadowNoise"),            
            FloatLink("NearNoise", "cShadowNoiseNear"),
            FloatLink("NearDistanceNoise", "cShadowNoiseNearDistance", default_value=10.0),
            FloatLink("Noise Size", "cShadowNoiseSize", default_value=1.0),
            FloatLink("Density", "cShadowDensity", default_value=1.0),
        ]

class PropShinySpotsComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("ShinySpots", "ShinySpots", "ShinySpots"),
            FloatLink("Sunlit Spot", "cSunLitSpot"),            
            FloatLink("Sunlit Spot Size", "cSunLitSpotSize", default_value=4.0),
            FloatLink("Sunreflect Spot", "cSunReflectSpot"),
            FloatLink("Sunreflect Spot Size", "cShadowNoiseSize", default_value=4.0)
        ]

class PropYetAnotherTerrainTintComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            FlagLink("Use Terrain Tint", "cUseTerrainTinting"),
            FlagLink("Boost Terrain Tint", "cBoostTerrainTinting"),
            FloatLink("Tint Intensity", "cTerrainTintIntensity", default_value=1.0)
        ]

class RimEffectComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("RimEffect", "RimEffect", "RimEffect"),
            ColorLink("Rim Color", "cRimColor"),
            FloatLink("Rim Intensity", "cRimIntensity")
        ]

class RipplesComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("Ripples", "Ripples", "Ripples"),
            TextureLink("RipplesTex", "RIPPLES_ENABLED", "cClothRippleTex"),
            FloatLink("Tiling", "cRippleTiling"),
            FloatLink("Speed", "cRippleSpeed"),
            FloatLink("Normal Intensity", "cRippleNormalIntensity")
        ]

class MiniTerrainAdapion(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("TerrainAdaption", "TerrainAdaption", "TerrainAdaption"),
            FlagLink("Adapt to Terrain", "ADJUST_TO_TERRAIN_HEIGHT")
        ]

class AtlasComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("Atlas", "Atlas", "Atlas"),
            FlagLink("Enable Logo Atlas", "LOGO_ATLAS_ENABLED"),
            FlagLink("Invert Logo Color", "INVERSE_LOGO_COLORING"),
        ]

class ClothShaderComponent(AbstractShaderComponent): 
    def __init__(self):
        self.links = [
            TextureLink("cDiffuse", "DIFFUSE_ENABLED", "cClothDiffuseTex", alpha_link="Alpha"),  
            FloatLink("Alpha", "", is_invalid=True, default_value=1.0),
            TextureLink("cNormal", "NORMAL_ENABLED", "cClothNormalTex", alpha_link="Glossiness"),
            FloatLink("Glossiness", "", is_invalid=True),
            ColorLink("cDiffuseMultiplier", "cDiffuseColor", default_value=(1.0, 1.0, 1.0, 1.0)),
            ColorLink("cSpecular", "cSpecularColor", default_value=(1.0, 1.0, 1.0, 1.0)),
            FloatLink("Gloss Factor", "cGlossinessFactor", default_value=1.0),
            FloatLink("Opacity", "cOpacity", default_value=1.0),
            FloatLink("AlphaRef", "cAlphaRef"),
            TextureLink("cDyeMask", "DYE_MASK_ENABLED", "cClothDyeMask", alpha_link="Glossiness"),
        ]

class CutoutComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            FlagLink("Cutout Terrain", "CUT_OUT_TERRAIN"),
            FlagLink("Cutout Water", "CUT_OUT_WATER")
        ]

class SimpleColorComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            ColorLink("Color", "cDiffuseColor"),
            FloatLink("Glossiness", "cGlossinessFactor"),
            FloatLink("Metallic", "cMetallicLowPoly"),
            FloatLink("Glow", "cGlow"),
            FlagLink("Adjust to Terrain Height", "ADJUST_TO_TERRAIN_HEIGHT"),
            FlagLink("Disable Revive Distance", "DisableReviveDistance"),
        ]

class LiquidStandardComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            FloatLink("Normal Intensity", "cFlowNormalIntensity"),
            FloatLink("Scaling", "cWaterTexScale"),
            FloatLink("Distortion", "cWaterDistortion"),
            FloatLink("Depth Fade", "cWaterDepthFade"),
            FloatLink("Depth", "cWaterDepth"),
            FloatLink("Reflectivity", "cBaseReflectivity"),
            FloatLink("Foam", "cWaterFoam"),
            FlagLink("Vertex Colored Foam", "VERTEX_COLOR_FOAM")
        ]

class FlowMapComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("FlowMap", "FlowMap", "FlowMap"),
            TextureLink("Flow Tex", "FLOW_MAP_ENABLED", "cWaterFlowTex"),
            FloatLink("Flow Speed", "cFlowSpeed")
        ]

class OceanWaveComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("OceanWaveTexture", "OceanWaveTexture", "OceanWaveTexture"),
            FlagLink("Use Small Waves", "USE_SMALL_WAVE_TEXTURE"),
            FloatLink("Small Waves Scale", "cSmallWaveTexScale")
        ]

class DetailMapComponent(AbstractShaderComponent):
    def __init__(self):
        self.links = [
            StaticFakeLink("DetailMap", "DetailMap", "DetailMap"),
            FlagLink("Enable Detail Map", "DETAIL_MAP_ENABLED"),
            FlaglessTextureLink("Water Detail", "cWaterDetailTex"),
            FlaglessTextureLink("Water Detail Normals", "cWaterDetailNormTex"),
        ]