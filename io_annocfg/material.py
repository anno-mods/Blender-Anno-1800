from __future__ import annotations
import bpy
from bpy.types import Object as BlenderObject
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple, List, NewType, Any, Union, Dict, Optional, TypeVar, Type
import bmesh
import sys
import os
import subprocess
from collections import defaultdict
from .prefs import IO_AnnocfgPreferences
from .utils import *

from .shaders import default_shader as SHADER


class Material:
    """
    Can be created from an xml material node. Stores with diffuse, normal and metal texture paths and can create a corresponding blender material from them.
    Uses a cache to avoid creating the exact same blender material multiple times when loading just one .cfg 
    """
    
    texture_definitions = {
        "cModelDiffTex":"DIFFUSE_ENABLED",
        "cModelNormalTex":"NORMAL_ENABLED",
        "cModelMetallicTex":"METALLIC_TEX_ENABLED",
        "cSeparateAOTex":"SEPARATE_AO_TEXTURE",
        "cHeightMap":"HEIGHT_MAP_ENABLED",
        "cNightGlowMap":"NIGHT_GLOW_ENABLED", 
        "cDyeMask":"DYE_MASK_ENABLED"
    }
    texture_names = {
        "diffuse":"cModelDiffTex",
        "normal":"cModelNormalTex",
        "metallic":"cModelMetallicTex",
        "ambient":"cSeparateAOTex",
        "height":"cHeightMap",
        "night_glow":"cNightGlowMap",
        "dye":"cDyeMask",
    }
    # color_definitions = {
    #     "cDiffuseColor":("cDiffuseColor.r", "cDiffuseColor.g", "cDiffuseColor.b"),
    #     "cEmissiveColor":("cEmissiveColor.r", "cEmissiveColor.g", "cEmissiveColor.b"),
    # }         "":"",
    

    color_definitions = ["cDiffuseColor", "cEmissiveColor"]
    custom_property_default_value = {
        "ShaderID":"", "VertexFormat":"", "NumBonesPerVertex":"", "cUseTerrainTinting":"", "Common":"", \
        "cTexScrollSpeed":"", "cParallaxScale":"", "PARALLAX_MAPPING_ENABLED":"", \
        "SELF_SHADOWING_ENABLED":"", "WATER_CUTOUT_ENABLED":"", "TerrainAdaption":"", "ADJUST_TO_TERRAIN_HEIGHT":"", "VERTEX_COLORED_TERRAIN_ADAPTION":"", \
        "ABSOLUTE_TERRAIN_ADAPTION":"", "Environment":"", "cUseLocalEnvironmentBox":"", "cEnvironmentBoundingBox.x":"", "cEnvironmentBoundingBox.y":"", "cEnvironmentBoundingBox.z":"", \
        "cEnvironmentBoundingBox.w":"", "Glow":"", "GLOW_ENABLED":"", \
        "WindRipples":"", "WIND_RIPPLES_ENABLED":"", "cWindRippleTex":"", "cWindRippleTiling":"", "cWindRippleSpeed":"", "cWindRippleNormalIntensity":"", \
        "cWindRippleMeshIntensity":"", "DisableReviveDistance":"", "cGlossinessFactor":"", "cOpacity":"",
    }
    materialCache: Dict[Tuple[Any,...], Material] = {}

    def __init__(self):
        self.textures: Dict[str, str] = {}
        self.texture_enabled: Dict[str, bool] = {}
        self.colors: Dict[str, List[float]] = {}
        self.custom_properties: Dict[str, Any] = {}
        self.name: str = "Unnamed Material"
        self.node = None
    @classmethod
    def from_material_node(cls, material_node: ET.Element) -> Material:
        instance = cls()
        instance.name = get_text_and_delete(material_node, "Name", "Unnamed Material")
        for texture_name, texture_enabled_flag in cls.texture_definitions.items():
            texture_path = get_text_and_delete(material_node, texture_name)
            instance.textures[texture_name] = texture_path
            instance.texture_enabled[texture_name] = bool(int(get_text(material_node, texture_enabled_flag, "0")))
        for color_name in cls.color_definitions:
            color = [1.0, 1.0, 1.0]
            color[0] = float(get_text_and_delete(material_node, color_name + ".r", 1.0))
            color[1] = float(get_text_and_delete(material_node, color_name + ".g", 1.0))
            color[2] = float(get_text_and_delete(material_node, color_name + ".b", 1.0))
            instance.colors[color_name] = color
        #for prop, default_value in cls.custom_property_default_value.items():
            #value = string_to_fitting_type(get_text(material_node, prop, default_value))
            #if value is not None:
            #    instance.custom_properties[prop] = value
        instance.node = material_node
        return instance
    
    @classmethod
    def from_filepaths(cls, name: str, diff_path: str, norm_path: str, metal_path: str) -> Material:
        element = ET.fromstring(f"""
            <Config>
                <Name>{name}</Name>
                <cModelDiffTex>{diff_path}</cModelDiffTex>
                <cModelNormalTex>{norm_path}</cModelNormalTex>
                <cModelMetallicTex>{metal_path}</cModelMetallicTex>
            </Config>                        
        """)
        return cls.from_material_node(element)
    
    
    @classmethod
    def from_default(cls) -> Material:
        element = ET.fromstring(f"""
            <Config>
                <Name>NEW_MATERIAL<Name>
            </Config>                        
        """)
        return cls.from_material_node(element)
         
    @classmethod
    def from_blender_material(cls, blender_material) -> Material:
        instance = cls()
        instance.node = blender_material.dynamic_properties.to_node(ET.Element("Material"))
        instance.name = blender_material.name
        for texture_name in cls.texture_definitions.keys():
            shader_node = blender_material.node_tree.nodes[texture_name] #Assumes that the nodes collection allows this lookup
            if not shader_node.image:
                instance.textures[texture_name] = ""
                instance.texture_enabled[texture_name] = shader_node.anno_properties.enabled
                continue
            filepath_full = os.path.realpath(bpy.path.abspath(shader_node.image.filepath, library=shader_node.image.library))
            texture_path = to_data_path(filepath_full)
            #Rename "data/.../some_diff_0.png" to "data/.../some_diff.psd"
            extension = shader_node.anno_properties.original_file_extension
            texture_path = Path(texture_path.as_posix().replace(instance.texture_quality_suffix()+".", ".")).with_suffix(extension)
            instance.textures[texture_name] = texture_path.as_posix()
            instance.texture_enabled[texture_name] = shader_node.anno_properties.enabled
        for color_name in cls.color_definitions:
            color = [1.0, 1.0, 1.0]
            shader_node = blender_material.node_tree.nodes.get(color_name, None)
            if shader_node:
                inputs = shader_node.inputs
                color = [inputs[0].default_value, inputs[1].default_value, inputs[2].default_value]
            instance.colors[color_name] = color
        for prop, default_value in cls.custom_property_default_value.items():
            if prop not in blender_material:
                if default_value:
                    instance.custom_properties[prop] = default_value
                continue
            instance.custom_properties[prop] = blender_material[prop]
        return instance
    
    def texture_quality_suffix(self):
        return "_"+IO_AnnocfgPreferences.get_texture_quality()
    
    def to_xml_node(self, parent: ET.Element) -> ET.Element:
        node = self.node
        if not parent is None:
            parent.append(node)
        # node = ET.SubElement(parent, "Config")
        #ET.SubElement(node, "ConfigType").text = "MATERIAL"
        ET.SubElement(node, "Name").text = self.name
        for texture_name in self.texture_definitions.keys():
            texture_path = self.textures[texture_name]
            if texture_path != "":
                ET.SubElement(node, texture_name).text = texture_path
        for color_name in self.color_definitions:
            ET.SubElement(node, color_name + ".r").text = format_float(self.colors[color_name][0])
            ET.SubElement(node, color_name + ".g").text = format_float(self.colors[color_name][1])
            ET.SubElement(node, color_name + ".b").text = format_float(self.colors[color_name][2])
        for texture_name, texture_enabled_flag in self.texture_definitions.items():
            used_value = self.texture_enabled[texture_name]
            find_or_create(node, texture_enabled_flag).text = str(int(used_value))
        for prop, value in self.custom_properties.items():
            if value == "":
                continue
            if type(value) == float:
                value = format_float(value)
            ET.SubElement(node, prop).text = str(value)
        return node
    
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
            subprocess.call(f"\"{IO_AnnocfgPreferences.get_path_to_texconv()}\" -ft PNG -sepalpha -y -o \"{fullpath.parent}\" \"{fullpath}\"")
        except:
            return False
        return fullpath.with_suffix(".png").exists()
    
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
        texture_path = Path(texture_path.parent, texture_path.stem + self.texture_quality_suffix()+".dds")
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

    

    def get_material_cache_key(self):
        attribute_list = tuple([self.name] + list(self.textures.items()) + list([(a, tuple(b)) for a, b in self.colors.items()]) + list(self.custom_properties.items()))
        return hash(attribute_list)
    
    
    
    def add_anno_shader(self, nodes):
        group = nodes.new(type='ShaderNodeGroup')
        if not "AnnoDefaultShader" in bpy.data.node_groups:
            SHADER.AnnoDefaultShader().create_anno_shader()            
        group.node_tree = bpy.data.node_groups["AnnoDefaultShader"]
        return group
        
    def as_blender_material(self):

        if self.get_material_cache_key() in Material.materialCache:
            return Material.materialCache[self.get_material_cache_key()]
        
        material = bpy.data.materials.new(name=self.name)
        
        material.dynamic_properties.from_node(self.node)
        material.use_nodes = True
        
        positioning_unit = (300, 300)
        positioning_offset = (0, 3 * positioning_unit[1])
        
        
        for i, texture_name in enumerate(self.texture_definitions.keys()):
            texture_node = material.node_tree.nodes.new('ShaderNodeTexImage')
            texture_path = Path(self.textures[texture_name])
            texture = self.get_texture(texture_path)
            if texture is not None:
                texture_node.image = texture
                if "Norm" in texture_name or "Metal" in texture_name or "Height" in texture_name:
                    texture_node.image.colorspace_settings.name = 'Non-Color'
            texture_node.name = texture_name
            texture_node.label = texture_name
            texture_node.location.x -= 4 * positioning_unit[0] - positioning_offset[0]
            texture_node.location.y -= i * positioning_unit[1] - positioning_offset[1]

            texture_node.anno_properties.enabled = self.texture_enabled[texture_name]
            extension = texture_path.suffix
            if extension not in [".png", ".psd"]:
                if texture_path != Path(""):
                    print("Warning: Unsupported texture file extension", extension, texture_path)
                extension = ".psd"
            texture_node.anno_properties.original_file_extension = extension
        
        node_tree = material.node_tree
        links = node_tree.links
        nodes = node_tree.nodes
        
        anno_shader = self.add_anno_shader(nodes)
        material.node_tree.nodes.remove(nodes["Principled BSDF"])
        
        emissive_color = self.add_shader_node(node_tree, "ShaderNodeCombineColor",
                            name = "cEmissiveColor",
                            mode = "RGB",
                            position = (3, 6.5),
                            default_inputs = {
                                "Red": self.colors["cEmissiveColor"][0],
                                "Green": self.colors["cEmissiveColor"][1],
                                "Blue": self.colors["cEmissiveColor"][2],
                            },
                            inputs = {}
        )
        c_diffuse_mult = self.add_shader_node(node_tree, "ShaderNodeCombineColor",
                            name = "cDiffuseColor",
                            mode = "RGB",
                            position = (2, 6.5),
                            default_inputs = {
                                "Red": self.colors["cDiffuseColor"][0],
                                "Green": self.colors["cDiffuseColor"][1],
                                "Blue": self.colors["cDiffuseColor"][2],
                            },
                            inputs = {}
        )
        
        links.new(anno_shader.inputs["cDiffuse"], nodes[self.texture_names["diffuse"]].outputs[0])
        links.new(anno_shader.inputs["cNormal"], nodes[self.texture_names["normal"]].outputs[0])
        links.new(anno_shader.inputs["cMetallic"], nodes[self.texture_names["metallic"]].outputs[0])
        links.new(anno_shader.inputs["cHeight"], nodes[self.texture_names["height"]].outputs[0])
        links.new(anno_shader.inputs["cNightGlow"], nodes[self.texture_names["night_glow"]].outputs[0])
        links.new(anno_shader.inputs["cDyeMask"], nodes[self.texture_names["dye"]].outputs[0])
        
        links.new(anno_shader.inputs["cDiffuseMultiplier"], c_diffuse_mult.outputs[0])
        links.new(anno_shader.inputs["cEmissiveColor"], emissive_color.outputs[0])
        
        links.new(anno_shader.inputs["Alpha"], nodes[self.texture_names["diffuse"]].outputs["Alpha"])
        links.new(anno_shader.inputs["Glossiness"], nodes[self.texture_names["normal"]].outputs["Alpha"])
        
        
        links.new(nodes["Material Output"].inputs["Surface"], anno_shader.outputs["Shader"])
        
        
        
        material.surface_render_method = "DITHERED"

        
        #Store all kinds of properties for export
        for prop, value in self.custom_properties.items():
            material[prop] = value


        Material.materialCache[self.get_material_cache_key()] = material
        return material
    
    def add_shader_node_to_material(self, material, node_type, **kwargs):
        nodes = material.node_tree
        return self.add_shader_node(nodes, node_type, **kwargs)
###################################################################################################################

class ClothMaterial(Material):
    texture_definitions = {
        "cClothDiffuseTex":"DIFFUSE_ENABLED",
        "cClothNormalTex":"NORMAL_ENABLED",
        "cClothMetallicTex":"METALLIC_TEX_ENABLED",
        "cSeparateAOTex":"SEPARATE_AO_TEXTURE",
        "cHeightMap":"HEIGHT_MAP_ENABLED",
        "cNightGlowMap":"NIGHT_GLOW_ENABLED", 
        "cClothDyeMask":"DYE_MASK_ENABLED"
    }
    texture_names = {
        "diffuse":"cClothDiffuseTex",
        "normal":"cClothNormalTex",
        "metallic":"cClothMetallicTex",
        "ambient":"cSeparateAOTex",
        "height":"cHeightMap",
        "night_glow":"cNightGlowMap",
        "dye":"cClothDyeMask",
    }