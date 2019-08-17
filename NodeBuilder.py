import bpy

## General Advices:
## ----------------
## This looks like you want to create a group of nodes directly in code.
## It might be worth to try to do a group in blender GUI, and include this blend in the addon
## (especially since it's always the same)
##
## The script can append the premade group from the blend file and then apply only the part which changes.
## This is actually similar to what I did for the Shader exporter (where I use premade nodes group).
## 
## Pseudocode:
## -----------
## Step 1: Initial Sanity Check: Are we ready to go? (what happen if we have more than one material, etc)
##         * If there are things that are missing but we can do them on runtime we do them
##         * Else we stop without attempting to go further (to avoid any potential issue)
## Step 2: Loading and connecting to the general output the premade Blender group from the blend file.
## Step 3: Adjusting the group based on the data from Zbrush.
##         * Setting up the diffuse map
##         * Checking for the normal Map
##         * Etc
##
## End General Advices
## -------------------


"""    
ShaderNodeOutputMaterial
ShaderNodeBsdfPrincipled    
ShaderNodeTexImage
ShaderNodeNormalMap
ShaderNodeDisplacement
"""


class BuildNodes(bpy.types.Operator):
    ##  access documentation with the help() function
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

    bl_idname = "scene.nodebuilder"
    bl_label = "build nodes"
    bl_description = "buidling node trees"

    def __init__(
            self,
             node_label='',
             material=None,
             pos_x=0,
             pos_y=0,
             node_width=400,
             node_input=None,
             node_output=None,
             texture_image=None,
             color_space='Raw',
             node_color=(0.5, 0.5, 0.5)):

        self.material = material
        self.node_label = node_label
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_width = node_width
        self.node_input = node_input
        self.node_output = node_output
        self.texture_image = texture_image
        self.color_space = color_space
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


class OutputNode(BuildNodes):
    """
    Is used for output nodes
    """
    def __init__(self):
        pass

    def create_output_node(self):
        if 'ShaderNodeOutputMaterial' not in [node.bl_idname for node in self.nodes]:
            self.output_node = self.nodes.new('ShaderNodeOutputMaterial')
        else:
            pass


class ShaderNode(BuildNodes):
    """
    Is used for shader nodes
    """
    def __init__(self):
        pass

    ## FIXME
    ## This is dangerous because you are changing the output node of the whole object. This can have unintended consequences
    def create_shader_node(self, output_node=None, pos_x=-300, pos_y=400):
    ## END FIXME
    ## ---------
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.output_node = output_node
        if 'ShaderNodeBsdfPrincipled' not in [node.bl_idname for node in self.nodes]:
            self.shader_node = self.nodes.new('ShaderNodeBsdfPrincipled')
            self.shader_node.location = self.pos_x, self.pos_y
        else:
            pass


class TextureNode(BuildNodes):
    """
    Is used for texture nodes
    """
    def __init__(self):
        pass
    def create_texture_node(self, texture_image=None, color_space='Raw', node_label='', node_color=(0.5, 0.5, 0.5), pos_x=-1200, pos_y=0):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_label = node_label
        self.texture_image = texture_image
        self.node_color = node_color
        self.color_space = color_space

        ## FIXME
        ## This should be in a specific method to test if a node is already existing or not
        ## ====================================================================

        if 'ShaderNodeTexImage' in [node.bl_idname for node in self.nodes] \
                and self.node_label in [node.label for node in self.nodes]:
            print("texture node already exits: ", self.node_label)
        
        ## END FIXME
        ## ---------

        else:
            print("creating texture node: ", self.node_label)
            self.texture_node = self.nodes.new('ShaderNodeTexImage')
            self.texture_node.location = self.pos_x, self.pos_y
            self.texture_node.label = self.node_label
            self.texture_node.image = self.texture_image.image
            self.texture_node.image.colorspace_settings.name = self.color_space
            self.texture_node.width = self.node_width
            self.texture_node.use_custom_color = True
            self.texture_node.color = self.node_color

        self.link_nodes(self.nodes)     #TODO: decouple from texture function


class NormalNode(BuildNodes):
    """
    Is used for normal nodes
    """
    def __init__(self):
        pass

    def create_normal_node(self, node_color=(0.5, 0.5, 1.0), pos_x=-650, pos_y=0):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_color = node_color

        if 'ShaderNodeNormalMap' not in [node.bl_idname for node in self.nodes]:
            self.normal_node = self.nodes.new('ShaderNodeNormalMap')
            self.normal_node.location = self.pos_x, self.pos_y
            self.normal_node.use_custom_color = True
            self.normal_node.color = self.node_color


class DisplacementNode(BuildNodes):
    """
    Is used for displacement nodes
    """
    def __init__(self):
        pass
    def create_displacement_node(self, node_color=(0.8, 0.3, 0.3), pos_x=-650, pos_y=-300):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.node_color = node_color

        if 'ShaderNodeDisplacement' not in [node.bl_idname for node in self.nodes]:
            self.displacement_node = self.nodes.new('ShaderNodeDisplacement')
            self.displacement_node.location = self.pos_x, self.pos_y
            self.displacement_node.use_custom_color = True
            self.displacement_node.color = self.node_color


