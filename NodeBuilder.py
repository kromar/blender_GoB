

"""
The purpose of this module is to create a material node that can translate the zbrush setup into a blender node material.
The material can contain a diffuse texture a normal map and a displacement map.

    - create node types
        - output
        - shader
        - displacement map (non_color / Linear)
        - normal map (non_color)
        - image texture (Linear
"""

"""    
ShaderNodeOutputMaterial
ShaderNodeBsdfPrincipled    
ShaderNodeTexImage
ShaderNodeNormalMap
ShaderNodeDisplacement
"""


import bpy


class BuildNodes(bpy.types.Operator):
    bl_idname = "scene.nodebuilder"
    bl_label = "build nodes"
    bl_description = "buidling node trees"
    def __init__(self, node_label='', material=None, pos_x=0, pos_y=0, node_width=400,
                 node_input=None, node_output=None, texture_image=None, node_color=(0.5, 0.5, 0.5)):

        self.material = material
        self.node_label = node_label
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_width = node_width
        self.node_input = node_input
        self.node_output = node_output
        self.texture_image = texture_image
        self.node_color = node_color

        self.normal_node = None
        self.displacement_node = None
        self.texture_node = None
        self.shader_node = None
        self.output_node = None

        # enable nodes
        if not self.material.use_nodes:
            self.material.use_nodes = True
        self.nodes = self.material.node_tree.nodes



    def create_output_node(self):
        if 'ShaderNodeOutputMaterial' not in [node.bl_idname for node in self.nodes]:
            self.output_node = self.nodes.new('ShaderNodeOutputMaterial')
            self.output_node.location = self.pos_x, self.pos_y

    def create_shader_node(self, pos_x=-300, pos_y=400):
        self.pos_x = pos_x
        self.pos_y = pos_y
        if 'ShaderNodeBsdfPrincipled' not in [node.bl_idname for node in self.nodes]:
            self.shader_node = self.nodes.new('ShaderNodeBsdfPrincipled')
            self.shader_node.location = self.pos_x, self.pos_y
            #self.material.node_tree.links.new(self.output_node.inputs[0], self.shader_node.outputs[0])

    def create_texture_node(self, texture_image=None, node_label='', node_color=(0.5, 0.5, 0.5), pos_x=-1200, pos_y=0):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_label = node_label
        self.texture_image = texture_image
        self.node_color = node_color

        if 'ShaderNodeTexImage' not in [node.bl_idname for node in self.nodes] \
                and self.node_label not in [node.label for node in self.nodes]:
            self.texture_node = self.nodes.new('ShaderNodeTexImage')
            self.texture_node.location = self.pos_x, self.pos_y
            self.texture_node.label = self.node_label
            self.texture_node.image = self.texture_image.image
            self.texture_node.width = self.node_width
            self.texture_node.use_custom_color = True
            self.texture_node.color = self.node_color

        link_nodes(self)
        #TODO: make it possible to define what needs to be connected, probably create a node connecter makes sense
        #self.material.node_tree.links.new(self.shader_node.inputs[0], self.texture_node.outputs[0])

    def create_normal_node(self, node_color=(0.5, 0.5, 1.0), pos_x=-650, pos_y=-400):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_color = node_color

        if 'ShaderNodeNormalMap' in [node.bl_idname for node in self.nodes]:
            print('node already exists!')
        else:
            self.normal_node = self.nodes.new('ShaderNodeNormalMap')
            self.normal_node.location = self.pos_x, self.pos_y
            self.normal_node.use_custom_color = True
            self.normal_node.color = self.node_color

            #self.nodetree.links.new(self.shader_node.inputs[19], self.normal_node.outputs[0])  # TODO: find index by input name

            """
            self.txtNmp_node = nodes.new('ShaderNodeTexImage')
            self.txtNmp_node.location = -800, -300
            self.txtNmp_node.image = txtNmp.image
            self.txtNmp_node.width = 400
            self.txtNmp_node.color_space = 'NONE'
            self.txtNmp_node.interpolation = 'Smart'
            self.material.node_tree.links.new(self.normal_node.inputs[1], self.txtNmp_node.outputs[0])
            """

    def create_displacement_node(self, node_color=(0.8, 0.3, 0.3), pos_x=-300, pos_y=-600):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_color = node_color

        if 'ShaderNodeDisplacement' in [node.bl_idname for node in self.nodes]:
            print('node already exists!')
        else:
            self.displacement_node = self.nodes.new('ShaderNodeDisplacement')
            self.displacement_node.location = self.pos_x, self.pos_y
            self.displacement_node.use_custom_color = True
            self.displacement_node.color = self.node_color

            #self.nodetree.links.new(self.output_node.inputs[2], self.displacement_node.outputs[0])

            """ create this part in create_textureimage_node
            self.txtDisp_node = nodes.new('ShaderNodeTexImage')
            self.txtDisp_node.location = -800, -600
            self.txtDisp_node.image = txtDisp.image
            self.txtDisp_node.width = 400
            self.txtDisp_node.interpolation = 'Smart'
            self.material.node_tree.links.new(self.displacement_node.inputs[0], self.txtDisp_node.outputs[0])
            """


