"""
Convert a .obj or a .stl to .mesh file, or all files inside a directory

python convert_stl_to_mesh.py -i /path/to/
or
python convert_stl_to_mesh.py -i /path/to/myModel.obj
"""

import os
import argparse
import sys
import lib_exe
import lib_msh
import numpy as np
import shutil

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Aligns .mesh files together")
    parser.add_argument("-i", "--input",    type=str,   help="Input mesh", required=True)
    parser.add_argument("-o", "--output",   type=str,   help="Output mesh", required=True)
    parser.add_argument("-d", "--distance", type=float, help="Hausdorff distance", default=0.01)
    parser.add_argument("-l", "--levelset", type=float, help="Levelset value", default=0)
    args = parser.parse_args(sys.argv[1:])

    #checks
    args.input  = os.path.abspath(args.input)
    args.output = os.path.abspath(args.output)

    lib_exe.execute("mmg3d_O3 %s -ls %f -hausd %f -o tmp.mesh" % (args.input, args.levelset, args.distance))

    mesh = lib_msh.Mesh("tmp.mesh")
    mesh.tets = np.array([])
    mesh.tris = mesh.tris[mesh.tris[:,-1]==10]
    mesh.discardUnused()
    mesh.write(args.output)

    os.remove("tmp.mesh")
    os.remove("tmp.sol")
