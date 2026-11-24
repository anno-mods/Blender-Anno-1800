import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

from ..utils import to_data_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences

class TerrainPropShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "TerrainPropShader"
        self.compose(PropBasicDiffNormComponent())
        self.add_link(FlagLink("Linear Shadow Interpolation", "LINEAR_SHADOW_INTERPOLATION_ENABLED"))
        self.compose(TerrainIntegrationComponent())
        self.compose(TerrainMaterialComponent())

        # override default vertexformat
        self.material_properties.clear()


    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")
        shader_template.add_normal("cNormal")
        shader_template.add_gloss("Glossiness")