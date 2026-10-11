class ShaderTemplate:
    def __init__(self, anno_shader):
        self.anno_shader = anno_shader
        self.inputs = self.add_shader_node(self.anno_shader, "NodeGroupInput", 
                                        position = (0, 0), 
                                    ).outputs

        self.bdsf = self.add_shader_node(self.anno_shader, "ShaderNodeBsdfPrincipled", 
                                        position = (4, 0), 
                                        default_inputs = {
                                            "Alpha": 1.0,
                                            "Emission Strength" : 0.0
                                        },
                                    )

        self.outputs = self.add_shader_node(self.anno_shader, "NodeGroupOutput", 
                                position = (5, 0), 
                                inputs = {
                                    "Shader" : self.bdsf.outputs["BSDF"]
                                },
                            )

    def direct_link(self, input_key, bdsf_key):
        self.anno_shader.links.new(self.bdsf.inputs[bdsf_key], self.inputs[input_key])

    def add_diffuse(self, diffuse_key, diffuse_multiplier_key):
        # Mixes Diffuse and cDiffuse
        mix_c_diffuse = self.add_shader_node(self.anno_shader, "ShaderNodeMixRGB",
                                        position = (1, 4),
                                        default_inputs = {
                                            0 : 1.0,
                                        },
                                        inputs = {
                                            "Color1" : self.inputs[diffuse_multiplier_key],
                                            "Color2" : self.inputs[diffuse_key],
                                        },
                                        blend_type = "MULTIPLY",
                                    )

        final_diffuse = self.add_shader_node(self.anno_shader, "ShaderNodeMixRGB",
                                    position = (2, 3),
                                    default_inputs = {
                                        "Color2" : (1.0, 1.0, 1.0, 1.0),
                                        "Fac" : 1.0
                                    },
                                    inputs = {
                                        "Color1" : mix_c_diffuse.outputs["Color"],
                                    },
                                    blend_type = "MULTIPLY",
                                )
        self.anno_shader.links.new(self.bdsf.inputs["Base Color"], final_diffuse.outputs["Color"])
        self.anno_shader.links.new(self.bdsf.inputs["Alpha"], self.inputs["Alpha"])
        return final_diffuse 

    def add_dye(self, diffuse):
        dye_mask = self.add_shader_node(self.anno_shader, "ShaderNodeRGBToBW",
                                    position = (1, 3),
                                    inputs = {
                                        "Color" : self.inputs["cDyeMask"],
                                    },
                    )
        
        self.anno_shader.links.new(diffuse.inputs["Fac"], dye_mask.outputs["Val"])
        return dye_mask

    def add_normal(self, normal_key, add_height = False):
        #Normals
        separate_normal = self.add_shader_node(self.anno_shader, "ShaderNodeSeparateColor",
                                        position = (1, 2),
                                        mode = "RGB",
                                        inputs = {
                                            "Color" : self.inputs[normal_key],
                                        },
                                    )
        #Calc normal blue
        square_x = self.add_shader_node(self.anno_shader, "ShaderNodeMath",
                                        position = (2, 1.5),
                                        operation = "POWER",
                                        inputs = {
                                            0 : separate_normal.outputs["Red"],
                                        },
                                        default_inputs = {
                                            1 : 2.0
                                        },
                                    )
        square_y = self.add_shader_node(self.anno_shader, "ShaderNodeMath",
                                        position = (2, 2.5),
                                        operation = "POWER",
                                        inputs = {
                                            0 : separate_normal.outputs["Green"],
                                        },
                                        default_inputs = {
                                            1 : 2.0
                                        },
                                    )
        add_squares = self.add_shader_node(self.anno_shader, "ShaderNodeMath",
                                        position = (2.5, 2),
                                        operation = "ADD",
                                        inputs = {
                                            0 : square_x.outputs["Value"],
                                            1 : square_y.outputs["Value"],
                                        },
                                    )
        inverted_add_squares = self.add_shader_node(self.anno_shader, "ShaderNodeMath",
                                        position = (3, 2),
                                        operation = "SUBTRACT",
                                        inputs = {
                                            1 : add_squares.outputs["Value"],
                                        },
                                        default_inputs = {
                                            0 : 1.0
                                        },
                                    )
        normal_blue = self.add_shader_node(self.anno_shader, "ShaderNodeMath",
                                        position = (3.5, 2),
                                        operation = "SQRT",
                                        inputs = {
                                            0 : inverted_add_squares.outputs["Value"],
                                        },
                                    )
        
        combine_normal = self.add_shader_node(self.anno_shader, "ShaderNodeCombineColor",
                                        position = (4, 2),
                                        mode = "RGB",
                                        inputs = {
                                            "Red" : separate_normal.outputs["Red"],
                                            "Green" : separate_normal.outputs["Green"],
                                            "Blue" : normal_blue.outputs["Value"],
                                        },
                                    )
        normal_map = self.add_shader_node(self.anno_shader, "ShaderNodeNormalMap",
                                        position = (5, 2),
                                        default_inputs = {
                                            0 : 0.5,
                                        },
                                        inputs = {
                                            "Color" : combine_normal.outputs["Color"],
                                        },
                                    )
        bump_map = None
        if add_height:
            height_bw = self.add_shader_node(self.anno_shader, "ShaderNodeRGBToBW",
                                            position = (5, 3),
                                            inputs = {
                                                "Color" : self.inputs["cHeight"],
                                            },
                                        )
            bump_map = self.add_shader_node(self.anno_shader, "ShaderNodeBump",
                                            position = (6, 2),
                                            default_inputs = {
                                                0 : 0.5,
                                            },
                                            inputs = {
                                                "Height" : height_bw.outputs["Val"],
                                                "Normal" : normal_map.outputs["Normal"],
                                            },
                                        )
        else: 
            bump_map = self.add_shader_node(self.anno_shader, "ShaderNodeBump",
                                            position = (6, 2),
                                            default_inputs = {
                                                0 : 0.5,
                                            },
                                            inputs = {
                                                "Normal" : normal_map.outputs["Normal"],
                                            },
                                        )
        self.anno_shader.links.new(self.bdsf.inputs["Normal"], bump_map.outputs["Normal"])
        return bump_map

    def add_gloss(self, gloss_key):
        roughness = self.add_shader_node(self.anno_shader, "ShaderNodeMath",
                        position = (3, 0),
                        operation = "SUBTRACT",
                        inputs = {
                            1 : self.inputs[gloss_key],
                        },
                        default_inputs = {
                            0 : 1.0
                        },
                    )
        
        self.anno_shader.links.new(self.bdsf.inputs["Roughness"], roughness.outputs["Value"])

    def add_metallic(self, metallic_key):
        metallic = self.add_shader_node(self.anno_shader, "ShaderNodeRGBToBW",
                                position = (1, 3),
                                inputs = {
                                    "Color" : self.inputs[metallic_key],
                                },
                            )
        
        self.anno_shader.links.new(self.bdsf.inputs["Metallic"], metallic.outputs["Val"])

    def add_emission(self, diffuse, emission_key, night_glow_key):
        
        #Emission
        scaled_emissive_color = self.add_shader_node(self.anno_shader, "ShaderNodeVectorMath",         
                            operation = "SCALE",
                            name = "EmissionScale",
                            position = (1, -1),
                            default_inputs = {
                                "Scale": 10.0,
                            },
                            inputs = {
                                "Vector" : self.inputs[emission_key],
                            }
        )
        combined_emissive_color = self.add_shader_node(self.anno_shader, "ShaderNodeVectorMath",         
                            operation = "MULTIPLY",
                            position = (2, -1),
                            inputs = {
                                0 : diffuse.outputs["Color"],
                                1 : scaled_emissive_color.outputs["Vector"],
                            }
        )
        object_info = self.add_shader_node(self.anno_shader, "ShaderNodeObjectInfo",         
                            position = (1, -2),
        )
        random_0_1 = self.add_shader_node(self.anno_shader, "ShaderNodeMath",  
                            operation = "FRACT",   
                            position = (2, -2),
                            inputs = {
                                "Value" : object_info.outputs["Location"],
                            }
        )
        color_ramp_node = self.add_shader_node(self.anno_shader, "ShaderNodeValToRGB",  
                            position = (3, -2),
                            inputs = {
                                "Fac" : random_0_1.outputs["Value"],
                            }
        )

        color_ramp = color_ramp_node.color_ramp
        color_ramp.elements[0].color = (1.0, 0.0, 0.0,1)
        color_ramp.elements[1].position = (2.0/3.0)
        color_ramp.elements[1].color = (0.0, 0.0, 1.0,1)
        
        color_ramp.elements.new(1.0/3.0)
        color_ramp.elements[1].color = (0.0, 1.0, 0.0,1)
        color_ramp.interpolation = "CONSTANT"
        
        location_masked_emission = self.add_shader_node(self.anno_shader, "ShaderNodeVectorMath",         
                            operation = "MULTIPLY",
                            position = (4, -2),
                            inputs = {
                                0 : color_ramp_node.outputs["Color"],
                                1 : self.inputs[night_glow_key],
                            }
        )
        
        final_emission_color = self.add_shader_node(self.anno_shader, "ShaderNodeMixRGB",         
                            blend_type = "MIX",
                            position = (5, -1),
                            default_inputs = {
                                "Color1" : (0.0, 0.0 ,0.0, 1.0)
                            },
                            inputs = {
                                "Fac" : location_masked_emission.outputs["Vector"],
                                "Color2" : combined_emissive_color.outputs["Vector"],
                            }
        )

        self.anno_shader.links.new(self.bdsf.inputs["Emission Color"], final_emission_color.outputs["Color"])
    
        
    def add_shader_node(self, node_tree, node_type, **kwargs):
        node = node_tree.nodes.new(node_type)
        positioning_unit = (300, 300)
        positioning_offset = (0, 3 * positioning_unit[1])
        x,y = kwargs.pop("position", (0,0))
        node.location.x = x* positioning_unit[0] - positioning_offset[0]
        node.location.y = y* positioning_unit[1] - positioning_offset[1]

        if "name" in kwargs and not "label" in kwargs:
            kwargs["label"] = kwargs["name"]

        for input_key, default_value in kwargs.pop("default_inputs", {}).items():
            print(input_key)

            nodeinput = None
            if type(input_key) is int: 
                nodeinput = node.inputs[input_key]
            elif type(input_key) is str:
                nodeinput = node.inputs.get(input_key)

            if(nodeinput is None):
                print("We aren't allowed to use this as a defaultInput: " + node_type + " | " + input_key)
                continue
            nodeinput.default_value = default_value

        for input_key, input_connector in kwargs.pop("inputs", {}).items():
                node_tree.links.new(node.inputs[input_key], input_connector)

        for attr, value in kwargs.items():
            setattr(node, attr, value)

        return node