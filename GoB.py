# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
import mathutils
import time
import os
from struct import pack, unpack
from copy import deepcopy
import string
from . import NodeBuilder



if os.path.isfile("C:/Users/Public/Pixologic/GoZBrush/GoZBrushFromApp.exe"):
    PATHGOZ = "C:/Users/Public/Pixologic"
    FROMAPP = "GoZBrushFromApp.exe"
elif os.path.isfile("/Users/Shared/Pixologic/GoZBrush/GoZBrushFromApp.app/Contents/MacOS/GoZBrushFromApp"):
    PATHGOZ = "/Users/Shared/Pixologic"
    FROMAPP = "GoZBrushFromApp.app/Contents/MacOS/GoZBrushFromApp"
else:
    PATHGOZ = False


time_interval = 2.0  # Check GoZ import for changes every 2.0 seconds
run_background_update = False
cached_last_edition_time = time.time() - 10.0

preview_collections = {}
def draw_goz_buttons(self, context):
    global run_background_update, icons
    icons = preview_collections["main"]
    pref = bpy.context.preferences.addons[__package__.split(".")[0]].preferences
    if context.region.alignment == 'RIGHT':
        layout = self.layout
        row = layout.row(align=True)

        if pref.show_button_text:
            row.operator(operator="scene.gob_export", text="Export", emboss=True, icon_value=icons["GOZ_SEND"].icon_id)
            if run_background_update:
                row.operator(operator="scene.gob_import", text="Import", emboss=True, depress=True, icon_value=icons["GOZ_SYNC_ENABLED"].icon_id)
            else:
                row.operator(operator="scene.gob_import", text="Import", emboss=True, depress=False, icon_value=icons["GOZ_SYNC_DISABLED"].icon_id)
        else:
            row.operator(operator="scene.gob_export", text="", emboss=True, icon_value=icons["GOZ_SEND"].icon_id)
            if run_background_update:
                row.operator(operator="scene.gob_import", text="", emboss=True, depress=True, icon_value=icons["GOZ_SYNC_ENABLED"].icon_id)
            else:
                row.operator(operator="scene.gob_import", text="", emboss=True, depress=False, icon_value=icons["GOZ_SYNC_DISABLED"].icon_id)


