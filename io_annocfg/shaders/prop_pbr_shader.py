import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

from ..utils import to_data_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences

class SimplePBRPropShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "SimplePBRPropShader"

        self.compose(DefaultPropComponent())
        self.compose(CommonShaderComponent())
        self.compose(DyeMaskTexScrollShaderComponent())
        self.compose(AdditionalPBRShaderComponent())
        self.compose(TerrainAdaptionShaderComponent())
        self.compose(EnvironmentShaderComponent())
        self.compose(GlowShaderComponent())
        self.add_link(FlagLink("Force Alphablending", "FORCE_ALPHA_BLEND"))
        self.add_link(FlagLink("Disable Revive Distance", "DisableReviveDistance"))

        # override default vertexformat
        self.material_properties.clear()

    def create_anno_shader(self):
       
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        diff = shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")
        shader_template.add_dye(diff)
        shader_template.add_normal("cNormal")
        shader_template.add_gloss("Glossiness")
        shader_template.add_metallic("cMetallic")
        shader_template.add_emission(diff, "cEmissiveColor", "cNightGlow")