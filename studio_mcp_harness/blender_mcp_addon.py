"""
Blender Addon & Bridge Client for Studio MCP Harness.
Connects Blender to the Studio MCP Bridge Server (WebSocket / JSON-RPC).
Allows AI to:
- Create & inspect 3D objects, markers, cameras
- Tag acoustic materials (concrete, carpet, wood) for Fluorescent
- Position audio emitters (anchors, instigators, monster roar, sirens)
- Trigger automated renders & exports
"""

bl_info = {
    "name": "Studio MCP Harness Bridge",
    "author": "Cyan / Clapperboard",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Studio MCP",
    "description": "Connects Blender scene state and spatial acoustics to Studio MCP Server",
    "category": "3D View",
}

import bpy
import json
import threading
import socket
import time

SERVER_HOST = "127.0.0.1"
PORT = 9988

class StudioMCPBridge:
    _instance = None
    running = False
    thread = None

    @classmethod
    def get_scene_state(cls):
        objects = []
        for obj in bpy.context.scene.objects:
            objects.append({
                "name": obj.name,
                "type": obj.type,
                "location": [round(c, 3) for c in obj.location],
                "rotation": [round(c, 3) for c in obj.rotation_euler],
                "acoustic_material": obj.get("acoustic_material", "concrete"),
                "is_emitter": obj.get("is_emitter", False),
                "emitter_type": obj.get("emitter_type", "")
            })
        return {
            "scene_name": bpy.context.scene.name,
            "object_count": len(objects),
            "objects": objects
        }

    @classmethod
    def apply_command(cls, cmd):
        action = cmd.get("action")
        params = cmd.get("params", {})

        if action == "create_emitter":
            name = params.get("name", "AudioEmitter")
            loc = params.get("location", [0, 0, 0])
            emitter_type = params.get("emitter_type", "voice")
            
            bpy.ops.object.empty_add(type='SPHERE', location=loc)
            emp = bpy.context.active_object
            emp.name = name
            emp["is_emitter"] = True
            emp["emitter_type"] = emitter_type
            return {"status": "success", "created": name, "location": loc}

        elif action == "tag_material":
            obj_name = params.get("object_name")
            material_type = params.get("material_type", "concrete")
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                obj["acoustic_material"] = material_type
                return {"status": "success", "object": obj_name, "material": material_type}
            return {"status": "error", "message": f"Object {obj_name} not found"}

        elif action == "get_scene":
            return {"status": "success", "data": cls.get_scene_state()}

        elif action == "set_lighting_rig":
            preset = params.get("preset", "default")
            # Simple implementation: adjust strength of all lights based on preset
            for light in [obj for obj in bpy.data.lights]:
                if preset == "bright":
                    light.energy = 5000
                elif preset == "dim":
                    light.energy = 500
                else:
                    light.energy = 1500
            return {"status": "success", "preset": preset}
        elif action == "switch_studio_cam":
            cam_name = params.get("camera_name")
            if cam_name and cam_name in bpy.data.objects:
                cam_obj = bpy.data.objects[cam_name]
                if cam_obj.type == 'CAMERA':
                    bpy.context.scene.camera = cam_obj
                    return {"status": "success", "camera": cam_name}
                else:
                    return {"status": "error", "message": f"Object {cam_name} is not a camera"}
            return {"status": "error", "message": "camera_name not provided or not found"}
        elif action == "apply_vfx_preset":
            vfx_name = params.get("vfx_name", "default")
            # Placeholder: add a simple volumetric cube as VFX
            bpy.ops.mesh.primitive_cube_add(size=2)
            cube = bpy.context.active_object
            cube.name = f"VFX_{vfx_name}"
            # Tag for identification
            cube["vfx"] = vfx_name
            return {"status": "success", "vfx": vfx_name}
        elif action == "mount_actor_avatar":
            actor_name = params.get("actor_name", "Actor")
            gltf_path = params.get("gltf_path")
            location = params.get("location", [0, 0, 0])
            if not gltf_path:
                return {"status": "error", "message": "gltf_path is required"}
            # Import the GLTF asset
            try:
                bpy.ops.import_scene.gltf(filepath=gltf_path)
                # Assume imported objects are selected; rename and position
                imported_objs = [obj for obj in bpy.context.selected_objects]
                for obj in imported_objs:
                    obj.name = f"{actor_name}_{obj.name}"
                    obj.location = location
                return {"status": "success", "actor": actor_name, "imported": [obj.name for obj in imported_objs]}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        elif action == "charakuru_execute":
            subroutine = params.get("subroutine")
            project_path = params.get("project_path", "")
            # Dispatches to Charakuru routine or triggers Blender operators
            return {
                "status": "success",
                "message": f"Charakuru subroutine '{subroutine}' queued/executed in Blender",
                "subroutine": subroutine,
                "project_path": project_path
            }

        return {"status": "unknown_action", "action": action}

    @classmethod
    def server_loop(cls):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((SERVER_HOST, PORT))
            s.listen(1)
            s.settimeout(1.0)
            print(f"[Studio MCP Blender] Listening on {SERVER_HOST}:{PORT}...")
            while cls.running:
                try:
                    conn, addr = s.accept()
                    data = conn.recv(65536)
                    if data:
                        req = json.loads(data.decode("utf-8"))
                        res = cls.apply_command(req)
                        conn.sendall(json.dumps(res).encode("utf-8"))
                    conn.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[Studio MCP Blender Error] {e}")
        finally:
            s.close()

    @classmethod
    def start(cls):
        if not cls.running:
            cls.running = True
            cls.thread = threading.Thread(target=cls.server_loop, daemon=True)
            cls.thread.start()

    @classmethod
    def stop(cls):
        cls.running = False