class GoB_OT_import(bpy.types.Operator):
    bl_idname = "scene.gob_import"
    bl_label = "GOZ import"
    bl_description = "GOZ import background listener"

    def GoZit(self, pathFile):
        scn = bpy.context.scene
        pref = bpy.context.preferences.addons[__package__.split(".")[0]].preferences
        diff_map = False
        normal_map = False
        disp_map = False

        utag = 0
        vertsData = []
        facesData = []
        polypaint = []
        exists = os.path.isfile(pathFile)
        if not exists:
            print(f'Cant read mesh from: {pathFile}. Skipping')
            return

        with open(pathFile, 'rb') as goz_file:
            goz_file.seek(36, 0)
            lenObjName = unpack('<I', goz_file.read(4))[0] - 16
            goz_file.seek(8, 1)
            obj_name = unpack('%ss' % lenObjName, goz_file.read(lenObjName))[0]
            # remove non ascii chars eg. /x 00
            objName = ''.join([letter for letter in obj_name[8:].decode('utf-8') if letter in string.printable])
            print(f"Importing: {pathFile, objName}")
            me = bpy.data.meshes.new(objName)
            tag = goz_file.read(4)
            while tag:
                print('tags: ', tag)
                if tag == b'\x89\x13\x00\x00':
                    cnt = unpack('<L', goz_file.read(4))[0] - 8
                    goz_file.seek(cnt, 1)

                # Vertices
                elif tag == b'\x11\x27\x00\x00':
                    goz_file.seek(4, 1)
                    cnt = unpack('<Q', goz_file.read(8))[0]
                    for i in range(cnt):
                        co1 = unpack('<f', goz_file.read(4))[0]
                        co2 = unpack('<f', goz_file.read(4))[0]
                        co3 = unpack('<f', goz_file.read(4))[0]
                        vertsData.append((co1, co2, co3))

                # Faces
                elif tag == b'\x21\x4e\x00\x00':
                    goz_file.seek(4, 1)
                    cnt = unpack('<Q', goz_file.read(8))[0]
                    for i in range(cnt):
                        v1 = unpack('<L', goz_file.read(4))[0]
                        v2 = unpack('<L', goz_file.read(4))[0]
                        v3 = unpack('<L', goz_file.read(4))[0]
                        v4 = unpack('<L', goz_file.read(4))[0]
                        if v4 == 0xffffffff:
                            facesData.append((v1, v2, v3))
                        elif v4 == 0:
                            facesData.append((v4, v1, v2, v3))
                        else:
                            facesData.append((v1, v2, v3, v4))

                # UVs
                elif tag == b'\xa9\x61\x00\x00':
                    break

                # Polypainting
                elif tag == b'\xb9\x88\x00\x00':
                    break

                # Mask
                elif tag == b'\x32\x75\x00\x00':
                    break

                # Polyroups
                elif tag == b'\x41\x9c\x00\x00':
                    break

                # End
                elif tag == b'\x00\x00\x00\x00':
                    break
                else:
                    # print(f"unknown tag:{tag}. Skip it...")
                    if utag >= 10:
                        print("...Too many mesh tags unknown...")
                        break
                    utag += 1
                    cnt = unpack('<I', goz_file.read(4))[0] - 8
                    goz_file.seek(cnt, 1)
                tag = goz_file.read(4)
            me.from_pydata(vertsData, [], facesData)  # Assume mesh data in ready to write to mesh..
            del vertsData
            del facesData
            if pref.flip_up_axis:  # fixes bad mesh orientation for some people
                if pref.flip_forward_axis:
                    me.transform(mathutils.Matrix([
                        (-1., 0., 0., 0.),
                        (0., 0., -1., 0.),
                        (0., 1., 0., 0.),
                        (0., 0., 0., 1.)]))
                    me.flip_normals()
                else:
                    me.transform(mathutils.Matrix([
                        (-1., 0., 0., 0.),
                        (0., 0., 1., 0.),
                        (0., 1., 0., 0.),
                        (0., 0., 0., 1.)]))

            else:
                if pref.flip_forward_axis:
                    me.transform(mathutils.Matrix([
                        (1., 0., 0., 0.),
                        (0., 0., -1., 0.),
                        (0., -1., 0., 0.),
                        (0., 0., 0., 1.)]))
                    me.flip_normals()
                else:
                    me.transform(mathutils.Matrix([
                        (1., 0., 0., 0.),
                        (0., 0., 1., 0.),
                        (0., -1., 0., 0.),
                        (0., 0., 0., 1.)]))

            # useful for development when the mesh may be invalid.
            me.validate(verbose=True)
            # update mesh data after transformations to fix normals
            me.update(calc_edges=True, calc_edges_loose=True, calc_loop_triangles=True)

            # if obj already exist do code below
            if objName in bpy.data.objects.keys():
                obj = bpy.data.objects[objName]
                oldMesh = obj.data
                instances = [ob for ob in bpy.data.objects if ob.data == obj.data]
                for old_mat in oldMesh.materials:
                    me.materials.append(old_mat)
                for instance in instances:
                    instance.data = me
                bpy.data.meshes.remove(oldMesh)
                obj.data.transform(obj.matrix_world.inverted()) #assume we have to rever transformation from obj mode
                obj.select_set(True)

                if len(obj.material_slots) > 0:
                    if obj.material_slots[0].material is not None:
                        objMat = obj.material_slots[0].material
                    else:
                        objMat = bpy.data.materials.new('GoB_{0}'.format(objName))
                        obj.material_slots[0].material = objMat
                else:
                    objMat = bpy.data.materials.new('GoB_{0}'.format(objName))
                    obj.data.materials.append(objMat)
                #create_node_material(objMat, pref)

            # create new object
            else:
                obj = bpy.data.objects.new(objName, me)
                objMat = bpy.data.materials.new('GoB_{0}'.format(objName))
                obj.data.materials.append(objMat)
                scn.collection.objects.link(obj)
                obj.select_set(True)
                #create_node_material(objMat, pref)

            # user defined import shading
            if pref.shading == 'SHADE_SMOOTH':
                values = [True] * len(me.polygons)
            else:
                values = [False] * len(me.polygons)
            me.polygons.foreach_set("use_smooth", values)

            utag = 0

            # UVs
            while tag:
                if tag == b'\xa9\x61\x00\x00':
                    me.uv_layers.new()
                    goz_file.seek(4, 1)
                    cnt = unpack('<Q', goz_file.read(8))[0] #face count..
                    uv_layer = me.uv_layers[0]
                    for tri in me.polygons:
                        for i, loop_index in enumerate(tri.loop_indices):
                            x, y = unpack('<2f', goz_file.read(8))
                            uv_layer.data[loop_index].uv = x, 1. - y
                        if i < 3:  # cos uv always have 4 coords... ??
                            x, y = unpack('<2f', goz_file.read(8))

                # Polypainting
                elif tag == b'\xb9\x88\x00\x00':
                    min = 255
                    goz_file.seek(4, 1)
                    cnt = unpack('<Q', goz_file.read(8))[0]
                    for i in range(cnt):
                        data = unpack('<3B', goz_file.read(3))
                        unpack('<B', goz_file.read(1))  # Alpha
                        if data[0] < min:
                            min = data[0]
                        polypaint.append(data)
                    if min < 250:
                        vertexColor = me.vertex_colors.new()
                        iv = 0
                        for poly in me.polygons:
                            for loop_index in poly.loop_indices:
                                loop = me.loops[loop_index]
                                v = loop.vertex_index
                                color = polypaint[v]
                                if bpy.app.version > (2, 79, 0):
                                    vertexColor.data[iv].color = [color[2]/255, color[1]/255, color[0]/255, 1]
                                else:
                                    vertexColor.data[iv].color = [color[2]/255, color[1]/255, color[0]/255]
                                iv += 1
                    del polypaint

                # Mask
                elif tag == b'\x32\x75\x00\x00':
                    goz_file.seek(4, 1)
                    cnt = unpack('<Q', goz_file.read(8))[0]
                    if 'mask' in obj.vertex_groups:
                        obj.vertex_groups.remove(obj.vertex_groups['mask'])
                    groupMask = obj.vertex_groups.new(name='mask')
                    for i in range(cnt):
                        data = unpack('<H', goz_file.read(2))[0] / 65535.
                        groupMask.add([i], 1.-data, 'ADD')

                # Polyroups
                elif tag == b'\x41\x9c\x00\x00':
                    groups = []
                    goz_file.seek(4, 1)
                    cnt = unpack('<Q', goz_file.read(8))[0]
                    for i in range(cnt):
                        gr = unpack('<H', goz_file.read(2))[0]
                        if gr not in groups:
                            if str(gr) in obj.vertex_groups:
                                obj.vertex_groups.remove(obj.vertex_groups[str(gr)])
                            polygroup = obj.vertex_groups.new(name=str(gr))
                            groups.append(gr)
                        else:
                            polygroup = obj.vertex_groups[str(gr)]
                        polygroup.add(list(me.polygons[i].vertices), 1., 'ADD')
                    try:
                        obj.vertex_groups.remove(obj.vertex_groups.get('0'))
                    except:
                        pass
                elif tag == b'\x00\x00\x00\x00':
                    break  # End

                # Diff map
                elif tag == b'\xc9\xaf\x00\x00':
                    print("diff tag")
                    cnt = unpack('<I', goz_file.read(4))[0] - 16
                    goz_file.seek(8, 1)
                    diffName = unpack('%ss' % cnt, goz_file.read(cnt))[0]
                    print("diff name: ", diffName.decode('utf-8'))
                    img = bpy.data.images.load(diffName.strip().decode('utf-8'))
                    diff_map = True
                    txtDiff = bpy.data.textures.new("GoB_diffuse", 'IMAGE')
                    txtDiff.image = img
                    # me.uv_textures[0].data[0].image = img

                # Disp map
                elif tag == b'\xd9\xd6\x00\x00':
                    print("Disp tag")
                    cnt = unpack('<I', goz_file.read(4))[0] - 16
                    goz_file.seek(8, 1)
                    dispName = unpack('%ss' % cnt, goz_file.read(cnt))[0]
                    print("disp name: ", dispName.decode('utf-8'))
                    img = bpy.data.images.load(dispName.strip().decode('utf-8'))
                    disp_map = True
                    txtDisp = bpy.data.textures.new("GoB_displacement", 'IMAGE')
                    txtDisp.image = img

                # Normal map
                elif tag == b'\x51\xc3\x00\x00':
                    print("Normal tag")
                    cnt = unpack('<I', goz_file.read(4))[0] - 16
                    goz_file.seek(8, 1)
                    nmpName = unpack('%ss' % cnt, goz_file.read(cnt))[0]
                    print("norm name: ", nmpName.decode('utf-8'))
                    img = bpy.data.images.load(nmpName.strip().decode('utf-8'))
                    normal_map = True
                    txtNmp = bpy.data.textures.new("GoB_normal", 'IMAGE')
                    txtNmp.image = img
                    txtNmp.use_normal_map = True

                else:
                    print("unknown tag:{0}\ntry to skip it...".format(tag))
                    if utag >= 10:
                        print("...Too many object tags unknown...")
                        break
                    utag += 1
                    cnt = unpack('<I', goz_file.read(4))[0] - 8
                    goz_file.seek(cnt, 1)
                tag = goz_file.read(4)

        bpy.context.view_layer.objects.active = obj

        if pref.materialinput == 'TEXTURES':

            #construct material node tree
            mat_node = NodeBuilder.BuildNodes(self, material=objMat)
            #create base nodes
            mat_node.create_output_node()
            mat_node.create_shader_node()
            # #create base color
            mat_node.create_textureimage_node(texture_image=txtDiff)
            #create normal map
            mat_node.create_normal_node()
            mat_node.create_textureimage_node(texture_image=txtNmp, pos_y=-300)
            # #create displacement map
            mat_node.create_displacement_node()
            mat_node.create_textureimage_node(texture_image=txtDisp, pos_y=-600)

            #mat_nodes.connect_nodes()
            #mat_node.align_nodes()

        #me.materials.append(objMat)
        return

    def execute(self, context):
        goz_obj_paths = []
        with open(f"{PATHGOZ}/GoZBrush/GoZ_ObjectList.txt", 'rt') as goz_objs_list:
            for line in goz_objs_list:
                goz_obj_paths.append(line.strip() + '.GoZ')

        if len(goz_obj_paths) == 0:
            self.report({'INFO'}, message="No goz files in GoZ_ObjectList.txt")
            return{'CANCELLED'}

        if context.object and context.object.mode != 'OBJECT':
            # ! cant get proper context from timers for now to change mode: https://developer.blender.org/T62074
            bpy.ops.object.mode_set(context.copy(), mode='OBJECT')      #TODO: fix #hack

        for ztool_path in goz_obj_paths:
            self.GoZit(ztool_path)

        self.report({'INFO'}, "Done")
        return{'FINISHED'}

    def invoke(self, context, event):
        global run_background_update
        if run_background_update:
            if bpy.app.timers.is_registered(run_import_periodically):
                bpy.app.timers.unregister(run_import_periodically)
                print('Disabling GOZ background listener')
            run_background_update = False
        else:
            if not bpy.app.timers.is_registered(run_import_periodically):
                bpy.app.timers.register(run_import_periodically, persistent=True)
                print('Enabling GOZ background listener')
            run_background_update = True
        return{'FINISHED'}




