import bpy
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lib_msh

def import_mesh(filepath):
    MESH = lib_msh.Mesh(filepath)
    if os.path.exists(filepath[:-5]+".sol"):
        MESH.readSol()
    MESH.tets = lib_msh.np.array([])
    MESH.discardUnused()

    meshes = []
    rTris = MESH.tris[:,-1].tolist() if len(MESH.tris)>0 else []
    rQuads = MESH.quads[:,-1].tolist() if len(MESH.quads)>0 else []
    tris = [t.tolist() for t in MESH.tris]
    quads = [q.tolist() for q in MESH.quads]
    verts = [v.tolist()[:-1] for v in MESH.verts]
    REFS = set(rTris + rQuads)

    for i,r in enumerate(REFS):
        refFaces = [t[:-1] for t in tris + quads if t[-1]==r]
        mesh_name = bpy.path.display_name_from_filepath(filepath)
        mesh = bpy.data.meshes.new(name=mesh_name)
        meshes.append(mesh)
        mesh.from_pydata(verts, [], refFaces)
        mesh.validate()
        mesh.update()

    scene = bpy.context.scene

    objects = []
    for i,m in enumerate(meshes):
        obj = bpy.data.objects.new(m.name, m)
        bpy.ops.object.select_all(action='DESELECT')
        scene.objects.link(obj)
        scene.objects.active = obj
        objects.append(obj)
    del meshes

    scene.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        o.select=True
    bpy.ops.object.join()
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.remove_doubles()
    bpy.ops.object.editmode_toggle()

def export_mesh(filepath):
    #Get the selected object
    APPLY_MODIFIERS = True
    scene = bpy.context.scene
    bpy.ops.object.duplicate()
    obj = scene.objects.active

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER')
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_face_by_sides(number=3, type='GREATER')
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.object.editmode_toggle()

    mesh = obj.to_mesh(scene, APPLY_MODIFIERS, 'PREVIEW')
    mesh.transform(obj.matrix_world)

    #Get the info
    verts = [[v.co[0], v.co[1], v.co[2], 0] for v in mesh.vertices[:]]
    triangles = [ [v for v in f.vertices] + [f.material_index + 1] for f in mesh.polygons if len(f.vertices) == 3 ]
    quads = [ [v for v in f.vertices] + [f.material_index + 1]  for f in mesh.polygons if len(f.vertices) == 4 ]
    edges = [[e.vertices[0], e.vertices[1], 0] for e in mesh.edges if e.use_edge_sharp]

    exportMesh = lib_msh.Mesh()
    exportMesh.verts = lib_msh.np.array(verts)
    exportMesh.tris  = lib_msh.np.array(triangles)
    exportMesh.quads = lib_msh.np.array(quads)
    exportMesh.edges = lib_msh.np.array(edges)
    exportMesh.write(filepath)

#Create an arguments parser
parser = argparse.ArgumentParser(description="Remesh a scan to a lowpoly model in blender")
parser.add_argument("-i", "--input",  dest="input",  type=str, metavar='FILE', required=True, help="Input model")
parser.add_argument("-o", "--output", dest="output", type=str, metavar='FILE', required=True, help="Output model")
parser.add_argument("-x", type=int, required=True, help="Positive or negative x (+1 or -1)")

argv = sys.argv[sys.argv.index("--") + 1:]
args = parser.parse_args(argv)

#Check their validity
if not os.path.exists(args.input):
    print("ERROR: " + args.input + " is not a valid file")
    sys.exit(1)
args.input = os.path.abspath(args.input)
if args.output.split(".")[-1]!="mesh":
    print("ERROR: " + args.output + " must be a .mesh file")
    sys.exit(1)
args.output = os.path.abspath(args.output)
if args.x==1 or args.x==-1:
    pass
else:
    print("x must be 1 or -1")
    sys.exit(1)

#Remove the delete file objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

import_mesh(args.input)

mesh = bpy.context.active_object
if args.x == 1:
    bpy.ops.mesh.primitive_cube_add(radius=1000, location=(-1000, 0, 0))
else:
    bpy.ops.mesh.primitive_cube_add(radius=1000, location=(1000, 0, 0))

cube = bpy.context.active_object
bpy.context.scene.objects.active = mesh

#remove objects but mesh
for o in bpy.data.objects:
    if o!=mesh:
        bpy.data.objects.remove(o)

#align the right side to the left
if args.x == 1:

    mesh.select = True
    bpy.ops.transform.resize(value=(-1, 1, 1))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()

export_mesh(args.output)
