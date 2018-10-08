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

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Aligns .mesh files together")
    parser.add_argument("-s", "--source",    type=str, help="Source .mesh file (from)", required=True)
    parser.add_argument("-t", "--target",    type=str, help="Target .mesh file (to)", required=True)
    parser.add_argument("-f", "--followers", type=str, nargs="+", help="Other files to align accordingly")
    parser.add_argument("--icp", action="store_true", help="Run a ICP on the models")
    args = parser.parse_args(sys.argv[1:])

    #check
    mesh = lib_msh.Mesh(args.input)
    if args.center:
        mesh.verts[:,:3] -= mesh.center
        if args.scale:
            mesh.verts[:,:3] *= args.scale
        else:
            mesh.verts[:,:3] *= 1. / np.max(mesh.dims)
        mesh.verts[:,:3] += [0.5,0.5,0.5]
    else:
        if args.scale:
            mesh.verts[:,:3] -= mesh.center
            mesh.verts[:,:3] *= args.scale
            mesh.verts[:,:3] += mesh.center
        if args.translate:
            mesh.verts[:,:3] += args.translate
    mesh.write(args.output)
