"""
Launches tests on demo data and on every script available, to see if some bugs were introduced.
"""

import lib_exe
import lib_msh
import os
import argparse
import numpy as np



if __name__ == "__main__":
    # 0 - arguments
    parser = argparse.ArgumentParser(description="Scripts testing")
    parser.add_argument("-d", "--directory", type=str, help="directory containing the data to test", required=True)
    parser.add_argument("-m", "--medit", action="store_true", help="visualize each result with medit")
    args = parser.parse_args()
    args.directory = os.path.abspath(args.directory)

    # 1 - Carve a .mesh object
    print("Testing carve.py")
    IN  = os.path.join(args.directory, "buddha.mesh")
    OUT = os.path.join(args.directory, "buddha.carved.mesh")
    lib_exe.execute( lib_exe.python_cmd("carve.py") + "-i %s -o %s -r %d" % (IN, OUT, 31))
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (OUT))
    os.remove(OUT)

    # 2 - convert .obj and .stl objects to .mesh
    print("Testing convert.py")
    IN1  = os.path.join(args.directory, "buddha.obj")
    OUT1 = os.path.join(args.directory, "buddha1.mesh")
    lib_exe.execute( lib_exe.python_cmd("convert.py") + "-i %s -o %s" % (IN1, OUT1))
    IN2  = os.path.join(args.directory, "buddha.stl")
    OUT2 = os.path.join(args.directory, "buddha2.mesh")
    lib_exe.execute( lib_exe.python_cmd("convert.py") + "-i %s -o %s" % (IN2, OUT2))
    if args.medit: lib_exe.execute(lib_exe.medit + "%s %s" % (OUT1, OUT2))
    buddha1 = lib_msh.Mesh(OUT1)
    buddha2 = lib_msh.Mesh(OUT2)
    assert( len(buddha1.verts) == len(buddha2.verts) )
    assert( buddha1.verts[0][1] == buddha2.verts[0][1] )
    assert( buddha1.tris[10][2] == buddha2.tris[10][2] )
    os.remove(OUT1)
    os.remove(OUT2)

    # 3 - compute the distance between two meshes
    print("Testing distance.py")
    IN1 = os.path.join(args.directory, "buddha.mesh")
    IN2 = os.path.join(args.directory, "buddha.displaced.mesh")
    OUT = os.path.join(args.directory, "buddha.distance.mesh")
    lib_exe.execute( lib_exe.python_cmd("distance.py") + "-i1 %s -i2 %s -o %s" % (IN1, IN2, OUT) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (OUT))
    os.remove(OUT)
    os.remove(OUT.replace(".mesh", ".sol"))

    # 4 - Fill a mesh for morphing
    print("Testing fill.py")
    IN1 = os.path.join(args.directory, "buddha.mesh")
    OUT = os.path.join(args.directory, "buddha.filled.mesh")
    lib_exe.execute( lib_exe.python_cmd("fill.py") + "-i %s -o %s -c %f %f %f -r %f" % (IN, OUT, 0., .5, 0., .5 ) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (OUT))
    buddha = lib_msh.Mesh(OUT)
    assert( len(buddha.tets) != 0 )
    os.remove(OUT)

    # 5 - Run an ICP (and test transform)
    print("Testing icp.py (and transform.py)")
    SOURCE = os.path.join(args.directory, "buddha.offset.mesh")
    TARGET = os.path.join(args.directory, "buddha.mesh")
    MATFILE = os.path.join(args.directory, "matrix_icp.txt")
    OUT = os.path.join(args.directory, "buddha.icped.mesh")
    lib_exe.execute( lib_exe.python_cmd("icp.py") + "-s %s -t %s -m %s" % (SOURCE, TARGET, MATFILE) )
    lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -m %s" % (SOURCE, OUT, MATFILE) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s %s" % (TARGET, OUT))
    source = lib_msh.Mesh(SOURCE)
    target = lib_msh.Mesh(TARGET)
    result = lib_msh.Mesh(OUT)
    #Check if the total error between target and result is far below total error between source and target
    erraftericp = np.sum( np.linalg.norm( target.verts[:,:3] - result.verts[:,:3] ) )
    erroriginal = np.sum( np.linalg.norm( target.verts[:,:3] - source.verts[:,:3] ) )
    assert(erraftericp < 1000 * erroriginal)
    os.remove(OUT)
    os.remove(MATFILE)

    # 6 - Create a shell around buddha
    print("Testing shell.py")
    IN     = os.path.join(args.directory, "buddha.mesh")
    OUT    = os.path.join(args.directory, "buddha.shell.mesh")
    lib_exe.execute( lib_exe.python_cmd("shell.py") + "-i %s -o %s -int %f -ext %f" % (IN, OUT, 20, 10) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (OUT))
    shell = lib_msh.Mesh(OUT)
    assert( len(shell.tets != 0) )
    assert( len(set(shell.tris[:,-1])) == 2 )
    os.remove(OUT)

    # 7 - Merge two buddha meshes
    IN1 = os.path.join(args.directory, "buddha.mesh")
    IN2 = os.path.join(args.directory, "buddha.mesh")
    OUT    = os.path.join(args.directory, "buddha.merged.mesh")
    lib_exe.execute( lib_exe.python_cmd("merge.py") + "-i %s %s -o %s" % (IN1, IN2, OUT) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (OUT))
    assert( len(lib_msh.Mesh(OUT).tris) == len(lib_msh.Mesh(IN1).tris) + len(lib_msh.Mesh(IN2).tris) )
    os.remove(OUT)

    # 8 - Get a signed distance and levelset it
    print("Testing signed.py and levelset.py")
    IN  = os.path.join(args.directory, "buddha.mesh")
    OUT = os.path.join(args.directory, "buddha.signed.mesh")
    lib_exe.execute( lib_exe.python_cmd("signed.py") + "-i %s -o %s" % (IN, OUT) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (OUT))
    signed = lib_msh.Mesh(OUT)
    signed.readSol()
    assert( len(signed.tets)>0 )
    assert( len(signed.scalars)>0 )
    LVL = os.path.join(args.directory, "buddha.levelset.mesh")
    lib_exe.execute( lib_exe.python_cmd("levelset.py") + "-i %s -o %s -l %f -r %d" % (OUT, LVL, 0., 3) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (LVL))
    levelset = lib_msh.Mesh(LVL)
    assert(len(levelset.tets) == 0)
    assert(levelset.tris[0,-1] == 3)
    os.remove(OUT)
    os.remove(OUT.replace(".mesh", ".sol"))
    os.remove(LVL)

    # 9 - Split buddha in half
    print("Testing split.py")
    IN   = os.path.join(args.directory, "buddha.mesh")
    OUTR = os.path.join(args.directory, "buddha.R.mesh")
    OUTL = os.path.join(args.directory, "buddha.L.mesh")
    lib_exe.execute( lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" % (IN, OUTR, +1) )
    lib_exe.execute( lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" % (IN, OUTL, -1) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s %s" % (OUTR, OUTL))
    left  = lib_msh.Mesh(OUTL)
    right = lib_msh.Mesh(OUTR)
    assert( np.max(left.verts[:,0]) <= 1e-3 )
    assert( np.max(right.verts[:,0]) <= 1e-2 )
    os.remove(OUTR)
    os.remove(OUTL)

    # 10  Create a mask from a known object
    print("Testing mask.py")
    IN    = os.path.join(args.directory, "buddha.mesh")
    SHELL = os.path.join(args.directory, "buddha.outermask.mesh")
    OUT   = os.path.join(args.directory, "buddha.masked.mesh")
    lib_exe.execute( lib_exe.python_cmd("mask.py") + "-i %s -e %s -o %s" % (IN, SHELL, OUT) )
    if args.medit: lib_exe.execute(lib_exe.medit + "%s" % (OUT))
    mask  = lib_msh.Mesh(OUT)
    assert( len(mask.tets != 0) )
    assert( len(set(mask.tris[:,-1])) == 2 )
    os.remove(OUT)

    # 11 - Others
    print("Must test warp.py")
    print("Must test morph.py")
    print("Must test pca.py")
