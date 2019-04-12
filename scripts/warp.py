import os
import argparse
import lib_exe
import lib_msh
import numpy as np
import shutil
import sys
import lib_paths


def intersects(f):
    lib_exe.execute(lib_exe.tetgen + "-d %s > log.txt" % (f))
    res = True
    with open("log.txt","r") as f:
        lines = f.readlines()
        if "No faces are intersecting" in "".join(lines):
            res = False
        else:
            res = True
    os.remove("log.txt")
    return res

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
    NIT = 50
    #lib_exe.execute(lib_paths.wrapping + "-s %s -p -nit %d -load %f > /dev/null 2>&1" % (args.input, NIT, 200) )
    #lib_exe.execute(lib_paths.wrapping + "-s %s -t %s -p -nit %d -load %f " % (args.input, args.template, NIT, 200) )
    lib_exe.execute(lib_paths.wrapping + "-s %s -p -nit %d -load %f " % (args.input, NIT, 200) )

    #Clean the mesh and extract the surface
    chemin = args.template
    final = None
    try:
        number_max=NIT
        for f in [x for x in os.listdir(".") if "sphere.d." in x and ".mesh" in x]:
            number = int(f.split(".")[2])
            if number>number_max:
                final = f
                #final = chemin.replace("sphere.mesh", f)
        if final!=None:
            while intersects(final):
                number_max=number_max-1
                for f in [x for x in os.listdir(".") if "sphere.d." in x and ".mesh" in x]:
                    number = int(f.split(".")[2])
                    if number==number_max:
                        final = f
                        #final = chemin.replace("sphere.mesh", f)
    except:
        final = "sphere.d.mesh"

    warped = lib_msh.Mesh(final)
    warped.tris = warped.tris[warped.tris[:,-1] != 2]
    warped.tets = np.array([])
    warped.discardUnused()
    warped.write(args.output)

    #Remove the unused files
    # for f in [x for x in os.listdir("./TEMPLATES") if "sphere.d." in x and ".mesh" in x]:
    #     os.remove(chemin.replace("sphere.mesh", f))
    # for f in [x for x in os.listdir("./TEMPLATES") if "sphere.d." in x and ".node" in x]:
    #     os.remove(chemin.replace("sphere.mesh", f))
    # for f in [x for x in os.listdir("./TEMPLATES") if "sphere.d." in x and ".face" in x]:
    #     os.remove(chemin.replace("sphere.mesh", f))
    #os.remove("sphere.d.mesh")
