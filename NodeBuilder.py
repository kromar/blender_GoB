

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
    def __init__(self, node_name=None, material=None, pos_x=0, pos_y=0, node_width=400,
                 node_input=None, node_output=None, texture_image=None):

        self.node_name = node_name
        self.material = material
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_width = node_width
        self.node_input = node_input
        self.node_output = node_output
        self.texture_image = texture_image

        self.normal_node = None
        self.displacement_node = None
        self.textureimage_node = None
        self.shader_node = None
        self.output_node = None
        print("self.material:", self.material)

        # enable nodes
        if not self.material.use_nodes:
            self.material.use_nodes = True
        self.nodetree = self.material.node_tree
        self.nodes = self.nodetree.nodes

        """
        ## node.bl_idname
    
        ShaderNodeOutputMaterial
        ShaderNodeBsdfPrincipled
    
        ShaderNodeTexImage
        ShaderNodeNormalMap
        ShaderNodeDisplacement
        """

        # if mat.use_nodes:
        #     ntree = mat.node_tree
        #     node = ntree.nodes.get("Diffuse BSDF", None)
        #     if node is not None:
        #         print("We Found:", node)


    def create_output_node(self):
        if 'ShaderNodeOutputMaterial' in [node.bl_idname for node in self.nodes]:
            print('node already exists!')
        else:
            self.output_node = self.nodes.new('ShaderNodeOutputMaterial')
            self.output_node.location = self.pos_x, self.pos_y


    def create_shader_node(self, pos_x=-400, pos_y=0):
        self.pos_x = pos_x
        self.pos_y = pos_y
        if 'ShaderNodeBsdfPrincipled' in [node.bl_idname for node in self.nodes]:
            print('node already exists!')
        else:
            self.shader_node = self.nodes.new('ShaderNodeBsdfPrincipled')
            self.shader_node.location = self.pos_x, self.pos_y
            #self.nodetree.links.new(self.output_node.inputs[0], self.shader_node.outputs[0])

    def create_textureimage_node(self, texture_image=None, pos_x=-1200, pos_y=0):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.texture_image = texture_image

        if 'ShaderNodeTexImage' in [node.bl_idname for node in self.nodes]:
            print('node already exists!')
        else:
            self.textureimage_node = self.nodes.new('ShaderNodeTexImage')
            self.textureimage_node.location = self.pos_x, self.pos_y
            self.textureimage_node.image = self.texture_image.image
            self.textureimage_node.width = self.node_width

            #TODO: make it possible to define what needs to be connected, probably create a node connecter makes sense
            #self.nodetree.links.new(self.shader_node.inputs[0], self.textureimage_node.outputs[0])

    def create_normal_node(self, pos_x=-650, pos_y=-400):
        self.pos_x = pos_x
        self.pos_y = pos_y

        if 'ShaderNodeNormalMap' in [node.bl_idname for node in self.nodes]:
            print('node already exists!')
        else:
            self.normal_node = self.nodes.new('ShaderNodeNormalMap')
            self.normal_node.location = self.pos_x, self.pos_y

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

    def create_displacement_node(self, pos_x=-300, pos_y=-600):
        self.pos_x = pos_x
        self.pos_y = pos_y
        if 'ShaderNodeDisplacement' in [node.bl_idname for node in self.nodes]:
            print('node already exists!')
        else:
            self.displacement_node = self.nodes.new('ShaderNodeDisplacement')
            self.displacement_node.location = self.pos_x, self.pos_y
            #self.nodetree.links.new(self.output_node.inputs[2], self.displacement_node.outputs[0])

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





