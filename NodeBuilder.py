

"""
The purpose of this module is to create a material node that can translate the zbrush setup into a blender node material.
The material can contain a diffuse texture a normal map and a displacement map.

    - create node material

    - create node types
        - output
        - shader
        - displacement map
        - normal map
        - image texture

    - connect node types

    - configure nodes
        - define the input for the node treee

    - test integrity of node tree
"""
import bpy

class CreateNodeMaterial():
    pass


class CreateNodes():
    pass


class ConnectNodes():
    pass


class ConfigureNodes():
    pass


class TestNodes():
    def __init__(self, name = None):
        self.name = name
        print("my name is ", name)


        #if not mat.use_nodes:
        #   mat.use_nodes = True


class BuildNodes(bpy.types.Operator):
    bl_idname = "scene.nodebuilder"
    bl_label = "build nodes"
    bl_description = "buidling node trees"
    def __init__(self, node_name=None, material=None, node_pos_x=0, node_pos_y=0, node_width = 400,
                 node_input=None, node_output=None, texture_image=None):

        self.node_name = node_name
        self.material = material
        self.node_pos_x = node_pos_x
        self.node_pos_y = node_pos_y
        self.node_width = node_width
        self.node_input = node_input
        self.node_output = node_output
        self.texture_image = texture_image

        self.normal_node = None
        self.displacement_node = None
        self.textureimage_node = None
        self.mynode = None
        self.output_node = None
        print("self.material:", self.material)
        self.nodes = self.material.node_tree.nodes



    def create_output_node(self):
        self.output_node = self.nodes.new('ShaderNodeOutputMaterial')
        self.output_node.location = self.node_pos_x, self.node_pos_y

    def create_shader_node(self):
        self.mynode = self.nodes.new('ShaderNodeBsdfPrincipled')
        self.mynode.location = self.node_pos_x, self.node_pos_y
        self.material.node_tree.links.new(self.mat_node.inputs[0], self.mynode.outputs[0])


    def create_textureimage_node(self):
        self.textureimage_node = self.nodes.new('ShaderNodeTexImage')
        self.textureimage_node.location = self.node_pos_x, self.node_pos_y
        self.textureimage_node.image = self.texture_image.image
        self.textureimage_node.width = self.node_width
        self.textureimage_node.interpolation = 'Smart'
        self.material.node_tree.links.new(self.shader_node.inputs[0], self.textureimage_node.outputs[0])

    def create_normal_node(self):
        self.normal_node = self.nodes.new('ShaderNodeNormalMap')
        self.normal_node.location = self.node_pos_x, self.node_pos_y
        self.material.node_tree.links.new(self.shader_node.inputs[17], self.normal_node.outputs[0])  # TODO: find index by input name

        """
        self.txtNmp_node = nodes.new('ShaderNodeTexImage')
        self.txtNmp_node.location = -800, -300
        self.txtNmp_node.image = txtNmp.image
        self.txtNmp_node.width = 400
        self.txtNmp_node.color_space = 'NONE'
        self.txtNmp_node.interpolation = 'Smart'
        self.material.node_tree.links.new(self.normal_node.inputs[1], self.txtNmp_node.outputs[0])
        """

    def create_displacement_node(self):
        self.displacement_node = self.nodes.new('ShaderNodeDisplacement')
        self.displacement_node.location = self.node_pos_x, self.node_pos_y
        self.material.node_tree.links.new(self.mat_node.inputs[2], self.displacement_node.outputs[0])

        """ create this part in create_textureimage_node
        self.txtDisp_node = nodes.new('ShaderNodeTexImage')
        self.txtDisp_node.location = -800, -600
        self.txtDisp_node.image = txtDisp.image
        self.txtDisp_node.width = 400
        self.txtDisp_node.interpolation = 'Smart'
        self.material.node_tree.links.new(self.displacement_node.inputs[0], self.txtDisp_node.outputs[0])
        """

    def align_nodes(self):
        pass