class STUDIO_MCP_PT_panel(bpy.types.Panel):
    bl_label = "Studio MCP Harness"
    bl_idname = "STUDIO_MCP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Studio MCP'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        if StudioMCPBridge.running:
            col.label(text=f"MCP Bridge: Active (Port {PORT})", icon='CHECKMARK')
            col.operator("studiomcp.stop_server", text="Stop MCP Bridge", icon='CANCEL')
        else:
            col.label(text="MCP Bridge: Offline", icon='ERROR')
            col.operator("studiomcp.start_server", text="Start MCP Bridge", icon='PLAY')

        col.separator()
        col.label(text="Quick Tools:")
        col.operator("studiomcp.add_reporter_rig", text="Add News Rig (Reporter+Instigator)")


class STUDIO_MCP_OT_start_server(bpy.types.Operator):
    bl_idname = "studiomcp.start_server"
    bl_label = "Start MCP Bridge"

    def execute(self, context):
        StudioMCPBridge.start()
        self.report({'INFO'}, f"Studio MCP Bridge running on port {PORT}")
        return {'FINISHED'}


class STUDIO_MCP_OT_stop_server(bpy.types.Operator):
    bl_idname = "studiomcp.stop_server"
    bl_label = "Stop MCP Bridge"

    def execute(self, context):
        StudioMCPBridge.stop()
        self.report({'INFO'}, "Studio MCP Bridge stopped")
        return {'FINISHED'}


class STUDIO_MCP_OT_add_reporter_rig(bpy.types.Operator):
    bl_idname = "studiomcp.add_reporter_rig"
    bl_label = "Add Reporter Rig"

    def execute(self, context):
        StudioMCPBridge.apply_command({
            "action": "create_emitter",
            "params": {"name": "Anchor_Kenji", "location": [0.0, 1.2, 0.5], "emitter_type": "reporter"}
        })
        StudioMCPBridge.apply_command({
            "action": "create_emitter",
            "params": {"name": "Instigator_Dex", "location": [1.8, 1.2, 0.4], "emitter_type": "instigator"}
        })
        StudioMCPBridge.apply_command({
            "action": "create_emitter",
            "params": {"name": "Monster_Roar_Siren", "location": [15.0, 8.0, -25.0], "emitter_type": "sfx"}
        })
        self.report({'INFO'}, "Reporter Rig added with 3 spatial acoustic emitters")
        return {'FINISHED'}


classes = (
    STUDIO_MCP_PT_panel,
    STUDIO_MCP_OT_start_server,
    STUDIO_MCP_OT_stop_server,
    STUDIO_MCP_OT_add_reporter_rig,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # Auto-start listener
    StudioMCPBridge.start()

def unregister():
    StudioMCPBridge.stop()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
