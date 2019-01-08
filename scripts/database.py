"""
python3 database.py -d FILES/ -t TEMPLATES/
"""

import lib_exe
import lib_msh
import os
import argparse
from shutil import copyfile
import sys
import numpy as np

from lib_paths import *

MERGEMASSETERSTOO = False

#arguments
def get_arguments():
    parser = argparse.ArgumentParser(description="Whole database creation")
    parser.add_argument("-d", "--directory", type=str, help="directory to process the files in", required=True)
    parser.add_argument("-t", "--templates", type=str, help="directory for the templates", required=True)
    args = parser.parse_args()
    args.directory = os.path.abspath(args.directory)
    args.templates = os.path.abspath(args.templates)
    return args

#templates and directories
def create_templates_and_directories(args):
    #Create the paths for the template files
    templateNames = ["masseter", "mandible", "bone", "sphere", "morphing", "morphingSkull", "box"]
    templates     = {}
    for d in templateNames:
        templates[d] = os.path.abspath(os.path.join(args.templates, d + ".mesh"))

    #Create the directories to process files into
    dirNames = [
        #"raw",
        "mesh",
        "scaled",
        "remeshed",
        "merged",
        "aligned",
        "warped",
        "filled",
        "signed",
        "masked",
        "morphed",
        "splitted",
        "muscles",
        "reconstruction"
    ]
    directories    = {}
    for d in dirNames:
        directories[d] = os.path.abspath(os.path.join(args.directory, d))
        if not os.path.exists(directories[d]):
            os.makedirs(directories[d])

    return templates, directories

