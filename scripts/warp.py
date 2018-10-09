import os
import argparse
import lib_exe
import lib_msh
import numpy as np
import shutil

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Warps a mesh with a baloon-like object")
    parser.add_argument("-i", "--input",      type=str, help="Mesh to wrap", required=True)
    parser.add_argument("-o", "--output",     type=str, help="Output mesh", required=True)
    parser.add_argument("-t", "--template",   type=str, help="Template to wrap", required=True)
    args = parser.parse_args(sys.argv[1:])

    #checks
    args.template = os.path.abspath(args.template) if args.template else None
    args.input    = os.path.abspath(args.input)
    args.output   = os.path.abspath(args.output)

    #Copy the template to warp
    shutil.copyfile(args.template, "sphere.mesh")

    #Warp
    lib_exe.execute(lib_exe.warping + "%s -p -nit %f -load %f > /dev/null 2>&1" % (args.input, 150, 40) )

    #Clean the mesh and extract the surface
    warped = msh.Mesh("sphere.d.mesh")
    ext_ref = 2
    warped.tris = warped.tris[warped.tris[:,-1] != ext_ref]
    warped.tets = np.array([])
    warped.discardUnused()
    warped.write(args.output)

    #Remove the unused files
    os.remove("sphere.mesh")
    os.remove("sphere.d.mesh")
