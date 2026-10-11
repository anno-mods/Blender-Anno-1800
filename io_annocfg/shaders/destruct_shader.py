import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

from ..utils import to_data_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences

class DestructShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "AnnoDestructShader"
        
        self.add_link(FlagLink("Enable Texture Atlas", "TEXTURE_ATLAS_ENABLED"))
        self.compose(VertexFormatShaderComponent())
        self.compose(DefaultShaderFakeComponent())
        self.compose(CommonShaderComponent())
        self.compose(TerrainAdaptionShaderComponent())
        self.compose(GlowShaderComponent())

        # override default vertexformat
        self.material_properties["ShaderID"] = "6"

    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        diff = shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")
        shader_template.add_normal("cNormal")
        shader_template.add_gloss("Glossiness")
        shader_template.add_metallic("cMetallic")