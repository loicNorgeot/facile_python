import os
import lib_msh
import lib_exe
import sys
import argparse

def intersects(f):
    lib_exe.execute("tetgen -d %s > log.txt" % (f))
    f = open("log.txt","r")
    lines = f.readlines()
    f.close()
    os.remove("log.txt")
    return "No faces are intersecting" not in "".join(f.readlines())

if __name__=="__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Fill a surface with an icosphere")
    parser.add_argument("-i", "--input", help="input .mesh file", type=str, required=True)
    parser.add_argument("-o", "--output", help="transformed .mesh file", type=str, required=True)
    parser.add_argument("-c", "--center", help="center of the icosphere", type=float, nargs=3)
    parser.add_argument("-r", "--radius", help="radius of the icosphere", type=float, default=0.1)
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print args.input + " is not a valid file"
        sys.exit()
    if not os.path.splitext(args.input)[1] == ".mesh":
        print args.input + " is not a .mesh file"
        sys.exit()
    if not os.path.splitext(args.output)[1] == ".mesh":
        print "Output file must be in the .mesh format"
        sys.exit()
    if intersects(args.input):
        print args.input + " has intersecting facets"
        sys.exit()

    mesh = lib_msh.Mesh(args.input)
    ico  = lib_msh.Mesh(ico=[args.center,args.radius])
    ico.tris[:,-1]=10
    mesh.fondre(ico)
    mesh.write("out.mesh")
    lib_exe.execute("tetgen -pgANEF out.mesh")
    lib_exe.execute("mmg3d_O3 out.1.mesh -nosurf -o " + args.output)
    os.remove("out.mesh")
    os.remove("out.1.mesh")
    os.remove(args.output.replace(".mesh", ".sol"))
