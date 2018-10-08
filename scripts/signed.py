import os
import argparse
import sys
import lib_exe
import lib_msh
import numpy as np
from scipy.spatial.distance import cdist
import shutil

def nearest_neighbor(src, dst):
    all_dists = cdist(src, dst, 'euclidean')
    indices = all_dists.argmin(axis=1)
    distances = all_dists[np.arange(all_dists.shape[0]), indices]
    return distances, indices

def adapt_box_to(f, box, maxNb=20000):
    shutil.copyfile(box,"box.mesh")
    cube = lib_msh.Mesh("box.mesh")
    mesh = lib_msh.Mesh(f)
    step = 1 if len(mesh.verts)<maxNb else int(len(mesh.verts)/maxNb)+1
    dists, _ = nearest_neighbor(cube.verts[:,:3], mesh.verts[::step,:3])
    cube.scalars = np.array(dists)
    ABS = np.absolute(cube.scalars)
    mini, maxi = 0.005*np.max(cube.dims), 0.5*np.max(cube.dims)
    cube.scalars = mini + (maxi-mini) * (ABS - np.min(ABS)) / (np.max(ABS) - np.min(ABS))
    cube.write("box.1.mesh")
    cube.writeSol("box.1.sol")
    lib_exe.execute("mmg3d_O3 box.1.mesh -hgrad 1.5  > /dev/null 2>&1")

def create_box(f):
    mesh = lib_msh.Mesh(f)
    cube = lib_msh.Mesh(cube=[mesh.xmin, mesh.xmax, mesh.ymin, mesh.ymax, mesh.zmin, mesh.zmax])
    cube.verts[:,:3] -= mesh.center
    cube.verts[:,:3] *= 1.25
    cube.verts[:,:3] += mesh.center
    cube.write("box.mesh")
    lib_exe.execute( "tetgen -pgANEF box.mesh > /dev/null 2>&1" )
    hausd = 0.04 * np.max(mesh.dims)
    lib_exe.execute( "mmg3d_O3 box.1.mesh -hausd %f -hmax %f > /dev/null 2>&1" % (hausd, hausd) )

def signedDistance(f, box=None):
    if box is not None:
        adapt_box_to(f, box)
    else:
        create_box(f)
    lib_exe.execute( "mshdist -ncpu 16 -noscale box.1.o.mesh " + f + " > /dev/null 2>&1")
    if os.path.exists("box.mesh"): os.remove("box.mesh")
    if os.path.exists("box.1.mesh"): os.remove("box.1.mesh")

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Computes the signed distance to a .mesh file")
    parser.add_argument("-i", "--input",  type=str, help="Input mesh", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output mesh", required=True)
    parser.add_argument("-v", "--volume", type=str, help="Volume mesh to adapt")
    args = parser.parse_args(sys.argv[1:])

    #checks
    args.input  = os.path.abspath(args.input)
    args.output = os.path.abspath(args.output)
    args.volume = os.path.abspath(args.volume) if args.volume is not None else None

    signedDistance(args.input, box=args.volume)
    lib_exe.execute("mv box.1.o.mesh " + args.output)
    lib_exe.execute("mv box.1.o.sol  " + args.output.replace(".mesh",".sol"))
