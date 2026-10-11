from .shader_node_templates import ShaderTemplate

from .default_shader import AnnoBasicShader
from .shader_components import AdditionalPBRShaderComponent, CommonShaderComponent, DefaultShaderFakeComponent, DyeMaskTexScrollShaderComponent, EnumLink, EnvironmentShaderComponent, GlowShaderComponent, IntegerLink, StringLink, TerrainAdaptionShaderComponent

class DecalShader(AnnoBasicShader):
    def __init__(self):
        super().__init__()
        self.shader_id = "AnnoDecalShader"
        self.material_properties["ShaderID"] = "1"        
        self.material_properties["NumBonesPerVertex"] = "0"
        self.add_link(EnumLink("VertexFormat", "VertexFormat", { "Decal (P3f_N3f_G3f_T2f_T1f_T1f_T1f)": "P3f_N3f_G3f_T2f_T1f_T1f_T1f" }))
        self.compose(DefaultShaderFakeComponent())
        self.compose(CommonShaderComponent())
        self.compose(DyeMaskTexScrollShaderComponent())
        self.compose(AdditionalPBRShaderComponent())
        self.compose(TerrainAdaptionShaderComponent())
        self.compose(EnvironmentShaderComponent())
        self.compose(GlowShaderComponent())

    def create_anno_shader(self):
        anno_shader = self.setup_empty_shader()                
        shader_template = ShaderTemplate(anno_shader)
        diff = shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")
        shader_template.add_dye(diff)
        shader_template.add_normal("cNormal", add_height=True)
        shader_template.add_gloss("Glossiness")
        shader_template.add_metallic("cMetallic")
        shader_template.add_emission(diff, "cEmissiveColor", "cNightGlow")