def link_nodes(self):
    """
    connections to establish:
    Image Texture (Color)                                               --> (Base Color) Principled BSDF (BSDF)       -->  (Surface) Material Output
    Image Texture (Color)   --> (Color) Normal Map (Normal)             --> (Normal) Principled BSDF
    Image Texture (Color)   --> (Height) Displacement (Displacement)                                                   -->  (Displacement) Material Output
    """

    for node in self.nodes:
        print(node.bl_idname)
        if node.bl_idname == 'ShaderNodeTexImage':
            print("Texture node Labels:", node.label)
            '''still need to check for the type, can the label be used?'''
            pass
        elif node.bl_idname == 'ShaderNodeNormalMap':
            pass
        elif node.bl_idname == 'ShaderNodeDisplacement':
            pass
        elif node.bl_idname == 'ShaderNodeOutputMaterial':
            pass
        elif node.bl_idname == 'ShaderNodeBsdfPrincipled':
            for idx, i in enumerate(node.inputs):
                print("inputs: ", idx, i.name)
                if i.name == 'Base Color':
                    return node.inputs[idx]
                elif i.name == 'Normal':
                    return node.inputs[idx]
            for idx, o in enumerate(node.outputs):
                print("outputs: ", idx, o)
                if o.name == 'BSDF':
                    return node.outputs[idx]



    #self.material.node_tree.links.new(self.output_node.inputs[0], self.shader_node.outputs[0])
    #self.material.node_tree.links.new(self.shader_node.inputs[0], self.texture_node.outputs[0])

    #self.nodetree.links.new(self.shader_node.inputs[19], self.normal_node.outputs[0])
    #self.nodetree.links.new(self.output_node.inputs[2], self.displacement_node.outputs[0])


def align_nodes(self):

    # if mat.use_nodes:
    #     ntree = mat.node_tree
    #     node = ntree.nodes.get("Diffuse BSDF", None)
    #     if node is not None:
    #         print("We Found:", node)

    # output_node = nodes.get('Material Output')
    # shader_node = nodes.get('Principled BSDF')

    # TODO: trace color node to input of output node
    #txtdiff_node = nodes.get('ShaderNodeTexImage')
    # for node_input in output_node.inputs:
    #     print("node inputs: ", input)
    #     if (node_input.name == 'Base Color' or node_input.name == 'Color') and node_input.links:
    #         pass
    #     if node_input.name == 'Normal' and node_input.links:
    #         pass
    #     if node_input.name == 'Color' and node_input.links:
    #         pass
    #
    #     if node_input.name == 'Height' and node_input.links:
    #         pass


    pass

