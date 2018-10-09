import os
import argparse
import lib_exe
import lib_msh
import numpy as np
import shutil

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Morphs a mesh to a signed distance volume")
    parser.add_argument("-t", "--template",   type=str, help="Template to morph", required=True)
    parser.add_argument("-o", "--output",     type=str, help="Output mesh", required=True)
    parser.add_argument("-s", "--signed",     type=str, help="Signed distance to morph to", required=True)
    parser.add_argument("-n", "--iterations", type=int, help="Number of iterations", default=200)
    args = parser.parse_args(sys.argv[1:])

    #checks
    args.template = os.path.abspath(args.template)
    args.signed   = os.path.abspath(args.signed)
    args.output   = os.path.abspath(args.output)

    #dref: Fixed surface inside the template (number + ref) elref: Elements inside the fixed surface bref: Follower elements
    shutil.copyfile(args.template, "template.mesh")
    cmd = lib_exe.morphing + "-dref 1 2 -elref 1 2 -nit %d %s %s > /dev/null 2>&1" % (args.iterations, args.signed, "template.mesh")
    lib_exe.execute(cmd)

    #Clean the mesh
    mesh = msh.Mesh(args.signed[:-5] + ".1.mesh")
    mesh.readSol(   args.signed[:-5] + ".1.depl.sol")
    mesh.tets = np.array([])
    mesh.discardUnused()
    mesh.write(args.output)
    mesh.writeSol(args.output.replace("mesh", "sol"))

    #Remove the temporary files
    os.remove(args.signed[:-5] + ".1.mesh")
    os.remove(args.signed[:-5] + ".1.depl.sol")
