import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

class GlassShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "AnnoGlassShader"
        
        self.add_link(ColorLink("Tint Color", "cTintColor"))
        self.add_link(FloatLink("Glass Distortion", "cGlassDistortion"))
        self.add_link(FloatLink("Glass Reflectivity", "cGlassReflectivity"))
        self.compose(VertexFormatShaderComponent())
        self.compose(DefaultShaderFakeComponent())
        self.compose(CommonShaderComponent())
        self.compose(TerrainAdaptionShaderComponent())
        self.compose(EnvironmentShaderComponent())

        # override default vertexformat
        self.material_properties["ShaderID"] = "2"

    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
                
        shader_template = ShaderTemplate(anno_shader)
        diff = shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")