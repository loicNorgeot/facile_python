import os
import argparse
import lib_exe
import lib_msh
import numpy as np
import shutil
import sys
import lib_paths

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
    #lib_exe.execute(lib_paths.wrapping + "-s %s -p -nit %d -load %f > /dev/null 2>&1" % (args.input, 30, 200) )
    lib_exe.execute(lib_paths.wrapping + "-s %s -t %s -p -nit %d -load %f " % (args.input, args.template, 30, 250) )

    #Clean the mesh and extract the surface
    final = None
    try:
        number_max=-1
        for f in [x for x in os.listdir(".") if "sphere.d." in x and ".mesh" in x]:
            number = int(f.split(".")[2])
            if number>number_max:
                final = f
    except:
        final = "sphere.d.mesh"

    warped = lib_msh.Mesh(final)
    warped.tris = warped.tris[warped.tris[:,-1] != 2]
    warped.tets = np.array([])
    warped.discardUnused()
    warped.write(args.output)

    #Remove the unused files
    os.remove("sphere.mesh")
    #os.remove("sphere.d.mesh")
