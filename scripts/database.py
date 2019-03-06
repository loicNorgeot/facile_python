#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
import tempfile

from lib_paths import *

MERGEREALMASS = False
MERGEPCAMASS = True

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
    """
    Looks in the directory associated with the templates, for a skull.mesh file for instance.
    If skull.mesh is found, then a variable templates["skull"] becomes available.
    """
    templateNames = ["masseter", "mandible", "skull", "sphere", "morphing_face", "morphing_skull", "box"]
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
        "mergedRealMass",
        "mergedPCAMass",
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
    """
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
    """

	### Etape d'ajout du masseter à la reconstruction ###
	# Il me faut faire la reconstruction sur les merge 1- juste Crane 2- Crane et vrai mass 3- Crane et mass reconstruit
    if MERGEPCAMASS == True:
        print('plouf')

        # 1 - Cut the raw mandibles and masseters in half
        def split(group):
            for g in group:
                mass = [g for g in group if "Mass" in g][0]
                print(mass)
                # Translate everything so that the center of the skull is on 0,0,0
                centerMass = lib_msh.Mesh(os.path.join(directories["mesh"], mass)).center
                print(centerMass)
            #Scale to one unit and center
                IN    = os.path.join(directories["mesh"], g)
                TMP   = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.mesh"))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -c %f %f %f" % (IN, TMP, -centerMass[0], -centerMass[1], -centerMass[2]))
            #Split in half
                TMP_R = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.R.mesh"))
                TMP_L = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.L.mesh"))
                lib_exe.execute(lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_R, 1))
                lib_exe.execute(lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_L, -1))
            #Move the halves to .5 .5 .5
                OUT_R = os.path.join(directories["splitted"], g.replace(".mesh", ".R.raw.mesh"))
                OUT_L = os.path.join(directories["splitted"], g.replace(".mesh", ".L.raw.mesh"))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_R, OUT_R, .75, .5, .5))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_L, OUT_L, .75, .5, .5))
            #Remove the temporary files
                os.remove(TMP)
                os.remove(TMP_L)
                os.remove(TMP_R)
        cases = set([f.split("-")[0] for f in os.listdir(directories["mesh"]) if "Mass" in f])
        print(cases)
        FILES = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case) and "Mass" in f]for case in cases]
        #FILES = [f for f in FILES if f.replace(".mesh", ".R.raw.mesh") not in os.listdir(directories["splitted"])]
        FILES.sort(key = lambda x:x[0])
        print(FILES)
        lib_exe.parallel(split, FILES, 1)


    """
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
    """


    # 4 - Merge the bones (skull, mandibles and teeth) together
    """
    def merge(group):
        OUT   = os.path.join(directories["merged"], group[0][:6] + "Skull.mesh")
        lib_exe.execute( lib_exe.python_cmd("merge.py") + "-i %s -o %s" % (" ".join([os.path.join(directories["mesh"], g) for g in group]), OUT))
    cases = set([f.split("-")[0] for f in os.listdir(directories["mesh"]) if ".mesh" in f and f[0]!="."])
    GROUPS = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case) and f.endswith(".mesh") and "Mass" not in f and "Skin" not in f] for case in cases] #"and "Mass" not in f" enleve le masseter du merge, si j'enlève cette partie il ajoute le masséter mais attention çà va tout refaire en erasant tout ce qui est fait.
    print(GROUPS)
    GROUPS = [f for f in GROUPS if f not in os.listdir(directories["merged"])]
    print(GROUPS)
    lib_exe.parallel(merge, GROUPS)
    """

    # 5 - Scale everything

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
    #for f in os.listdir(directories["mesh"]):
        #if "Mass" in f or "Skin" in f:
            #copyfile(
                #os.path.join(directories["mesh"], f),
                #os.path.join(directories["merged"], f)
            #)
    #Get the skull files in "merged"
    cases = set([f.split("-")[0] for f in os.listdir(directories["merged"])])
    FILES = [[f for f in os.listdir(directories["merged"]) if f.startswith(case)] for case in cases]
    FILES.sort(key = lambda x:x[0])
    print(FILES)
    #Execute
    lib_exe.parallel(scale, FILES)

    """
    # 6 - Remesh all the files
    def remesh(f):
        IN    = os.path.join(directories["scaled"], f)
        HAUSD = 0.0025
        OUT   = os.path.join(directories["remeshed"], f)
        lib_exe.execute(lib_exe.mmgs + "%s -nr -nreg -hausd %f -out %s -hmin 0.008 > /dev/null 2>&1" % (IN, HAUSD, OUT))
    FILES = [f for f in os.listdir(directories["scaled"]) if ".mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories["remeshed"])]
    print(FILES)
    lib_exe.parallel(remesh, FILES, 2)



    # 7 - Align the models

    def align(group):
        SOURCE = os.path.join(directories["remeshed"], [g for g in group if "Skull" in g][0])
        TARGET = templates["skull"]
        FILE   = os.path.join(directories["aligned"], group[0].split("-")[0] + "_icp_matrix.txt")
        lib_exe.execute( lib_exe.python_cmd("icp.py") + "-s %s -t %s -m %s" % (SOURCE, TARGET, FILE))
        for g in group:
            IN  = os.path.join(directories["remeshed"], g)
            OUT = os.path.join(directories["aligned"], g)
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -m %s" % (IN, OUT, FILE))
            #S'assurer qu'on n'overwrite pas le fichier de la matrice
            #python3 transform.py -i merged/mandibule.mesh -o aligned/mandibule.mesh -m merged/icp_matrix.txt
    cases = set([f.split("-")[0] for f in os.listdir(directories["remeshed"])])
    GROUPS = [[f for f in os.listdir(directories["remeshed"]) if f.startswith(case) and f.endswith(".mesh") and f not in os.listdir(directories["aligned"])] for case in cases]
    GROUPS = [g for g in GROUPS if len(g)>0]
    for g in GROUPS:
        print(g)
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

    # 9 - Warp the bones
    """
    def warp(f):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            IN  = os.path.join(directories["aligned"], f)
            OUT = os.path.join(directories["warped"], f)
            TEMPLATE = templates["sphere"]
            lib_exe.execute( lib_exe.python_cmd("warp.py") + "-i %s -o %s -t %s" % (IN, OUT, TEMPLATE))
    FILES = [f for f in os.listdir(directories["aligned"]) if "Skull.mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories["warped"])]
    lib_exe.parallel(warp, FILES)


    # 10 - Compute the signed distances on the warped bones and skins

    def signed(f):
        IN  = os.path.join(directories["aligned"], f) if "Skin" in f else os.path.join(directories["warped"], f)
        OUT = os.path.join(directories["signed"], f)
        BOX = templates["box"]
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            lib_exe.execute( lib_exe.python_cmd("signed.py") + "-i %s -o %s -v %s -p" % (IN, OUT, BOX))
    FILES = []
    warpedSkulls = [f for f in os.listdir(directories["warped"]) if "Skull" in f and f.endswith(".mesh")]
    for skull in warpedSkulls:
        name = skull.split("-")[0]
        for face in os.listdir(directories["aligned"]):
            if face.split("-")[0] == name and "Skin.mesh" in face:
                FILES.append(skull)
                FILES.append(face)
    FILES = [f for f in FILES if f not in os.listdir(directories["signed"])]
    #FILES = [f for f in FILES if "MADAN" not in f and "LAUVI" not in f]
    for f in FILES:
        try:
            signed(f)
        except:
            print("%s failed..." % f)
    """

    #12 - Fill the wrapped surfaces with tetrahedra and an icosphere
    """
    def fill(f):
        IN  = os.path.join(directories["warped"], f)
        OUT = os.path.join(directories["filled"], f)
        lib_exe.execute( lib_exe.python_cmd("fill.py") + "-i %s -o %s -c 0.5 0.5 0.65 -r 0.1" % (IN, OUT))
    FILES = [f for f in os.listdir(directories["warped"]) if f not in os.listdir(directories["filled"]) if "GROJU" in f]
    lib_exe.parallel(fill, FILES)
    """

    # 13 - Morph the appropriate templates to the skull
    """
    def morph(f):
        IN   = os.path.join(directories["signed"], f)
        OUT  = os.path.join(directories["morphed"], f)
        TMP  = templates["morphing_skull"] if "Skull" in f else templates["morphing_face"]
        REFS = [10, 2, 0] if "Skull" in f else [10, 2, 3]
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            lib_exe.execute( lib_exe.python_cmd("morph.py") + "-t %s -s %s -o %s --icotris %d --icotets %d --fixtris %d -n %d" % (TMP, IN, OUT, REFS[0], REFS[1], REFS[2], 2000))
    FILES = [f for f in os.listdir(directories["signed"]) if ("Skull" in f or "Skin" in f) and f.endswith("mesh") ]
    FILES = [f for f in FILES if f not in os.listdir(directories["morphed"])]
    lib_exe.parallel(morph, FILES)
    """
    # 14 - Generate "La Masqué"
    """
    def mask(group):
        INTERIOR  = [ os.path.join(directories["morphed"], g) for g in group if "Skull" in g][0]
        EXTERIOR  = [ os.path.join(directories["morphed"], g) for g in group if "Skin" in g][0]
        MASK      = os.path.join(directories["masked"], group[0].split("-")[0] + "_la_masque.mesh")
        TEMPLATE  = templates["morphing_skull"]
        lib_exe.execute( lib_exe.python_cmd("mask.py") + "-i %s -e %s -o %s -t %s" % (INTERIOR, EXTERIOR, MASK, TEMPLATE))

    cases = set([f.split("-")[0] for f in os.listdir(directories["morphed"]) if ".mesh" in f])
    GROUPS = [ [f for f in os.listdir(directories["morphed"]) if ("Skull" in f or "Skin" in f) and case in f] for case in cases]
    print(GROUPS)
    GROUPS = [g for g in GROUPS if len(g)==2]
    GROUPS = [g for g in GROUPS if g not in os.listdir(directories["masked"])]
    #print(GROUPS)
    lib_exe.parallel(mask, GROUPS, 1) #ne fonctionne pas sur plus d'un processeur à la fois ... ?
    """





    """
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