def create_node_textures(mat=None, txtDiff=None, txtNmp=None, txtDisp=None):


    #if no nodes:

        # create full input stack

    #else:
        #
        # if texture is connected to shader color:
        #     'we know we have a diffuse'
        #
        # if texture is connectd to normal color:
        #     'we know we have a normal map'
        #
        # if texture is conected to displacement height:
        #     'we know we have a displacement map'



    # sanity checks for node links
    #     - check that shader is connected to output
    #     - check that normal is connected to shader
    #     - check that displacement node is connected to output




    #if diff_map:
    print("current material: ", mat.name)
    # enable nodes
    if not mat.use_nodes:
        mat.use_nodes = True
 
    nodes = mat.node_tree.nodes
    if nodes:
        for node in nodes:
            for output in node.outputs:
                for link in output.links:
                    if link:
                        print("out link found: ", node.bl_idname, " -> ", link.to_node.name)    # , " : ", link.to_node.link)

                        if node.bl_idname == 'ShaderNodeTexImage' and link.to_node.name == 'Principled BSDF':
                            print("diffuse texture node identified")
                        else:
                            pass
                        if node.bl_idname == 'ShaderNodeTexImage' and link.to_node.name == 'Normal Map':
                            print("normal map texture node identified")
                        else:
                            pass
                        if node.bl_idname == 'ShaderNodeTexImage' and link.to_node.name == 'Displacement':
                            print("displacement map texture node identified")
                        else:
                            pass
                    else:
                        print("No node link found: ", node.bl_idname)


            # if node.bl_idname == 'ShaderNodeTexImage':
            #     print("ShaderNodeTexImage"G)
            # if node.name == 'Image Texture':
            #     print(node)
            # else:
            #     print("no textures found, lets create one")
            #
            # if node.bl_idname == 'ShaderNodeOutputMaterial':
            #     print("ShaderNodeOutputMaterial: ", node)
            #     if node.inputs:
            #         for node_input in node.inputs:
            #             # print("node inputs: ", node_input)
            #
            #             # iterate through the links until we find the textures?
            #             # check here for connections
            #             for link in node_input.links:
            #                 if link:
            #                     print("links: ", node_input, link.from_node)
            #     else:
            #         print("we need a connection!")
            # else:
            #     print("no nodes found")
            #     # nodes.new('Material Output')


    # if no nodes are available create the full node tree
    else:
        mat_node = nodes.new('ShaderNodeOutputMaterial')
        mat_node.location = 400, 0

        shader_node = nodes.new('ShaderNodeBsdfPrincipled')
        shader_node.location = 0, 0
        mat.node_tree.links.new(mat_node.inputs[0], shader_node.outputs[0])

        if txtDiff:
            txtDiff_node = nodes.new('ShaderNodeTexImage')
            txtDiff_node.location = -800, 0
            txtDiff_node.image = txtDiff.image
            txtDiff_node.width = 400
            txtDiff_node.interpolation = 'Smart'
            mat.node_tree.links.new(shader_node.inputs[0], txtDiff_node.outputs[0])

        if txtNmp:
            nm_node = nodes.new('ShaderNodeNormalMap')
            nm_node.location = -300, -300
            mat.node_tree.links.new(shader_node.inputs[17], nm_node.outputs[0])     # TODO: find index by input name

            txtNmp_node = nodes.new('ShaderNodeTexImage')
            txtNmp_node.location = -800, -300
            txtNmp_node.image = txtNmp.image
            txtNmp_node.width = 400
            txtNmp_node.color_space = 'NONE'
            txtNmp_node.interpolation = 'Smart'
            mat.node_tree.links.new(nm_node.inputs[1], txtNmp_node.outputs[0])

        if txtDisp:
            disp_node = nodes.new('ShaderNodeDisplacement')
            disp_node.location = -300, -600
            mat.node_tree.links.new(mat_node.inputs[2], disp_node.outputs[0])

            txtDisp_node = nodes.new('ShaderNodeTexImage')
            txtDisp_node.location = -800, -600
            txtDisp_node.image = txtDisp.image
            txtDisp_node.width = 400
            txtDisp_node.interpolation = 'Smart'
            mat.node_tree.links.new(disp_node.inputs[0], txtDisp_node.outputs[0])


        print(80*"=")


        # output_node = nodes.get('Material Output')
        # shader_node = nodes.get('Principled BSDF')
        # print("output_node: ", output_node)


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



        # # create new node
        #if not txtdiff_node:
        #txtdiff_node = nodes.new('ShaderNodeTexImage')
        #txtdiff_node.location = -300, 300
        #txtdiff_node.image = txtDiff.image
        # link nodes
        #mat.node_tree.links.new(output_node.inputs[0], txtdiff_node.outputs[0])


