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

REALMASS = False
PCAMASS = True
SKULLONLY = False

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
    templateNames = ["test2", "ellipsoide", "morphing_mass", "skull", "sphere", "morphing_face", "morphing_skull", "box"]
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
        "reconstruction",
        "PcaMass",
        "RealMass",
        "SkullOnly"
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

    # 4 - Choice of the type of reconstruction wanted

    ##### Reconstruction with only the skull #####
    if SKULLONLY == True:
        dossier = "SkullOnly"

        # Merge the bones (skull, mandibles and teeth) together
        def merge(group):
            OUT   = os.path.join(directories[dossier], group[0][:6] + "Skull.mesh")
            lib_exe.execute( lib_exe.python_cmd("merge.py") + "-i %s -o %s" % (" ".join([os.path.join(directories["mesh"], g) for g in group]), OUT))
        cases = set([f.split("-")[0] for f in os.listdir(directories["mesh"]) if ".mesh" in f and f[0]!="."])
        GROUPS = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case) and f.endswith(".mesh") and "Mass" not in f and "Skin" not in f] for case in cases] #"and "Mass" not in f" enleve le masseter du merge, si j'enlève cette partie il ajoute le masséter mais attention çà va tout refaire en erasant tout ce qui est fait.
        print(GROUPS)
        GROUPS = [f for f in GROUPS if f not in os.listdir(directories[dossier])]
        print(GROUPS)
        lib_exe.parallel(merge, GROUPS)

    ##### Reconstruction with the real masseter #####
    if REALMASS == True:
        dossier = "RealMass"

        # Merge the bones (skull, mandibles and teeth) together
        def merge(group):
            OUT   = os.path.join(directories[dossier], group[0][:6] + "Skull.mesh")
            lib_exe.execute( lib_exe.python_cmd("merge.py") + "-i %s -o %s" % (" ".join([os.path.join(directories["mesh"], g) for g in group]), OUT))
        cases = set([f.split("-")[0] for f in os.listdir(directories["mesh"]) if ".mesh" in f and f[0]!="."])
        GROUPS = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case) and f.endswith(".mesh") and "Skin" not in f] for case in cases] #"and "Mass" not in f" enleve le masseter du merge, si j'enlève cette partie il ajoute le masséter mais attention çà va tout refaire en erasant tout ce qui est fait.
        print(GROUPS)
        GROUPS = [f for f in GROUPS if f not in os.listdir(directories[dossier])]
        print(GROUPS)
        lib_exe.parallel(merge, GROUPS)

	##### Reconstruction with the masseter reconstruc from pca #####
    if PCAMASS == True:
        dossier = "PcaMass"

        # 1 - Cut the masseters in half
        """
        def split(group):
            for g in group:
                mass = [g for g in group if "Mass" in g][0]
                #print(mass)
                # Translate everything so that the center of the mass is on 0,0,0
                centerMass = lib_msh.Mesh(os.path.join(directories["mesh"], mass)).center
                #print(centerMass)
            # Scale to one unit and center
                IN    = os.path.join(directories["mesh"], g)
                TMP   = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.mesh"))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (IN, TMP, -centerMass[0], -centerMass[1], -centerMass[2]))
            # Split in half
                TMP_R = os.path.join(directories["splitted"], g.replace(".mesh", ".R.tmp.mesh"))
                TMP_L = os.path.join(directories["splitted"], g.replace(".mesh", ".L.tmp.mesh"))
                print(TMP_R)
                lib_exe.execute(lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_R, 1))
                lib_exe.execute(lib_exe.blender_cmd("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_L, -1))
            # Center tmpL et tmpR en zéro pour pouvoir faire le scalling et le move en 0.5 0.5 0.5
                centerR = lib_msh.Mesh(os.path.join(directories["mesh"],TMP_R)).center
                centerL = lib_msh.Mesh(os.path.join(directories["mesh"],TMP_L)).center
                TMP_R2 = os.path.join(directories["splitted"], g.replace(".mesh", ".R.tmp2.mesh"))
                TMP_L2 = os.path.join(directories["splitted"], g.replace(".mesh", ".L.tmp2.mesh"))
                print(centerR)
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_R, TMP_R2, -centerR[0], -centerR[1], -centerR[2]))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_L, TMP_L2, -centerL[0], -centerL[1], -centerL[2]))
            # Scale by 0.008
                TMP_R3 = os.path.join(directories["splitted"], g.replace(".mesh", ".R.tmp3.mesh"))
                TMP_L3 = os.path.join(directories["splitted"], g.replace(".mesh", ".L.tmp3.mesh"))
                S = 0.008
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -s %f %f %f" % (TMP_R2, TMP_R3, S, S, S) )
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -s %f %f %f" % (TMP_L2, TMP_L3, S, S, S) )
            # Move the halves to .5 .5 .5
                OUT_R = os.path.join(directories["splitted"], g.replace(".mesh", ".R.raw.mesh"))
                OUT_L = os.path.join(directories["splitted"], g.replace(".mesh", ".L.raw.mesh"))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_R3, OUT_R, .5, .5, .5))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_L3, OUT_L, .5, .5, .5))
            # Save center.txt
                tmp_fileR = os.path.join(directories["splitted"], g.replace(".mesh", ".R.center.txt"))
                tmp_fileL = os.path.join(directories["splitted"], g.replace(".mesh", ".L.center.txt"))
                with open(tmp_fileR, "w") as q:
                    q.write("%f %f %f" % (centerMass[0], centerMass[1], centerMass[2]))
                    q.write("\n")
                    q.write("%f %f %f" % (centerR[0], centerR[1], centerR[2]))
                    q.write("\n")
                    q.write("%f" % (1))
                q.close()
                with open(tmp_fileL, "w") as k:
                    k.write("%f %f %f" % (centerMass[0], centerMass[1], centerMass[2]))
                    k.write("\n")
                    k.write("%f %f %f" % (centerL[0], centerL[1], centerL[2]))
                    k.write("\n")
                    k.write("%f" % (-1))
                k.close()
            #Remove the temporary files
                os.remove(TMP)
                os.remove(TMP_L)
                os.remove(TMP_R)
                os.remove(TMP_L2)
                os.remove(TMP_R2)
                os.remove(TMP_L3)
                os.remove(TMP_R3)

        cases = set([f.split("-")[0] for f in os.listdir(directories["mesh"]) if "Mass.mesh" in f])
        # attention si j'ai déja fait tourné le programme et qu'il y a des mass reconstruct dans "mesh" çà va merder !!!
        #print(cases)
        FILES = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case) and "Mass" in f]for case in cases]
        #FILES = [f for f in FILES if f.replace(".mesh", ".R.raw.mesh") not in os.listdir(directories["splitted"])]
        FILES.sort(key = lambda x:x[0])
        print(FILES)
        lib_exe.parallel(split, FILES)
        """
        # 2 - Remesh everything
        """
        def remesh(f):
            IN    = os.path.join(directories["splitted"], f)
            HAUSD = 0.0025
            HMIN = 0.001
            OUT   = os.path.join(directories["splitted"], f.replace(".raw.mesh", ".remeshed.mesh"))
            lib_exe.execute( lib_exe.mmgs + "%s -nr -nreg -hausd %f -hmin %f -out %s > /dev/null 2>&1" % (IN, HAUSD, HMIN, OUT))
        FILES = [f for f in os.listdir(directories["splitted"]) if ".raw.mesh" in f and f.replace(".raw.mesh", ".remeshed.mesh") not in os.listdir(directories["splitted"])]
        print(FILES)
        lib_exe.parallel(remesh, FILES)
        """
        # 3 - Align the masseters : Je le laisse de côté pour le moment parce que çà n'apport pas vraiment de différence pour la PCA et que çà me fait une manpeurvre supplémentaire inutile à sauvegarder dans un prmier temps
        """
        def align(f):
            SOURCE = os.path.join(directories["splitted"], f)
            TARGET = templates["ellipsoide"]
            MAT    = os.path.join(directories["splitted"], f[:13] + "icp_matrix.txt")
            OUT    = os.path.join(directories["splitted"], f.replace(".remeshed.mesh", ".aligned.mesh"))
            lib_exe.execute( lib_exe.python_cmd("icp.py") + "-s %s -t %s -m %s" % (SOURCE, TARGET, MAT))
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -m %s" % (SOURCE, OUT, MAT))
        FILES = [f for f in os.listdir(directories["splitted"]) if ".remeshed.mesh" in f and f.replace(".remeshed.mesh", ".aligned.mesh") not in os.listdir(directories["splitted"])]
        lib_exe.parallel(align, FILES)
        """
        # 4 - Compute the signed distances on the masseter # REMPLACER remeshed par aligned si je veux intégrer l'alignement
        """
        def signed(f):
            IN  = os.path.join(directories["splitted"], f)
            OUT = os.path.join(directories["splitted"], f.replace(".remeshed.mesh", ".signed.mesh"))
            BOX = templates["box"]
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                lib_exe.execute( lib_exe.python_cmd("signed.py") + "-i %s -o %s -v %s -p" % (IN, OUT, BOX))
        FILES = [f for f in os.listdir(directories["splitted"]) if ".remeshed.mesh" in f and f.replace(".remeshed.mesh", ".signed.mesh") not in os.listdir(directories["splitted"])]
        lib_exe.parallel(signed, FILES)
        # for f in FILES:
        #     try:
        #         signed(f)
        #     except:
        #         print("%s failed..." % f)
        """
        # 5 - Morph the appropriate templates to the masseter
        """
        def morph(f):
            IN   = os.path.join(directories["splitted"], f)
            OUT  = os.path.join(directories["splitted"], f.replace(".signed.mesh", ".morphed.mesh"))
            TMP  = templates["morphing_mass"]
            REFS = [10, 2, 0]
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                lib_exe.execute( lib_exe.python_cmd("morph.py") + "-t %s -s %s -o %s --icotris %d --icotets %d --fixtris %d -n %d" % (TMP, IN, OUT, REFS[0], REFS[1], REFS[2], 1800))
        FILES = [f for f in os.listdir(directories["splitted"]) if ".signed.mesh" in f and f.replace(".signed.mesh", ".morphed.mesh") not in os.listdir(directories["splitted"])]
        lib_exe.parallel(morph, FILES)
        """
        # 6 - PCA des Masseters
        """
        def pca(group):
            for g in group:
                #print(g)
                #print(group)
                #newGroup = group[group!=g]
                newGroup = [f for f in group if f != g]
                TRAINING = str()
                for n in newGroup:
                    TRAINING = TRAINING + ' ' + os.path.join(directories["splitted"], n)
                #print(TRAINING)
                IN = os.path.join(directories["splitted"], g)
                OUT  = os.path.join(directories["splitted"], g.replace(".morphed.mesh", ".pca.mesh"))
                lib_exe.execute( lib_exe.python_cmd("pca.py") + "-t %s -u %s -o %s" % (TRAINING, IN, OUT))
        TEST = [f for f in os.listdir(directories["splitted"]) if ".morphed.mesh" in f and f.replace(".morphed.mesh", ".pca.mesh") not in os.listdir(directories["splitted"])]
        #print(TEST)
        if len(TEST)>0:
            print('\033[95m' + "## EXECUTING 'PCA' on " + str(len(TEST)) + " cases " + '\033[0m')
        else:
            print('\033[95m' + "## SKIPPING 'PCA', no data found." + '\033[0m')
            pass
        pca(TEST) #Trouver un moyen de le lancer en parallèle sans "éclater les données de la listes d'entrée"
        """
        # 7 - Replacer les masseters dans le bon repère (sans la version "align" avec matrice 4x4)
        """
        def replace(group):
            # 1 - inverser l'alignement serait normalement la première étape
            for g in group:
                mass = [g for g in group if "Mass" in g][0]
                #print(mass)
                # Translate everything so that the center of the mass is on 0,0,0
                centerNow = lib_msh.Mesh(os.path.join(directories["splitted"], mass)).center
                tmp_file = str(g[:13])+"center.txt"
                with open(os.path.join(directories["splitted"],tmp_file), "r") as q:
                    centerTruc = q.read()
                #print(centerMass)
            # 2 - Translate in 0 0 0
                IN    = os.path.join(directories["splitted"], g)
                TMP   = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.mesh"))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (IN, TMP, -centerNow[0], -centerNow[1], -centerNow[2]))
            # 3 - Rescale
                TMP2 = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.2.mesh"))
                S = (1/0.008)
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -s %f %f %f" % (TMP, TMP2, S, S, S) )
            # 4 - Translate into center of the first version of L/R masseter
                TMP3   = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.3.mesh"))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP2, TMP3, float(centerTruc.split()[0]), float(centerTruc.split()[1]), float(centerTruc.split()[2])))
            # 5 - Symétrisation des L
                TMP4   = os.path.join(directories["splitted"], g.replace(".mesh", ".tmp.4.mesh"))
                lib_exe.execute(lib_exe.blender_cmd("symetrie.py") + "-i %s -o %s -x %d" %  (TMP3, TMP4, float(centerTruc.split()[6])))
            # 6 - Translate into center of the segmented masseter
                OUT   = os.path.join(directories["splitted"], g.replace(".pca.mesh", ".reconstruct.mesh"))
                lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP4, OUT, float(centerTruc.split()[3]), float(centerTruc.split()[4]), float(centerTruc.split()[5])))
            # Suppression des TEMPLATES
                os.remove(TMP)
                os.remove(TMP2)
                os.remove(TMP3)
                os.remove(TMP4)
        cases = set([f.split("-")[0] for f in os.listdir(directories["splitted"]) if ".pca.mesh" in f])
        #print(cases)
        FILES = [[f for f in os.listdir(directories["splitted"]) if f.startswith(case) and ".pca.mesh" in f and f.replace(".pca.mesh", ".recons.mesh") not in os.listdir(directories["splitted"])]for case in cases]
        FILES.sort(key = lambda x:x[0])
        #print(FILES)
        lib_exe.parallel(replace, FILES)
        """
        # 8 - Merge the skull with the mass PCA reconstruct

        def merge(group):
            OUT   = os.path.join(directories[dossier], group[0][:6] + "Skull.mesh")
            lib_exe.execute( lib_exe.python_cmd("merge.py") + "-i %s -o %s" % (" ".join([os.path.join(directories["mesh"], g) for g in group]), OUT))
        # Copy the masseters reconstructed from splitted to merged.
        for f in os.listdir(directories["splitted"]):
            if ".reconstruct.mesh" in f:
                copyfile(
                    os.path.join(directories["splitted"], f),
                    os.path.join(directories["mesh"], f)
                )
        cases = set([f.split("-")[0] for f in os.listdir(directories["mesh"]) if "Mass.mesh" in f and f[0]!="."])
        #print(cases)
        GROUPS = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case) and f.endswith(".mesh") and "Mass.mesh" not in f and "Skin" not in f] for case in cases] #"and "Mass" not in f" enleve le masseter du merge, si j'enlève cette partie il ajoute le masséter mais attention çà va tout refaire en erasant tout ce qui est fait.
        #print(GROUPS)
        GROUPS = [f for f in GROUPS if f not in os.listdir(directories[dossier])]
        #print(GROUPS)
        lib_exe.parallel(merge, GROUPS)
        
    ### Back to the main script which get data ready for the reconstruction
    # 5 - Scale everything
    """
    def scale(group):
        #Start here
        skull = [g for g in group if "Skull" in g][0]
        #la c'est le premier de la liste mais ca serait plus logique de le faire sur centre de chaque crane indépendament OU sur le centre du crane template éventuellement ...
        # 1 - Translate everything so that the center of the skull is on 0,0,0
        centerskull = lib_msh.Mesh(os.path.join(directories[dossier], skull)).center
        for g in group:
            IN    = os.path.join(directories[dossier], g)
            TMP1  = os.path.join(directories[dossier], "tmp1_%s" % g )
            # Translate everything so that the center of the skull is on 0,0,0
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (IN, TMP1, -centerskull[0], -centerskull[1], -centerskull[2]) )
            # Scale by 0.0035
            S = 0.0035
            TMP2  = os.path.join(directories[dossier], "tmp2_%s" % g )
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -s %f %f %f" % (TMP1, TMP2, S, S, S) )
            # Translate to 0.5 0.5 0.5
            OUT  = os.path.join(directories[dossier], g )
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP2, OUT, 0.5, 0.5, 0.5) )
            os.remove(TMP1)
            os.remove(TMP2)

    # Copy the masseters and skins from mesh to merged.
    for f in os.listdir(directories["mesh"]):
        if "Mass" in f or "Skin" in f:
            copyfile(
                os.path.join(directories["mesh"], f),
                os.path.join(directories[dossier], f)
            )
    #Get the skull files in "merged"
    cases = set([f.split("-")[0] for f in os.listdir(directories[dossier])])
    FILES = [[f for f in os.listdir(directories[dossier]) if f.startswith(case)] for case in cases]
    FILES.sort(key = lambda x:x[0])
    print(FILES)
    #Execute
    lib_exe.parallel(scale, FILES)
    """

    # 6 - Remesh all the files
    """
    def remesh(f):
        IN    = os.path.join(directories[dossier], f)
        HAUSD = 0.0025
        OUT   = os.path.join(directories[dossier], f)
        lib_exe.execute(lib_exe.mmgs + "%s -nr -nreg -hausd %f -out %s -hmin 0.008 > /dev/null 2>&1" % (IN, HAUSD, OUT))
    FILES = [f for f in os.listdir(directories[dossier]) if ".mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories[dossier])]
    print(FILES)
    lib_exe.parallel(remesh, FILES, 2)
    """

    # 7 - Align the models
    """
    def align(group):
        SOURCE = os.path.join(directories[dossier], [g for g in group if "Skull" in g][0])
        TARGET = templates["skull"]
        FILE   = os.path.join(directories[dossier], group[0].split("-")[0] + "_icp_matrix.txt")
        lib_exe.execute( lib_exe.python_cmd("icp.py") + "-s %s -t %s -m %s" % (SOURCE, TARGET, FILE))
        for g in group:
            IN  = os.path.join(directories[dossier], g)
            OUT = os.path.join(directories[dossier], g)
            lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -m %s" % (IN, OUT, FILE))
            #S'assurer qu'on n'overwrite pas le fichier de la matrice
            #python3 transform.py -i merged/mandibule.mesh -o aligned/mandibule.mesh -m merged/icp_matrix.txt
    cases = set([f.split("-")[0] for f in os.listdir(directories[dossier])])
    GROUPS = [[f for f in os.listdir(directories[dossier]) if f.startswith(case) and f.endswith(".mesh") and f not in os.listdir(directories["aligned"])] for case in cases]
    GROUPS = [g for g in GROUPS if len(g)>0]
    for g in GROUPS:
        print(g)
    lib_exe.parallel(align, GROUPS)
    """

    # 8 - OPTIONAL: generate a shell for warping from all the skulls we have
    # TOTALLY OPTIONNAL FOR NOW
    """
    mesh = lib_msh.Mesh()
    for f in os.listdir(directories[dossier]):
        mesh.fondre(lib_msh.Mesh(os.path.join(directories[dossier], f)))
    mesh.write("merged.mesh")
    lib_exe.execute( lib_exe.python_cmd("shell.py") + "-i %s -o %s" % ("merged.mesh", "shell.mesh"))
    os.remove("merged.mesh")
    """

    # 9 - Warp the bones
    """
    def warp(f):
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            IN  = os.path.join(directories[dossier], f)
            OUT = os.path.join(directories[dossier], f)
            TEMPLATE = templates["sphere"]
            lib_exe.execute( lib_exe.python_cmd("warp.py") + "-i %s -o %s -t %s" % (IN, OUT, TEMPLATE))
    FILES = [f for f in os.listdir(directories[dossier]) if "Skull.mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories[dossier])]
    lib_exe.parallel(warp, FILES)
    """

    # 10 - Compute the signed distances on the warped bones and skins
    """
    def signed(f):
        IN  = os.path.join(directories[dossier], f) if "Skin" in f else os.path.join(directories[dossier], f)
        OUT = os.path.join(directories[dossier], f)
        BOX = templates["box"]
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            lib_exe.execute( lib_exe.python_cmd("signed.py") + "-i %s -o %s -v %s -p" % (IN, OUT, BOX))
    FILES = []
    warpedSkulls = [f for f in os.listdir(directories[dossier]) if "Skull" in f and f.endswith(".mesh")]
    for skull in warpedSkulls:
        name = skull.split("-")[0]
        for face in os.listdir(directories[dossier]):
            if face.split("-")[0] == name and "Skin.mesh" in face:
                FILES.append(skull)
                FILES.append(face)
    FILES = [f for f in FILES if f not in os.listdir(directories[dossier])]
    #FILES = [f for f in FILES if "MADAN" not in f and "LAUVI" not in f]
    for f in FILES:
        try:
            signed(f)
        except:
            print("%s failed..." % f)
    """

    #12 - ONLY FOR THE TEMPLATE ... Fill the wrapped surfaces with tetrahedra and an icosphere
    """
    def fill(f):
        IN  = os.path.join(directories[dossier], f)
        OUT = os.path.join(directories[dossier], f)
        lib_exe.execute( lib_exe.python_cmd("fill.py") + "-i %s -o %s -c 0.5 0.5 0.5 -r 0.05" % (IN, OUT))
    FILES = [f for f in os.listdir(directories[dossier]) if "test2" in f]
    lib_exe.parallel(fill, FILES)
    """

    # 13 - Morph the appropriate templates to the skull
    """
    def morph(f):
        IN   = os.path.join(directories[dossier], f)
        OUT  = os.path.join(directories[dossier], f)
        TMP  = templates["morphing_skull"] if "Skull" in f else templates["morphing_face"]
        REFS = [10, 2, 0] if "Skull" in f else [10, 2, 3]
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            lib_exe.execute( lib_exe.python_cmd("morph.py") + "-t %s -s %s -o %s --icotris %d --icotets %d --fixtris %d -n %d" % (TMP, IN, OUT, REFS[0], REFS[1], REFS[2], 2000))
    FILES = [f for f in os.listdir(directories[dossier]) if ("Skull" in f or "Skin" in f) and f.endswith("mesh") ]
    FILES = [f for f in FILES if f not in os.listdir(directories[dossier])]
    lib_exe.parallel(morph, FILES)
    """
    # 14 - Generate "La Masqué"
    """
    def mask(group):
        INTERIOR  = [ os.path.join(directories[dossier], g) for g in group if "Skull" in g][0]
        EXTERIOR  = [ os.path.join(directories[dossier], g) for g in group if "Skin" in g][0]
        MASK      = os.path.join(directories[dossier], group[0].split("-")[0] + "_la_masque.mesh")
        TEMPLATE  = templates["morphing_skull"]
        lib_exe.execute( lib_exe.python_cmd("mask.py") + "-i %s -e %s -o %s -t %s" % (INTERIOR, EXTERIOR, MASK, TEMPLATE))

    cases = set([f.split("-")[0] for f in os.listdir(directories[dossier]) if ".mesh" in f])
    GROUPS = [ [f for f in os.listdir(directories[dossier]) if ("Skull" in f or "Skin" in f) and case in f] for case in cases]
    print(GROUPS)
    GROUPS = [g for g in GROUPS if len(g)==2]
    GROUPS = [g for g in GROUPS if g not in os.listdir(directories[dossier])]
    #print(GROUPS)
    lib_exe.parallel(mask, GROUPS, 1) #ne fonctionne pas sur plus d'un processeur à la fois ... ?
    """
