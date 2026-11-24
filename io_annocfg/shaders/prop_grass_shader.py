import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

from ..utils import to_data_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences

class GrassPropShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "GrassPropShader"
        self.compose(PropBasicDiffuseComponent())
        self.compose(GrassAdditionalComponent())
        self.compose(PropBackfaceComponent())
        self.add_link(FlagLink("Flip Backface Normal", "cFlipBackfaceNormal"))

        # override default vertexformat
        self.material_properties.clear()


    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")