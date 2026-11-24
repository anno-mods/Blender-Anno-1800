import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

class LiquidShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "AnnoLiquidShader"
        self.add_link(IntegerLink("NumBonesPerVertex", "NumBonesPerVertex", 0))
        self.compose(LiquidStandardComponent())
        self.compose(FlowMapComponent())
        self.compose(OceanWaveComponent())
        self.compose(DetailMapComponent())
        self.compose(CommonShaderComponent())
        self.compose(TerrainAdaptionShaderComponent())
        self.compose(EnvironmentShaderComponent())
        self.add_link(FlagLink("Disable Revive Distance", "DisableReviveDistance"))

        # override default vertexformat
        self.material_properties["VertexFormat"] = "P4h_N4b_G4b_B4b_T2h"
        self.material_properties["ShaderID"] = "7"

    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        diff = shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")