# currently not used
def collect_export_nodes():
    # obj.material_slots[0].material
    for matslot in obj.material_slots:
        # print("matslot: ", matslot)
        if matslot.material:
            GoBmat = matslot.material
            break

    # get the textures from material nodes
    if GoBmat.node_tree:
        nodes = GoBmat.node_tree.nodes

        output_node = nodes.get('Material Output')
        mat_surface_input = output_node.inputs[0].links[0].from_node
        mat_disp_input = output_node.inputs[2].links[0].from_node

        # displacement
        for node_input in mat_disp_input.inputs:
            if node_input.name == 'Height' and node_input.links:
                disp_map = node_input.links[0].from_node
                # print("disp_map: ", disp_map)

        # diffuse and normal
        for node_input in mat_surface_input.inputs:
            if (node_input.name == 'Base Color' or node_input.name == 'Color') and node_input.links:
                diff_map = node_input.links[0].from_node
                # print("diff map: ", diff_map)

            elif node_input.name == 'Normal':
                normal_node = node_input.links[0].from_node
                for i in normal_node.inputs:
                    if i.name == 'Color' and i.links:
                        normal_map = i.links[0].from_node
                        # print("normal_map: ", i.links[0].from_node)


    # enable nodes
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    output_node = nodes.get('Principled BSDF')
    vcol_node = nodes.get('ShaderNodeAttribute')

    if pref.materialinput == 'POLYPAINT':

        # create new node
        if not vcol_node:
            vcol_node = nodes.new('ShaderNodeAttribute')
            vcol_node.location = -300, 200
            vcol_node.attribute_name = 'Col'  # TODO: replace with vertex color group name

            # link nodes
            mat.node_tree.links.new(output_node.inputs[0], vcol_node.outputs[0])


