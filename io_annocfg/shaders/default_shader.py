from enum import Enum
from tokenize import String

import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

from ..utils import to_data_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences

class AnnoDefaultShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "AnnoDefaultShader"       
        self.compose(VertexFormatShaderComponent())
        self.compose(DefaultShaderFakeComponent())
        self.compose(CommonShaderComponent())
        self.compose(DyeMaskTexScrollShaderComponent())
        self.compose(AdditionalPBRShaderComponent())
        self.compose(TerrainAdaptionShaderComponent())
        self.compose(EnvironmentShaderComponent())
        self.compose(GlowShaderComponent())

        # override default vertexformat
        self.material_properties["ShaderID"] = "8"

    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        diff = shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")
        shader_template.add_dye(diff)
        shader_template.add_normal("cNormal", add_height=True)
        shader_template.add_gloss("Glossiness")
        shader_template.add_metallic("cMetallic")
        shader_template.add_emission(diff, "cEmissiveColor", "cNightGlow")