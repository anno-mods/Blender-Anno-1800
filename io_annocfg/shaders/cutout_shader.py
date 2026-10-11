from .shader_base import AnnoBasicShader
from .default_shader import AnnoDefaultShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

class CutoutShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()
        self.shader_id = "AnnoCutoutShader"        
        self.material_properties["NumBonesPerVertex"] = "0"
        self.add_link(EnumLink("VertexFormat", "VertexFormat", { "Standard (P4h_N4b_G4b_B4b_T2h)": "P4h" }))
        self.material_properties["ShaderID"] = "5"

        self.compose(CutoutComponent())
        self.compose(TerrainAdaptionShaderComponent())
        self.add_link(FlagLink("Disable Revive Distance", "DisableReviveDistance"))

    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()