class LinkNodes(BuildNodes):
    """
    Is used to link nodes
    """
    def __init__(self):
        pass
    def link_nodes(self, nodes):
        self.nodes = nodes
        self.diffuse_label = 'GoB_diffuse'
        self.normal_label = 'GoB_normal'
        self.displacement_label = 'GoB_displacement'
        self.shader_node = self.nodes.get('Principled BSDF')
        self.output_node = self.nodes.get('Material Output')
        self.texture_node = self.nodes.get('Image Texture')
        self.normal_node = self.nodes.get('Normal Map')
        self.displacement_node = self.nodes.get('Displacement')

        """
        connections to establish:
        Image Texture (Color)                                               --> (Base Color) Principled BSDF (BSDF)       -->  (Surface) Material Output
        Image Texture (Color)   --> (Color) Normal Map (Normal)             --> (Normal) Principled BSDF
        Image Texture (Color)   --> (Height) Displacement (Displacement)                                                   -->  (Displacement) Material Output
        """

        ## FIXME
        ## This can be replaced by a premade group (see general advice section)
        ## ====================================================================

        #connect shader node to output
        if 'ShaderNodeBsdfPrincipled' in [node.bl_idname for node in self.nodes] \
                and 'ShaderNodeOutputMaterial' in [node.bl_idname for node in self.nodes]:
            self.material.node_tree.links.new(self.shader_node.outputs[0], self.output_node.inputs[0])

        #connect displacement map to output
        if 'ShaderNodeDisplacement' in [node.bl_idname for node in self.nodes] \
                and 'ShaderNodeOutputMaterial' in [node.bl_idname for node in self.nodes]:
            self.material.node_tree.links.new( self.displacement_node.outputs[0], self.output_node.inputs[2])

        #connect normal map to shader node
        if 'ShaderNodeNormalMap' in [node.bl_idname for node in self.nodes] \
                and 'ShaderNodeBsdfPrincipled' in [node.bl_idname for node in self.nodes]:
            self.material.node_tree.links.new(self.normal_node.outputs[0], self.shader_node.inputs[19])

        #connect texture nodes to inputs
        if 'ShaderNodeTexImage' in [node.bl_idname for node in self.nodes]:
            for node in self.nodes:
                print(node.label)
                if node.label == self.diffuse_label:
                    if 'ShaderNodeBsdfPrincipled' in [node.bl_idname for node in self.nodes]:
                        self.material.node_tree.links.new(node.outputs[0], self.shader_node.inputs[0])
                if node.label == self.normal_label:
                    if 'ShaderNodeNormalMap' in [node.bl_idname for node in self.nodes]:
                        self.material.node_tree.links.new(node.outputs[0], self.normal_node.inputs[0])
                if node.label == self.displacement_label:
                    if 'ShaderNodeDisplacement' in [node.bl_idname for node in self.nodes]:
                        self.material.node_tree.links.new(node.outputs[0], self.displacement_node.inputs[0])
        
        ## END FIXME
        ## ---------


        # for node in self.nodes:
        #     print(node.bl_idname)        #
        #     if node.bl_idname == 'ShaderNodeBsdfPrincipled':
        #         for idx, i in enumerate(node.inputs):
        #             print("inputs: ", idx, i.name)
        #             if i.name == 'Base Color':
        #                 return node.inputs[idx]
        #             elif i.name == 'Normal':
        #                 return node.inputs[idx]
        #         for idx, o in enumerate(node.outputs):
        #             print("outputs: ", idx, o)
        #             if o.name == 'BSDF':
        #                 return node.outputs[idx]

class AlignNodes(BuildNodes):
    """
    Is used to align nodes
    """
    def __init__(self):
        pass
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

        ## FIXME
        ## Ideally position should be computed dynamically without having you to care where it is
        self.output_node.location = self.pos_x, self.pos_y
        ## END FIXME
        ## ---------

        pass




## If you want to not use a premade node:
## --------------------------------------
##
## So if you don't want to go with the premade node group solution but building it from scratch this is how I would do it.
## We need a simple node class (contain only the basic information)

class SimpleNodeExample:
    """
    Contain only the common parts for a node
    """
    _color = None
    _pos_x = None
    _pos_y = None
    # etc ...

    def __init__(self, color, pos_x, _pos_y):
        self._color = color
        # etc ...

## We then have subclass extending the SimpleNode for each type of "special" nodes

class ShaderNodeExample(SimpleNode):
    """
    Is used for the shader nodes
    """
    _something_specific_to_shadernode = None

    def __init__(self, color, pos_x, _pos_y,  something_specific_to_shadernode):
        ## super calls the parent __init__() method
        super(color, pos_x, _pos_y)
        self._something_specific_to_shadernode = something_specific_to_shadernode

## For the normal map
class NormalNodeExample(SimpleNode):
    """
    Is used for the normal map node
    """
    _something_specific_to_normalmap = None

    def __init__(self, color, pos_x, _pos_y,  something_specific_to_normalmap):
        ## super calls the parent __init__ method
        super(color, pos_x, _pos_y)
        self._something_specific_to_normalmap = something_specific_to_normalmap

## Etc
## ---

## Then there is a group of nodes (which contain the individual nodes)

class NodeGroupExample:
    """
    Contain a group of nodes connected togheter
    """
    _nodes = None
    _name = None

    def __init__(self, name):
        self._nodes = []
        self._name = name
    
    def add_node(self, node):
        self._nodes.append(node)
    
    def make_links(self):
        for node in self._nodes:
            ## make the complicated connection between them here
            ## Actually since it's a group which has always the same connection 
            ## you don't even need to specify them per nodes.
            pass


## And to use it this how we would do

# my_group = NodeGroup("zbrush group")
#
# my_group.add_node(ShaderNode(color, position_x, position_y, more_data))
# my_group.add_node(NormalNode(color, position_x, position_y, more_data))
#
# my_group.make_links()

## End
## ---


# mat_node.create_output_node()
#             mat_node.create_shader_node()
#             mat_node.create_normal_node()
#             mat_node.create_displacement_node()