if __name__ == "__main__":
    args = get_arguments()
    templates, directories = create_templates_and_directories(args)

    ################################################################################
    # 1 - Create the database
    ################################################################################

    # 1 - Download all the files from the FTP server
    """
    IP  = "134.157.66.224"
    USR = "norgeot"
    PWD = "*******"
    DIR = "Projets/FaciLe/Data/AllDataRaw"
    OUT = directories["raw"]
    lib_exe.execute( lib_exe.python_cmd("download.py") + "-a %s -u %s -p %s -i %s -o %s" % (IP, USR, PWD, DIR, OUT))
    """

    # 2 - Convert all the downloaded files to .mesh
    """
    def convert(f):
        IN  = os.path.join(directories["raw"], f)
        OUT = os.path.join(directories["mesh"], f.replace("obj","mesh").replace("stl","mesh"))
        lib_exe.execute( lib_exe.python_cmd("convert.py") + "-i %s -o %s" % (IN, OUT))
    FILES = [f for f in os.listdir(directories["raw"]) if os.path.splitext(f)[1] in [".obj", ".stl"]]
    FILES = [f for f in FILES if f.replace(".obj", ".mesh").replace(".stl",".mesh") not in os.listdir(directories["mesh"])]
    lib_exe.parallel(convert, FILES)
    """

    # 3 - Check maurice which objects are misaligned
    def check(group):
        centerskull = lib_msh.Mesh(os.path.join(EVERYTHING, group[0])).center
        centerskin  = lib_msh.Mesh(os.path.join(EVERYTHING, group[1])).center
        def distance(a,b):
            return ( (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2 ) **0.5
        if distance(centerskin, centerskull)>50:
            print(group)
    cases = set([f.split("-")[0] for f in os.listdir(EVERYTHING)])
    GROUPS = [[f for f in os.listdir(EVERYTHING) if f.startswith(case) and f.endswith(".mesh") and ("Skin" in f or "Skull" in f)] for case in cases]
    lib_exe.parallel(check, GROUPS)

    # 4 - Merge the bones (skull, mandibles and teeth) together
    """
    def merge(group):
        OUT   = os.path.join(directories["merged"], group[0][:6] + "Skull.mesh")
        lib_exe.execute( lib_exe.python_cmd("merge.py") + "-i %s -o %s" % (" ".join([os.path.join(directories["mesh"], g) for g in group]), OUT))
    cases = set([f.split("-")[0] for f in os.listdir(directories["mesh"]) if ".mesh" in f and f[0]!="."])
    GROUPS = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case) and f.endswith(".mesh") and "Mass" not in f and "Skin" not in f] for case in cases]
    lib_exe.parallel(merge, GROUPS)
    """

    # 5 - Scale everything
    """
    def scale(group):

        #Start here
        skull = [g for g in group if "Skull" in g][0]
        # 1 - Translate everything so that the center of the skull is on 0,0,0
        centerskull = lib_msh.Mesh(os.path.join(directories["merged"], skull)).center
        for g in group:
            IN    = os.path.join(directories["merged"], g)
            TMP1  = os.path.join(directories["scaled"], "tmp1_%s" % g )
            # Translate everything so that the center of the skull is on 0,0,0
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (IN, TMP1, -centerskull[0], -centerskull[1], -centerskull[2]) )
            # Scale by 0.0035
            S = 0.0035
            TMP2  = os.path.join(directories["scaled"], "tmp2_%s" % g )
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -s %f %f %f" % (TMP1, TMP2, S, S, S) )
            # Translate to 0.5 0.5 0.5
            OUT  = os.path.join(directories["scaled"], g )
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP2, OUT, 0.5, 0.5, 0.5) )
            os.remove(TMP1)
            os.remove(TMP2)

    #Copy the masseters and skins from mesh to merged.
    for f in os.listdir(directories["mesh"]):
        if "Mass" in f or "Skin" in f:
            copyfile(
                os.path.join(directories["mesh"], f),
                os.path.join(directories["merged"], f)
            )
    #Get the skull files in "merged"
    cases = set([f.split("-")[0] for f in os.listdir(directories["merged"])])
    FILES = [[f for f in os.listdir(directories["merged"]) if f.startswith(case)] for case in cases]
    FILES.sort(key = lambda x:x[0])
    #Execute
    lib_exe.parallel(scale, FILES)
    """

    # 6 - Remesh all the files
    """
    def remesh(f):
        IN    = os.path.join(directories["scaled"], f)
        HAUSD = 0.0025
        OUT   = os.path.join(directories["remeshed"], f)
        lib_exe.execute(lib_exe.mmgs + "%s -nr -nreg -hausd %f -out %s > /dev/null 2>&1" % (IN, HAUSD, OUT))
    FILES = [f for f in os.listdir(directories["scaled"]) if ".mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories["remeshed"])]
    lib_exe.parallel(remesh, FILES)
    """


    # 7 - Align the models
    """
    def align(group):
        SOURCE = os.path.join(directories["remeshed"], [g for g in group if "Skull" in g][0])
        TARGET = os.path.join(directories["remeshed"], "PREVI-Skull.mesh")#templates["bone"]
        FILE   = os.path.join(directories["aligned"], group[0].split("-")[0] + "_icp_matrix.txt")
        lib_exe.execute( lib_exe.python_cmd("icp.py") + "-s %s -t %s -m %s" % (SOURCE, TARGET, FILE))
        for g in group:
            IN  = os.path.join(directories["remeshed"], g)
            OUT = os.path.join(directories["aligned"], g)
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -m %s" % (IN, OUT, FILE))
            #S'assurer qu'on n'overwrite pas le fichier de la matrice
            #python3 transform.py -i merged/mandibule.mesh -o aligned/mandibule.mesh -m merged/icp_matrix.txt
    cases = set([f.split("-")[0] for f in os.listdir(directories["remeshed"])])
    GROUPS = [[f for f in os.listdir(directories["remeshed"]) if f.startswith(case) and f.endswith(".mesh")] for case in cases]
    lib_exe.parallel(align, GROUPS)
    """

    # 8 - OPTIONAL: generate a shell for warping from all the skulls we have
    # TOTALLY OPTIONNAL FOR NOW
    """
    mesh = lib_msh.Mesh()
    for f in os.listdir(directories["merged"]):
        mesh.fondre(lib_msh.Mesh(os.path.join(directories["merged"], f)))
    mesh.write("merged.mesh")
    lib_exe.execute( lib_exe.python_cmd("shell.py") + "-i %s -o %s" % ("merged.mesh", "shell.mesh"))
    os.remove("merged.mesh")
    """


    """
    # 9 - Warp the bones
    def warp(f):
        IN  = os.path.join(directories["aligned"], f)
        OUT = os.path.join(directories["warped"], f)
        TEMPLATE = templates["sphere"]
        lib_exe.execute( lib_exe.python_cmd("warp.py") + "-i %s -o %s -t %s" % (IN, OUT, TEMPLATE))
    FILES = [f for f in os.listdir(directories["aligned"]) if "bone" in f and ".mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories["warped"])]
    lib_exe.parallel(warp, FILES)

    # 8 - Compute the signed distances on the warped bones...
    def signed(f):
        IN  = os.path.join(directories["warped"], f)
        OUT = os.path.join(directories["signed"], f)
        BOX = templates["box"]
        lib_exe.execute( lib_exe.python_cmd("signed.py") + "-i %s -o %s -v %s" % (IN, OUT, BOX))
    FILES = [f for f in os.listdir(directories["warped"]) if "bone" in f and f.endswith(".mesh")]
    FILES = [f for f in FILES if f not in os.listdir(directories["signed"])]
    lib_exe.parallel(signed, FILES)

    # 9 - ... and on the faces
    def signed(f):
        IN  = os.path.join(directories["aligned"], f)
        OUT = os.path.join(directories["signed"], f)
        BOX = templates["box"]
        lib_exe.execute( lib_exe.python_cmd("signed.py") + "-i %s -o %s -v %s" % (IN, OUT, BOX))
    FILES = [f for f in os.listdir(directories["aligned"]) if "face" in f and f.endswith(".mesh")]
    FILES = [f for f in FILES if f not in os.listdir(directories["signed"])]
    lib_exe.parallel(signed, FILES)

    #10 - Fill the wrapped surfaces with tetrahedra and an icosphere
    def fill(f):
        IN  = os.path.join(directories["warped"], f)
        OUT = os.path.join(directories["filled"], f)
        BOX = templates["box"]
        lib_exe.execute( lib_exe.python_cmd("fill.py") + "-i %s -o %s -c 0.5 0.5 0.7 -r 0.05" % (IN, OUT))
    FILES = [f for f in os.listdir(directories["warped"]) if f not in os.listdir(directories["filled"])]
    lib_exe.parallel(fill, FILES)

    # 11 - Morph the appropriate templates to the skull (and the faces = used for later, to have the same mesh for all faces)
    def morph(f):
        IN  = os.path.join(directories["filled"], f)
        OUT = os.path.join(directories["morphed"], f)
        TMP = templates["morphingSkull"] if "bone" in f else templates["morphing"]
        lib_exe.execute( lib_exe.python_cmd("morph.py") + "-t %s -s %s -o %s" % (TMP, IN, OUT))
    FILES = [f for f in os.listdir(directories["filled"]) if "bone" in f or "face" in f and f.endswith("mesh") ]
    FILES = [f for f in FILES if f not in os.listdir(directories["morphed"])]
    lib_exe.parallel(morph, FILES)

    # 12 - Generate "La Masqué"
    def mask(num):
        INTERIOR  = os.path.join(directories["morphed"], num + "_bone.mesh")
        EXTERIOR  = os.path.join(directories["morphed"], num + "_face.mesh")
        MASK      = os.path.join(directories["masked"], num + "_mask.mesh")
        lib_exe.parallel(mask, GROUPS)
    NUMS = set([f.split("-")[0] for f in os.listdir(directories["morphed"]) if f.endswith("mesh")])
    NUMS = [n for n in NUMS if os.path.exists(os.path.join(directories["morphed"], n+"_face.mesh")) and os.path.exists(os.path.join(directories["morphed"], n+"_bone.mesh"))]
    NUMS = [n for n in NUMS if not os.path.exists(os.path.join(directories["masked"], n+"_mask.mesh"))]
    lib_exe.parallel(mask, NUMS)

    ################################################################################
    # 2 - Prepare the mandibles and masseters (cut them in half and position)
    ################################################################################

    # 1 - Cut the raw mandibles and masseters in half
    def split(f):
        #Scale to one unit and center
        IN    = os.path.join(directories["mesh"], f)
        TMP   = os.path.join(directories["splitted"], f.replace(".mesh", ".tmp.mesh"))
        lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -c" % (IN, TMP))
        #Split in half
        TMP_R = os.path.join(directories["splitted"], f.replace(".mesh", ".tmp.R.mesh"))
        TMP_L = os.path.join(directories["splitted"], f.replace(".mesh", ".tmp.L.mesh"))
        lib_exe.execute(lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_R, 1))
        lib_exe.execute(lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_L, -1))
        #Move the halves to .5 .5 .5
        OUT_R = os.path.join(directories["splitted"], f.replace(".mesh", ".R.raw.mesh"))
        OUT_L = os.path.join(directories["splitted"], f.replace(".mesh", ".L.raw.mesh"))
        lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_R, OUT_R, .75, .5, .5))
        lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_L, OUT_L, .75, .5, .5))
        #Remove the temporary files
        os.remove(TMP)
        os.remove(TMP_L)
        os.remove(TMP_R)
    FILES = [f for f in os.listdir(directories["mesh"]) if "mand" in f or "mass" in f]
    FILES = [f for f in FILES if f.replace(".mesh", ".R.raw.mesh") not in os.listdir(directories["splitted"])]
    lib_exe.parallel(split, FILES)

    # 2 - Remesh everything
    def remesh(f):
        IN    = os.path.join(directories["splitted"], f)
        HAUSD = 0.0025
        OUT   = os.path.join(directories["splitted"], f.replace(".raw.mesh", ".remeshed.mesh"))
        lib_exe.execute( lib_exe.mmgs + "%s -nr -nreg -hausd %f -o %s > /dev/null 2>&1" % (IN, HAUSD, OUT))
    FILES = [f for f in os.listdir(directories["splitted"]) if ".raw.mesh" in f and f.replace(".raw.mesh", ".remeshed.mesh") not in os.listdir(directories["splitted"])]
    lib_exe.parallel(remesh, FILES)

    # 3 - Align the mandibles and the masseters
    def align(f):
        SOURCE = os.path.join(directories["splitted"], f)
        TARGET = templates["masseter"] if "mass" in f else template["mandible"]
        MAT    = os.path.join(directories["splitted"], f[:4] + "icp_matrix.txt")
        OUT    = os.path.join(directories["splitted"], f.replace(".remeshed.mesh", ".aligned.mesh"))
        lib_exe.execute( lib_exe.python_cmd("icp.py") + "-s %s -t %s -m %s" % (SOURCE, TARGET, MAT))
        lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -m %s" % (SOURCE, OUT, MAT))
    FILES = [f for f in os.listdir(directories["splitted"]) if ".remeshed.mesh" in f and f.replace(".remeshed.mesh", ".aligned.mesh") not in os.listdir(directories["splitted"])]
    lib_exe.parallel(align, FILES)

    #OPTIONAL: generate a shell forthe mandibles and a shell for the masseters
    #Mandibles
    mesh = lib_msh.Mesh()
    FILES = [f for f in os.listdir(directories["splitted"]) if "mand.aligned.mesh" in f]
    for f in FILES:
        mesh.fondre(lib_msh.Mesh(os.path.join(directories["splitted"], f)))
    mesh.write("merged.mesh")
    lib_exe.execute( lib_exe.python_cmd("shell.py") + "-i %s -o %s" % ("merged.mesh", "shell_mandible.mesh"))
    os.remove("merged.mesh")
    #Masseters
    mesh = lib_msh.Mesh()
    FILES = [f for f in os.listdir(directories["splitted"]) if "mass.aligned.mesh" in f]
    for f in FILES:
        mesh.fondre(lib_msh.Mesh(os.path.join(directories["splitted"], f)))
    mesh.write("merged.mesh")
    lib_exe.execute( lib_exe.python_cmd("shell.py") + "-i %s -o %s" % ("merged.mesh", "shell_masseter.mesh"))
    os.remove("merged.mesh")

    # 7 - Warp the mandibles
    def warp(f):
        IN  = os.path.join(directories["splitted"], f)
        OUT = os.path.join(directories["splitted"], f.replace(".aligned.mesh", ".warped.mesh"))
        TEMPLATE = templates["sphere"] if "mass" in f else templates["sphere"]
        lib_exe.execute( lib_exe.python_cmd("warp.py") + "-i %s -o %s -t %s" % (IN, OUT, TEMPLATE))
    FILES = [f for f in os.listdir(directories["splitted"]) if ".aligned.mesh" in f and f.replace(".aligned.mesh", ".warped.mesh") not in os.listdir(directories["splitted"])]
    lib_exe.parallel(warp, FILES)

    """
