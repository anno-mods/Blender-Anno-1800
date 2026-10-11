from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

class MockupShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()
        self.shader_id = "AnnoMockupShader"
        self.compose(VertexFormatShaderComponent())
        self.material_properties["ShaderID"] = "18"
        self.compose(SimpleColorComponent())

    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()
        template = ShaderTemplate(anno_shader)
        template.direct_link("Color", "Base Color")
        template.direct_link("Metallic", "Metallic")
        template.add_gloss("Glossiness")