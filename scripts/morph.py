import os
import argparse
import lib_exe
import lib_msh
import numpy as np
import shutil
import sys

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Morphs a mesh to a signed distance volume")
    parser.add_argument("-t", "--template",   type=str, help="Template to morph", required=True)
    parser.add_argument("-o", "--output",     type=str, help="Output mesh", required=True)
    parser.add_argument("-s", "--signed",     type=str, help="Signed distance to morph to", required=True)
    parser.add_argument("-n", "--iterations", type=int, help="Number of iterations", default=200)
    parser.add_argument("-d", "--icotris",  type=int, help="Icosphere triangles reference", required=True)
    parser.add_argument("-e", "--icotets",     type=int, help="Icosphere tetrahedra reference", required=True)
    parser.add_argument("-b", "--fixtris",      type=int, help="Fixed triangles reference", required=True)

    args = parser.parse_args(sys.argv[1:])

    #checks
    args.template = os.path.abspath(args.template)
    args.signed   = os.path.abspath(args.signed)
    args.output   = os.path.abspath(args.output)

    # dref: Fixed surface inside the template (number + ref)
    # elref: Elements inside the fixed surface
    # bref: Follower elements
    shutil.copyfile(args.template, "template.mesh")
    cmd = lib_exe.morphing + " %s %s -nit %d -dref 1 %d -elref 1 %d -bref 1 %d  > /dev/null 2>&1" % (args.signed, "template.mesh", args.iterations, args.icotris, args.icotets, args.fixtris)
    lib_exe.execute(cmd)

    #Clean the mesh
    mesh = lib_msh.Mesh(args.signed[:-5] + ".1.mesh")
    mesh.readSol(   args.signed[:-5] + ".1.depl.sol")
    mesh.tets = np.array([])
    mesh.tris = mesh.tris[mesh.tris[:,-1]!=10]
    mesh.discardUnused()
    mesh.write(args.output)
    mesh.writeSol(args.output.replace("mesh", "sol"))

    #Remove the temporary files
    os.remove(args.signed[:-5] + ".1.mesh")
    os.remove(args.signed[:-5] + ".1.depl.sol")