def run_import_periodically():
    # print("Runing timers update check")
    global cached_last_edition_time, run_background_update

    try:
        file_edition_time = os.path.getmtime(f"{PATHGOZ}/GoZBrush/GoZ_ObjectList.txt")
    except Exception as e:
        print(e)
        run_background_update = False
        if bpy.app.timers.is_registered(run_import_periodically):
            bpy.app.timers.unregister(run_import_periodically)
        return time_interval

    if file_edition_time > cached_last_edition_time:
        cached_last_edition_time = file_edition_time
        # ! cant get proper context from timers for now. Override context: https://developer.blender.org/T62074
        window = bpy.context.window_manager.windows[0]
        ctx = {'window': window, 'screen': window.screen, 'workspace': window.workspace}
        bpy.ops.scene.gob_import(ctx) #only call operator update is found (executing operatros is slow)
    else:
        # print("GOZ: Nothing to update")
        return time_interval
    
    if not run_background_update and bpy.app.timers.is_registered(run_import_periodically):
        bpy.app.timers.unregister(run_import_periodically)
    return time_interval


class GoB_OT_export(bpy.types.Operator):
    bl_idname = "scene.gob_export"
    bl_label = "Export to Zbrush"
    bl_description = "Export to Zbrush"

    @staticmethod
    def apply_modifiers(obj, pref):
        dg = bpy.context.evaluated_depsgraph_get()
        if pref.modifiers == 'APPLY_EXPORT':
            # me = object_eval.to_mesh() #with modifiers - crash need to_mesh_clear()?
            me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
            obj.data = me
            obj.modifiers.clear()
        elif pref.modifiers == 'ONLY_EXPORT':
            me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        else:
            me = obj.data

        #DO the triangulation of Ngons only, but do not write it to original object. User has to handle Ngons manaully if they want.
        bm = bmesh.new()
        bm.from_mesh(me)
        triangulate_faces = [f for f in bm.faces if len(f.edges) > 4]
        result = bmesh.ops.triangulate(bm, faces=triangulate_faces)
        #join traingles only that are result of ngon triangulation
        bmesh.ops.join_triangles(bm, faces=result['faces'], cmp_seam=False, cmp_sharp=False, cmp_uvs=False, cmp_vcols=False,
                                 cmp_materials=False, angle_face_threshold=3.1, angle_shape_threshold=3.1)
        export_mesh = bpy.data.meshes.new(name=f'{obj.name}_goz')  # mesh is deleted in main loop anyway
        bm.to_mesh(export_mesh)
        bm.free()

        return export_mesh

    @staticmethod
    def make_polygroups(obj, pref, create=False):

        if pref.polygroups == 'MATERIALS':
            for index, slot in enumerate(obj.material_slots):
                #select the verts from faces with material index
                if not slot.material:
                    # empty slot
                    continue
                verts = [v for f in obj.data.polygons
                         if f.material_index == index for v in f.vertices]
                if len(verts):
                    vg = obj.vertex_groups.get(slot.material.name)
                    if create == True:
                        if vg is None:
                            vg = obj.vertex_groups.new(name=slot.material.name)
                            vg.add(verts, 1.0, 'ADD')
                    else:
                        try:
                            obj.vertex_groups.remove(vg)
                        except:
                            pass
        else:
            pass


    def exportGoZ(self, path, scn, obj, pathImport):
        pref = bpy.context.preferences.addons[__package__.split(".")[0]].preferences


        # TODO: when linked system is finalized it could be possible to provide
        #  a option to modify the linked object. for now a copy
        #  of the linked object is created to goz it
        if bpy.context.object.type == 'MESH':
            if bpy.context.object.library:
                new_ob = obj.copy()
                new_ob.data = obj.data.copy()
                scn.collection.objects.link(new_ob)
                new_ob.select_set(state=True)
                obj.select_set(state=False)
                bpy.context.view_layer.objects.active = new_ob

        #create polygroups from object features (materials, uvs, ...)
        self.make_polygroups(obj, pref, True)
        me = self.apply_modifiers(obj, pref)
        me.calc_loop_triangles()

        if pref.flip_up_axis:
            if pref.flip_forward_axis:
                mat_transform = mathutils.Matrix([
                    (1., 0., 0., 0.),
                    (0., 0., 1., 0.),
                    (0., -1., 0., 0.),
                    (0., 0., 0., 1.)])
            else:
                mat_transform = mathutils.Matrix([
                    (-1., 0., 0., 0.),
                    (0., 0., 1., 0.),
                    (0., 1., 0., 0.),
                    (0., 0., 0., 1.)])
        else:
            if pref.flip_forward_axis:
                mat_transform = mathutils.Matrix([
                    (-1., 0., 0., 0.),
                    (0., 0., -1., 0.),
                    (0., -1., 0., 0.),
                    (0., 0., 0., 1.)])
            else:
                mat_transform = mathutils.Matrix([
                    (1., 0., 0., 0.),
                    (0., 0., -1., 0.),
                    (0., 1., 0., 0.),
                    (0., 0., 0., 1.)])

        with open(pathImport+'/{0}.GoZ'.format(obj.name), 'wb') as goz_file:
            goz_file.write(b"GoZb 1.0 ZBrush GoZ Binary")
            goz_file.write(pack('<6B', 0x2E, 0x2E, 0x2E, 0x2E, 0x2E, 0x2E))
            goz_file.write(pack('<I', 1))  # obj tag
            goz_file.write(pack('<I', len(obj.name)+24))
            goz_file.write(pack('<Q', 1))
            goz_file.write(b'GoZMesh_'+obj.name.encode('U8'))
            goz_file.write(pack('<4B', 0x89, 0x13, 0x00, 0x00))
            goz_file.write(pack('<I', 20))
            goz_file.write(pack('<Q', 1))
            goz_file.write(pack('<I', 0))
            nbFaces = len(me.polygons)
            nbVertices = len(me.vertices)
            goz_file.write(pack('<4B', 0x11, 0x27, 0x00, 0x00))
            goz_file.write(pack('<I', nbVertices*3*4+16))
            goz_file.write(pack('<Q', nbVertices))
            for vert in me.vertices:
                modif_coo = obj.matrix_world @ vert.co
                modif_coo = mat_transform @ modif_coo
                goz_file.write(pack('<3f', modif_coo[0], modif_coo[1], modif_coo[2]))
            goz_file.write(pack('<4B', 0x21, 0x4E, 0x00, 0x00))
            goz_file.write(pack('<I', nbFaces*4*4+16))
            goz_file.write(pack('<Q', nbFaces))
            for face in me.polygons:
                if len(face.vertices) == 4:
                    goz_file.write(pack('<4I', face.vertices[0],
                                face.vertices[1],
                                face.vertices[2],
                                face.vertices[3]))
                elif len(face.vertices) == 3:
                    goz_file.write(pack('<3I4B', face.vertices[0],
                                face.vertices[1],
                                face.vertices[2],
                                0xFF, 0xFF, 0xFF, 0xFF))
            # --UVs--
            if me.uv_layers.active:
                uv_layer = me.uv_layers[0]
                uvdata = me.uv_layers[0].data
                goz_file.write(pack('<4B', 0xA9, 0x61, 0x00, 0x00))
                goz_file.write(pack('<I', len(me.polygons)*4*2*4+16))
                goz_file.write(pack('<Q', len(me.polygons)))
                for face in me.polygons:
                    for i, loop_index in enumerate(face.loop_indices):
                        goz_file.write(pack('<2f', uv_layer.data[loop_index].uv.x, 1. - uv_layer.data[loop_index].uv.y))
                    if i == 2:
                        goz_file.write(pack('<2f', 0., 1.))


            # --Polypainting--
            if me.vertex_colors.active:
                vcoldata = me.vertex_colors.active.data # color[loop_id]
                vcolArray = bytearray([0] * nbVertices * 3)
                #fill vcArray(vert_idx + rgb_offset) = color_xyz
                for loop in me.loops: #in the end we will fill verts with last vert_loop color
                    vert_idx = loop.vertex_index
                    vcolArray[vert_idx*3] = int(255*vcoldata[loop.index].color[0])
                    vcolArray[vert_idx*3+1] = int(255*vcoldata[loop.index].color[1])
                    vcolArray[vert_idx*3+2] = int(255*vcoldata[loop.index].color[2])

                goz_file.write(pack('<4B', 0xb9, 0x88, 0x00, 0x00))
                goz_file.write(pack('<I', nbVertices*4+16))
                goz_file.write(pack('<Q', nbVertices))
                for i in range(0, len(vcolArray), 3):
                    goz_file.write(pack('<B', vcolArray[i+2]))
                    goz_file.write(pack('<B', vcolArray[i+1]))
                    goz_file.write(pack('<B', vcolArray[i]))
                    goz_file.write(pack('<B', 0))
                del vcolArray
            # --Mask--
            for vertexGroup in obj.vertex_groups:
                if vertexGroup.name.lower() == 'mask':
                    goz_file.write(pack('<4B', 0x32, 0x75, 0x00, 0x00))
                    goz_file.write(pack('<I', nbVertices*2+16))
                    goz_file.write(pack('<Q', nbVertices))
                    for i in range(nbVertices):
                        try:
                            goz_file.write(pack('<H', int((1.-vertexGroup.weight(i))*65535)))
                        except:
                            goz_file.write(pack('<H', 255))
                    break
            # --Polygroups--
            vertWeight = []
            for i in range(len(me.vertices)):
                vertWeight.append([])
                for group in me.vertices[i].groups:
                    try:
                        if group.weight == 1. and obj.vertex_groups[group.group].name.lower() != 'mask':
                            vertWeight[i].append(group.group)
                    except:
                        print('error reading vertex group data')
            goz_file.write(pack('<4B', 0x41, 0x9C, 0x00, 0x00))
            goz_file.write(pack('<I', nbFaces*2+16))
            goz_file.write(pack('<Q', nbFaces))
            import random
            numrand = random.randint(1, 40)
            for face in me.polygons:
                gr = []
                for vert in face.vertices:
                    gr.extend(vertWeight[vert])
                gr.sort()
                gr.reverse()
                tmp = {}
                groupVal = 0
                for val in gr:
                    if val not in tmp:
                        tmp[val] = 1
                    else:
                        tmp[val] += 1
                        if tmp[val] == len(face.vertices):
                            groupVal = val
                            break
                if obj.vertex_groups.items() != []:
                    grName = obj.vertex_groups[groupVal].name
                    if grName.lower() == 'mask':
                        goz_file.write(pack('<H', 0))
                    else:
                        grName = obj.vertex_groups[groupVal].index * numrand
                        goz_file.write(pack('<H', grName))
                else:
                    goz_file.write(pack('<H', 0))

            # Diff, disp and nm maps
            diff_map = False
            normal_map = False
            disp_map = False
            GoBmat = False

            # obj.material_slots[0].material
            for matslot in obj.material_slots:
                #print("matslot: ", matslot)
                if matslot.material:
                    GoBmat = matslot.material
                    break

            #get the textures from material nodes
            #TODO: currently only full node export is supported, cover partial node setup (diff, nm, dm)
            # if GoBmat.node_tree:
            #     nodes = GoBmat.node_tree.nodes
            #
            #     output_node = nodes.get('Material Output')
            #     mat_surface_input = output_node.inputs[0].links[0].from_node
            #     mat_disp_input = output_node.inputs[2].links[0].from_node
            #
            #     # displacement
            #     for node_input in mat_disp_input.inputs:
            #         if node_input.name == 'Height' and node_input.links:
            #             disp_map = node_input.links[0].from_node
            #             #print("disp_map: ", disp_map)
            #
            #     # diffuse and normal
            #     for node_input in mat_surface_input.inputs:
            #         if (node_input.name == 'Base Color' or node_input.name == 'Color') and node_input.links:
            #             diff_map = node_input.links[0].from_node
            #             #print("diff map: ", diff_map)
            #
            #         elif node_input.name == 'Normal':
            #             normal_node = node_input.links[0].from_node
            #             for i in normal_node.inputs:
            #                 if i.name == 'Color' and i.links:
            #                     normal_map = i.links[0].from_node
            #                     #print("normal_map: ", i.links[0].from_node)



            formatRender = scn.render.image_settings.file_format
            scn.render.image_settings.file_format = 'TIFF'
            texture_extension = '.tif'
            diff_suffix = '_TXTR'
            norm_suffix = '_NM'
            disp_suffix = '_DM'

            if diff_map:
                name = diff_map.image.filepath.replace('\\', '/')
                name = name.rsplit('/')[-1]
                name = name.rsplit('.')[0]
                if len(name) > 5:
                    if name[-5:] == diff_suffix:
                        name = path + '/GoZProjects/Default/' + name + texture_extension
                    else:
                        name = path + '/GoZProjects/Default/' + name + diff_suffix + texture_extension
                diff_map.image.save_render(name)
                print("exported: ", name)
                name = name.encode('utf8')
                goz_file.write(pack('<4B', 0xc9, 0xaf, 0x00, 0x00))
                goz_file.write(pack('<I', len(name)+16))
                goz_file.write(pack('<Q', 1))
                goz_file.write(pack('%ss' % len(name), name))

            if normal_map:
                name = normal_map.image.filepath.replace('\\', '/')
                name = name.rsplit('/')[-1]
                name = name.rsplit('.')[0]
                if len(name) > 3:
                    if name[-3:] == norm_suffix:
                        name = path + '/GoZProjects/Default/' + name + texture_extension
                    else:
                        name = path + '/GoZProjects/Default/' + name + norm_suffix + texture_extension
                normal_map.image.save_render(name)
                print("exported: ", name)
                name = name.encode('utf8')
                goz_file.write(pack('<4B', 0x51, 0xc3, 0x00, 0x00))
                goz_file.write(pack('<I', len(name) + 16))
                goz_file.write(pack('<Q', 1))
                goz_file.write(pack('%ss' % len(name), name))

            if disp_map:
                name = disp_map.image.filepath.replace('\\', '/')
                name = name.rsplit('/')[-1]
                name = name.rsplit('.')[0]
                if len(name) > 3:
                    if name[-3:] == disp_suffix:
                        name = path + '/GoZProjects/Default/' + name + texture_extension
                    else:
                        name = path + '/GoZProjects/Default/' + name + disp_suffix + texture_extension
                disp_map.image.save_render(name)
                print("exported: ", name)
                name = name.encode('utf8')
                goz_file.write(pack('<4B', 0xd9, 0xd6, 0x00, 0x00))
                goz_file.write(pack('<I', len(name)+16))
                goz_file.write(pack('<Q', 1))
                goz_file.write(pack('%ss' % len(name), name))

            # fin
            scn.render.image_settings.file_format = formatRender
            goz_file.write(pack('16x'))

        self.make_polygroups(obj, pref, False)

        bpy.data.meshes.remove(me)
        return

    def execute(self, context):
        exists = os.path.isfile(f"{PATHGOZ}/GoZBrush/GoZ_ObjectList.txt")
        if not exists:
            print(f'Cant find: {f"{PATHGOZ}/GoZBrush/GoZ_ObjectList.txt"}. Check your Zbrush GOZ installation')
            return {"CANCELLED"}
        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        with open(f"{PATHGOZ}/GoZBrush/GoZ_ObjectList.txt", 'wt') as GoZ_ObjectList:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    self.escape_object_name(obj)
                    self.exportGoZ(PATHGOZ, context.scene, obj, f'{PATHGOZ}/GoZProjects/Default')
                    with open( f"{PATHGOZ}/GoZProjects/Default/{obj.name}.ztn", 'wt') as ztn:
                        ztn.write(f'{PATHGOZ}/GoZProjects/Default/{obj.name}')
                    GoZ_ObjectList.write(f'{PATHGOZ}/GoZProjects/Default/{obj.name}\n')

        global cached_last_edition_time
        cached_last_edition_time = os.path.getmtime(f"{PATHGOZ}/GoZBrush/GoZ_ObjectList.txt")
        os.system(f"{PATHGOZ}/GoZBrush/{FROMAPP}")
        return{'FINISHED'}


    def escape_object_name(self, obj):
        """
        Escape object name so it can be used as a valid file name.
        Keep only alphanumeric characters, underscore, dash and dot, and replace other characters with an underscore.
        Multiple consecutive invalid characters will be replaced with just a single underscore character.
        """
        import re
        new_name = re.sub('[^\w\_\-]+', '_', obj.name)
        if new_name == obj.name:
            return
        i = 0
        while new_name in bpy.data.objects.keys(): #while name collision with other scene objs,
            name_cut = None if i == 0 else -2  #in first loop, do not slice name.
            new_name = new_name[:name_cut] + str(i).zfill(2) #add two latters to end of obj name.
            i += 1
        obj.name = new_name



