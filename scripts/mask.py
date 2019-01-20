import os
import argparse
import lib_exe
import lib_msh
import numpy as np
import shutil
import sys

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
    parser = argparse.ArgumentParser(description="Creates a mask based on interior and exterior surface")
    parser.add_argument("-i", "--interior",   type=str, help="Interior surface", required=True)
    parser.add_argument("-e", "--exterior",   type=str, help="Exterior surface", required=True)
    parser.add_argument("-t", "--template",   type=str, help="Template used for the interior surface")
    parser.add_argument("-o", "--output",     type=str, help="Output mesh", required=True)
    args = parser.parse_args(sys.argv[1:])

    #checks
    args.interior = os.path.abspath(args.interior)
    args.exterior = os.path.abspath(args.exterior)
    args.output   = os.path.abspath(args.output)
    if args.template:
        args.template = os.path.abspath(args.template)


    #check for intersections
    if intersects(args.interior):
        print("interior surface is self-intersecting")
        sys.exit(1)
    if intersects(args.exterior):
        print("exterior surface is self-intersecting")
        sys.exit(2)

    #Merge the meshes and run tetgen
    exterior, interior = lib_msh.Mesh(args.exterior), lib_msh.Mesh(args.interior)
    #exterior.tris = exterior.tris[exterior.tris[:,-1]!=2]
    exterior.tris[:,-1] = 2
    exterior.discardUnused()
    interior.tris[:,-1]  = 1
    interior.fondre(exterior)
    interior.write("mask.mesh")

    if intersects("mask.mesh"):
        print("mask is self-intersecting")
        sys.exit(3)

    #Run tetgen
    lib_exe.execute(lib_exe.tetgen + "-pgaANEFY mask.mesh")
    for f in os.listdir("."):
        if 'mask' in f and ".mesh" not in f and ".py" not in f:
            os.remove(f)

    lib_exe.execute(lib_exe.mmg3d + "-nosurf -nr -hgrad 1.75 mask.1.mesh -out mask.1.o.mesh") #Because the number of triangles is not good, therefore tetrahedra re not read!!
    os.remove("mask.1.o.sol")
    os.remove("mask.mesh")
    os.remove("mask.1.mesh")

    #Remove the inside of the mask
    mesh = lib_msh.Mesh("mask.1.o.mesh")
    ext_point_ind = np.argmin(mesh.verts[:,:3], axis=0)[0]
    ext_ref=None
    for t in mesh.tets:
        if ext_point_ind in t[:4]:
            ext_ref = t[-1]
            break
    mesh.tets = mesh.tets[mesh.tets[:,-1]==ext_ref]
    mesh.discardUnused()
    mesh.tets[:,4] = 2
    for t in mesh.tris:
        if ext_point_ind in t[:3]:
            ext_ref = t[-1]
            break
    mesh.tris = mesh.tris[mesh.tris[:,3]>0]
    M = mesh.tris[:,-1]==ext_ref
    mesh.tris[M==1][:,3] = 1
    mesh.tris[M==0][:,3] = 0
    mesh.discardUnused()
    for t in mesh.tris:
        if t[-1]==1:
            for i in t[:3]:
                mesh.verts[i,-1]=1
    #Write the mask
    mesh.write("mask.2.mesh")
    os.remove("mask.1.o.mesh")

    #Volume remesh
    lib_exe.execute("mmg3d_O3 %s -o %s -hausd 0.005 -nosurf -nr -hgrad 1.75 > /dev/null 2>&1" % ("mask.2.mesh", args.output))
    os.remove(args.output.replace(".mesh", ".sol"))
    os.remove("mask.2.mesh")


    #Add a .sol corresponding to the difference between the interior surface and the template

    mesh = lib_msh.Mesh(args.output)

    if args.template:
        print("We're here")
        template = lib_msh.Mesh(args.template)
        template.tets = np.array([])
        template.discardUnused()

        n = len(mesh.verts)
        mesh.vectors = np.zeros((n,3))
        mesh.vectors[:len(template.verts)] = template.verts[:,:3] - mesh.verts[:len(template.verts),:3] #THIS SHOULD BE REPLACED BY THE RESULTS OF MORPHING

        mesh.writeSol( args.output.replace(".mesh", ".sol") )
        mesh.write( args.output )
