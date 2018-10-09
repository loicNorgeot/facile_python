import os
import argparse
import sys
import lib_exe
import lib_msh
import numpy as np
import shutil

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Creates a shell for warping")
    parser.add_argument("-i", "--input", help="input .mesh file", type=str, required=True)
    parser.add_argument("-o", "--output", help="transformed .mesh file", type=str, required=True)
    parser.add_argument("-int", "--interiorIsovalue", help="ratio to the maximum dimension for the interior shell surface distance to the mesh", type=float, default=20)
    parser.add_argument("-ext", "--exteriorIsovalue", help="ratio to the maximum dimension for the exterior shell surface distance to the mesh", type=float, default=10)
    args = parser.parse_args()

    #checks
    if not os.path.isfile(args.input):
        print (args.input + " is not a valid file")
        sys.exit()
    if not os.path.splitext(args.input)[1] == ".mesh":
        print (args.input + " is not a .mesh file")
        sys.exit()
    if not os.path.splitext(args.output)[1] == ".mesh":
        print ("Output file must be in the .mesh format")
        sys.exit()
    if args.interiorIsovalue < args.exteriorIsovalue:
        print ("The inner shell must be closer than the outer shell")
        sys.exit()
    if args.interiorIsovalue<5 or args.exteriorIsovalue<5:
        print ("The shell must be closer than maxDim/5")
        sys.exit()
    args.input  = os.path.abspath(args.input)
    args.output = os.path.abspath(args.output)

    #Carve the input mesh
    lib_exe.execute( lib_exe.python_cmd("carve.py") + "-i %s -o %s -r %d" % (args.input, args.output.replace(".mesh",".carved.mesh"), 31) )

    #Create a box and mesh it to compute the signed distance on
    mesh = lib_msh.Mesh(args.input)
    c = np.max(mesh.dims)/8
    cube = lib_msh.Mesh(cube=[mesh.xmin-c,
        mesh.xmax+c,
        mesh.ymin-c,
        mesh.ymax+c,
        mesh.zmin-c,
        mesh.zmax+c])
    cube.write("box.mesh")
    lib_exe.execute(lib_exe.tetgen + "-pgANEF %s" % ("box.mesh"))
    lib_exe.execute( lib_exe.mmg3d + "%s -hausd %f -hmax %f" % ("box.1.mesh", np.max(mesh.dims)/50, np.max(mesh.dims)/25) )

    #Compute the signed distance to the carved object
    lib_exe.execute(lib_exe.mshdist + "-ncpu 16 -noscale %s %s"  % ("box.1.o.mesh", args.output.replace(".mesh",".carved.mesh")))

    #Extracting the isovalues meshes
    #Exterior one
    lib_exe.execute(lib_exe.mmg3d + "%s -nr -ls %f -hausd %f -out %s" % ("box.1.o.mesh", np.max(mesh.dims)/args.exteriorIsovalue, np.max(mesh.dims)/50, "iso1.mesh"))
    iso1 = lib_msh.Mesh("iso1.mesh")
    iso1.tets = np.array([])
    iso1.removeRef(0)
    iso1.discardUnused()
    #Interior one
    lib_exe.execute(lib_exe.mmg3d + "%s -nr -ls %f -hausd %f -out %s" % ("box.1.o.mesh", np.max(mesh.dims)/args.interiorIsovalue, np.max(mesh.dims)/50, "iso2.mesh"))
    iso2 = lib_msh.Mesh("iso2.mesh")
    iso2.tets = np.array([])
    iso2.removeRef(0)
    iso2.discardUnused()
    #Merging meshes
    iso1.replaceRef(10,1)
    iso2.replaceRef(10,2)
    iso1.fondre(iso2)
    iso1.write("iso3.mesh")

    #Volume meshing
    lib_exe.execute(lib_exe.tetgen + "-pgaYAq1.02 iso3.mesh")
    for f in os.listdir("."):
        if 'iso3' in f and ".mesh" not in f:
            os.remove(f)
    lib_exe.execute(lib_exe.mmg3d + "-nosurf iso3.1.mesh -out iso3.1.o.mesh")#Because the number of triangles is not good, therefore tetrahedra re not read!!
    os.remove("iso3.1.o.sol")

    final = lib_msh.Mesh("iso3.1.o.mesh")
    #Remove the center volume
    ext_point_ind = np.argmin(final.verts[:,:3], axis=0)[0]
    ext_ref=None
    for t in final.tets:
        if ext_point_ind in t:
            ext_ref = t[-1]
            break
    final.tets = final.tets[final.tets[:,-1]==ext_ref]
    final.discardUnused()
    final.write("iso3.1.o.mesh")

    #Last volume remesh
    lib_exe.execute(lib_exe.mmg3d + "%s -nr -hausd %f -o %s" % ("iso3.1.o.mesh", np.max(final.dims)/500, args.output) )

    #Clean the workspace
    for f in ["box.mesh", "box.1.mesh", "box.1.o.mesh", "box.1.o.sol", "iso1.mesh", "iso1.sol", "iso2.sol", "iso2.mesh",  args.output.replace(".mesh",".carved.mesh"), args.output.replace(".mesh",".sol")]:
        os.remove(f)
    for f in ["iso3.mesh", "iso3.1.mesh", "iso3.1.o.mesh"]:
        os.remove(f)
