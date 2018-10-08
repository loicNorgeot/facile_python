import os
import argparse
import lib_exe
import lib_msh
import numpy as np
import shutil
import sys

def intersects(f):
    lib_exe.execute("tetgen -d %s > log.txt" % (f))
    f = open("log.txt","r")
    lines = f.readlines()
    f.close()
    os.remove("log.txt")
    return "No faces are intersecting" not in "".join(f.readlines())

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
    exterior.tris = exterior.tris[exterior.tris[:,-1]!=2]
    exterior.tris[:,3] = 2
    exterior.discardUnused()
    interior.tris[:,3]  = 1
    interior.fondre(exterior)
    interior.write("mask.mesh")
    if intersects("mask.mesh"):
        print("mask is self-intersecting")
        sys.exit(3)
    lib_exe.execute("tetgen -pgaAYNEF mask.mesh > /dev/null 2>&1")
    os.remove("mask.mesh")

    #Remove the inside of the mask
    mesh = lib_msh.Mesh("mask.1.mesh")
    ext_point_ind = np.argmin([np.linalg.norm(x) for x in mesh.verts[:,:3]])
    ext_ref=None
    for t in mesh.tets:
        if ext_point_ind in t[:4]:
            ext_ref = t[-1]
            break
    mesh.tets = mesh.tets[mesh.tets[:,-1]==ext_ref]
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
    mesh.write(args.output)

    #Volume remesh
    lib_exe.execute("mmg3d_O3 %s -o %s -hausd 0.0005 -nosurf -hgrad 1.15 > /dev/null 2>&1" % (args.output, args.output.replace(".mesh", ".o.mesh")))
    os.remove(args.output.replace(".mesh", ".o.sol"))

    #Add a .sol corresponding to the difference between the interior surface and the template
    if args.template:
        template = lib_msh.Mesh(args.template)
        template.tets = np.array([])
        template.tris = template.tris[template.tris[:,-1]==1]
        template.discardUnused()

        mesh = lib_msh.Mesh(args.output.replace(".mesh", ".o.mesh"))
        n = len(mesh.verts)
        mesh.tris = mesh.tris[mesh.tris[:,-1]==1]
        mesh.tets = np.array([])
        mesh.discardUnused()
        mesh.vectors = np.zeros((n,3))
        mesh.vectors[:len(template.verts)] = mesh.verts[:,:3] - template.verts[:,:3] #THIS SHOULD BE REPLACED BY THE RESULTS OF MORPHING

        mesh.writeSol( args.output.replace(".mesh", ".sol") )
        mesh.write( args.output )
