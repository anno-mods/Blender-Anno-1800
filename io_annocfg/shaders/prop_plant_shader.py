import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

from ..utils import to_data_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences

class PlantPropShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "PlantPropShader"
        self.compose(PropPlantDiffNormComponent())
        self.add_link(FlagLink("Disable Plant Glossiness", "DISABLE_PLANT_GLOSSINESS"))        
        self.add_link(FlagLink("Fadeout Shadow", "FADE_OUT_SHADOW"))  
        self.compose(PropBackfaceComponent())
        self.compose(PropTransparencyComponent())
        self.compose(PropWindComponent())
        self.compose(PropTiledTintComponent())
        self.compose(PropTerrainAdaptionComponent())
        self.compose(PropYetAnotherTerrainTintComponent())
        self.compose(PropShadowNoiseComponent())
        self.compose(PropShinySpotsComponent())

        # override default vertexformat
        self.material_properties.clear()


    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")
        shader_template.add_normal("cNormal")
        shader_template.add_gloss("Glossiness")