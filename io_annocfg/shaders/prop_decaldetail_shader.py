import bpy
from .shader_base import AnnoBasicShader
from .shader_components import *
from .shader_node_templates import ShaderTemplate

from ..utils import to_data_path
import os
from pathlib import Path
from ..prefs import IO_AnnocfgPreferences

class DecalDetailPropShader(AnnoBasicShader):

    def __init__(self):
        super().__init__()

        self.shader_id = "DecalDetailPropShader"
        self.compose(PropBasicDiffuseComponent())

        # override default vertexformat
        self.material_properties.clear()


    def create_anno_shader(self):
        anno_shader = bpy.data.node_groups.new(self.shader_id, 'ShaderNodeTree')

        for l in self.links: 
            if not l.has_socket():
                continue

            socket = anno_shader.interface.new_socket(socket_type = l.socket_type, name = l.link_key, in_out = 'INPUT')
            l.setup_socket(anno_shader, socket)
            if l.has_default_value():
                socket.default_value = l.default_value    
        
        anno_shader.interface.new_socket(socket_type = "NodeSocketShader", name = "Shader", in_out='OUTPUT')
                
        shader_template = ShaderTemplate(anno_shader)
        shader_template.add_diffuse("cDiffuse", "cDiffuseMultiplier")