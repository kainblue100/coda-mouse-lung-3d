#!/usr/bin/env python3
"""Blender headless: import CODA class OBJs, light, Cycles hero + turntable.

Run:
  blender -b -P blender_render_lung.py -- --mesh-dir DIR --out DIR --frames 72
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args(argv):
    args = {
        "mesh_dir": None,
        "out": None,
        "frames": 72,
        "res_x": 1600,
        "res_y": 1000,
        "samples": 256,
        "engine": "CYCLES",
        "preset": "final",
    }
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    i = 0
    while i < len(argv):
        k = argv[i]
        if k == "--mesh-dir":
            args["mesh_dir"] = argv[i + 1]; i += 2
        elif k == "--out":
            args["out"] = argv[i + 1]; i += 2
        elif k == "--frames":
            args["frames"] = int(argv[i + 1]); i += 2
        elif k == "--samples":
            args["samples"] = int(argv[i + 1]); i += 2
        elif k == "--preset":
            args["preset"] = argv[i + 1]; i += 2
        else:
            i += 1
    if args["preset"] == "preview":
        args["samples"] = min(args["samples"], 64)
        args["res_x"] //= 2
        args["res_y"] //= 2
    return args


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)


def make_material(name: str, rgb, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.15
    elif "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = 0.15
    bsdf.inputs["Roughness"].default_value = 0.45
    if alpha < 1.0:
        mat.blend_method = "BLEND"
        bsdf.inputs["Alpha"].default_value = alpha
    return mat


def setup_world():
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.08, 0.09, 0.11, 1.0)
    bg.inputs[1].default_value = 0.35


def setup_lights(center: Vector):
    def area(name, loc, energy, size, color=(1, 0.98, 0.95)):
        light = bpy.data.lights.new(name=name, type="AREA")
        light.energy = energy
        light.size = size
        light.color = color
        obj = bpy.data.objects.new(name, light)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        direction = center - obj.location
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return obj

    area("Key", center + Vector((0.9, -1.2, 0.8)), 250, 0.55)
    area("Fill", center + Vector((-1.0, -0.4, 0.3)), 80, 0.8, (0.85, 0.9, 1.0))
    area("Rim", center + Vector((0.2, 1.1, 0.6)), 120, 0.4, (1.0, 0.95, 0.9))


def setup_camera(center: Vector, radius: float):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 65
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = center + Vector((0, -radius, radius * 0.28))
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return cam


def setup_cycles(scene, samples: int, res_x: int, res_y: int):
    try:
        scene.render.engine = "CYCLES"
    except TypeError:
        scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01 if samples >= 256 else 0.05
    scene.cycles.use_denoising = True
    scene.cycles.device = "GPU"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for dt in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = dt
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            break
        except Exception:
            continue
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.render.use_persistent_data = True
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Punchy"
    except TypeError:
        try:
            scene.view_settings.view_transform = "Filmic"
        except TypeError:
            pass
    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.sample_clamp_indirect = 8.0


def import_meshes(mesh_dir: Path):
    meta_path = mesh_dir / "materials.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {"classes": {}}
    objs = []
    for obj_path in sorted(mesh_dir.glob("*.obj")):
        bpy.ops.wm.obj_import(filepath=str(obj_path))
        ob = bpy.context.selected_objects[0]
        ob.name = obj_path.stem
        key = obj_path.stem.split("_", 1)[0].lstrip("0") or "0"
        info = meta.get("classes", {}).get(key) or meta.get("classes", {}).get(str(int(key)))
        rgb = tuple(info["rgb"]) if info else (0.6, 0.6, 0.6)
        alpha = 0.55 if "alveoli" in obj_path.stem or "nonexpanded" in obj_path.stem else 1.0
        mat = make_material(ob.name, rgb, alpha=alpha)
        if ob.data.materials:
            ob.data.materials[0] = mat
        else:
            ob.data.materials.append(mat)
        objs.append(ob)
    return objs


def bounds_center(objs):
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        for corner in ob.bound_box:
            w = ob.matrix_world @ Vector(corner)
            mins = Vector((min(mins.x, w.x), min(mins.y, w.y), min(mins.z, w.z)))
            maxs = Vector((max(maxs.x, w.x), max(maxs.y, w.y), max(maxs.z, w.z)))
    center = (mins + maxs) * 0.5
    size = (maxs - mins).length
    return center, max(size, 0.01)


def main():
    args = parse_args(sys.argv)
    mesh_dir = Path(args["mesh_dir"] or "")
    out = Path(args["out"] or "")
    assert mesh_dir.is_dir(), mesh_dir
    out.mkdir(parents=True, exist_ok=True)

    clear_scene()
    setup_world()
    objs = import_meshes(mesh_dir)
    center, size = bounds_center(objs)
    setup_lights(center)
    cam = setup_camera(center, radius=size * 1.15)
    scene = bpy.context.scene
    setup_cycles(scene, args["samples"], args["res_x"], args["res_y"])

    # Hero still
    scene.render.filepath = str(out / "hero")
    bpy.ops.render.render(write_still=True)

    # Turntable
    scene.frame_start = 1
    scene.frame_end = args["frames"]
    empty = bpy.data.objects.new("SpinPivot", None)
    bpy.context.collection.objects.link(empty)
    empty.location = center
    for ob in objs:
        ob.parent = empty

    empty.rotation_mode = "XYZ"
    empty.keyframe_insert(data_path="rotation_euler", frame=1)
    empty.rotation_euler[2] = math.radians(360)
    empty.keyframe_insert(data_path="rotation_euler", frame=args["frames"])
    for fc in empty.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

    scene.render.filepath = str(out / "turn_")
    bpy.ops.render.render(animation=True)
    print("RENDER_DONE", out)


if __name__ == "__main__":
    main()
