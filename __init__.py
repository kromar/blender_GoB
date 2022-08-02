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


if "bpy" in locals():
    import importlib
    importlib.reload(GoB)
    importlib.reload(preferences)
    importlib.reload(addon_updater)
else:
    from . import GoB
    from . import preferences
    from . import addon_updater

import bpy
import os
import bpy.utils.previews


bl_info = {
    "name": "GoB",
    "description": "An unofficial GOZ-like addon for Blender",
    "author": "ODe, JoseConseco, Daniel Grauer",
    "version": (3, 5, 99),
    "blender": (2, 93, 0),
    "location": "In the info header",
    "doc_url": "https://github.com/JoseConseco/GoB/wiki",                
    "tracker_url": "https://github.com/JoseConseco/GoB/issues/new",
    "category": "Import-Export"}


classes = (
    GoB.GoB_OT_import,
    GoB.GoB_OT_export,
    GoB.GoB_OT_export_button,
    GoB.GoB_OT_GoZ_Installer,
    GoB.GOB_OT_Popup,
    preferences.GoB_Preferences,
    addon_updater.AU_OT_SearchUpdates,
    )

icons = ["goz_send" , "goz_sync_enabled", "goz_sync_disabled"]
custom_icons = {}

def register():
    [bpy.utils.register_class(c) for c in classes]
    
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    for icon in icons :
       custom_icons.load( icon , os.path.join(my_icons_dir, icon + ".png" )  , 'IMAGE')    
    GoB.custom_icons["main"] = custom_icons 
    bpy.types.TOPBAR_HT_upper_bar.prepend(GoB.draw_goz_buttons)


def unregister():
    [bpy.utils.unregister_class(c) for c in classes]

    bpy.types.TOPBAR_HT_upper_bar.remove(GoB.draw_goz_buttons)

    [bpy.utils.previews.remove(c) for c in GoB.custom_icons.values()]
    GoB.custom_icons.clear()

    if bpy.app.timers.is_registered(GoB.run_import_periodically):
        bpy.app.timers.unregister(GoB.run_import_periodically)
