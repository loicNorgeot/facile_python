import os
import argparse
import sys
import lib_exe
import lib_msh
import numpy as np

@lib_exe.debug()
def to_mesh(f, output):

    #Convert a stl to mesh with meshlabserver
    meshlabScript = os.path.join( os.path.dirname(os.path.abspath(__file__)), "meshlab_scripts", "cleanSTL.mlx")
    tmp = f.replace(".stl", ".obj")
    cmd = "LC_ALL=C meshlabserver -i " + f + " -o " + tmp + " -s " + meshlabScript + " > /dev/null 2>&1"
    print(cmd)
    err = os.system(cmd)
    f = tmp

    #Convert a .obj to .mesh
    with open(f, "r") as _f:
        LINES = _f.readlines()
        mesh = lib_msh.Mesh()
        mesh.verts = np.array([ [float(x) for x in l.split()[1:]] for l in LINES if l[0]=="v" ])
        mesh.tris  = np.array([ [int(x)-1 for x in l.split()[1:]]   for l in LINES if l[0]=="f" ])
        mesh.verts = np.insert(mesh.verts,3,0,axis=1)
        mesh.tris  = np.insert(mesh.tris,3,0,axis=1)
        mesh.computeBBox()
        mesh.write(output)

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Convert .obj and .stl files to .mesh")
    parser.add_argument("-i", "--input",  type=str, help="Input .obj or .stl", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output .mesh")
    args = parser.parse_args(sys.argv[1:])

    #check
    args.input  = os.path.abspath(args.input)
    if args.output is not None and args.output.endswith("mesh"):
        args.output = os.path.abspath(args.output)
    else:
        args.output = args.input.replace(os.path.splitext(args.input)[1],".mesh")

    if os.path.exists(args.input) and os.path.splitext(args.input)[1] in [".obj", ".stl"]:
        to_mesh(args.input, args.output)
