import os
import argparse
import sys
import lib_exe
import lib_msh
import numpy as np

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Translates and scales a .mesh file")
    parser.add_argument("-i", "--input",     type=str, help="Input .mesh files", required=True)
    parser.add_argument("-o", "--output",    type=str, help="Output .mesh file", required=True)
    parser.add_argument("-s", "--scale",     type=float, nargs=3, help="Scale ( x y z )")
    parser.add_argument("-t", "--translate", type=float, nargs=3, help="Translation ( x y z )")
    parser.add_argument("-c", "--center",    action="store_true", help="Center and scale to [.5, .5, .5]")
    parser.add_argument("-m", "--matrix",    type=str, nargs="+", help="Matrix file(s)")
    args = parser.parse_args()

    #check
    args.input = os.path.abspath(args.input)
    if not os.path.exists(args.input):
        print("No input file")
        sys.exit(1)
    if args.matrix:
        for i,m in enumerate(args.matrix):
            args.matrix[i] = os.path.abspath(m)
            if not os.path.exists(m):
                print("No matrix file", m)
                sys.exit(1)

    #apply
    mesh = lib_msh.Mesh(args.input)
    if args.matrix:
        for matrix in args.matrix:
            mesh.applyMatrix(matFile = matrix)
    else:
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
