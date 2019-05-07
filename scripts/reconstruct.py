#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
python3 reconstruct.py -t /home/loic/TEMPLATES -m /home/loic/FACILE/morphed -i skull.mesh
"""

"""
Pour reconstruire un nouveau crane, on lui fait subir des opérations similaires aux crânes de la base de données.
Sous-citées:
01. OK - Conversion si le fichier est dans un autre format
02. OK - Merge les teeth, mands... si nécessaire (et optionnellement, le masseter)
03. OK - Mise à l'échelle par rapport au template skull: doit se faire manuellement?
04. OK - Remaillage avec la meme distance d'haussdorf que les autres
05. OK - ICP alignement
06. OK - Warp sphere.mesh vers le crane
07. OK - Calcul de la distance signée de la surface ainsi warpée
08. OK - Morphing de morphing_skull.mesh vers la distance signée sus-citée
8. OK - Choix d'un masque ou d'une moyenne de masques qui sont les plus proches
9. OK - Déplacement du masque vers la surface.
"""

import lib_exe
import lib_msh
import os
import argparse
from shutil import copyfile
import sys
import numpy as np
import tempfile
import shutil

from lib_paths import *


def init():
    #Argument parsing
    parser = argparse.ArgumentParser(description="Reconstruction of one skull")
    parser.add_argument("-t", "--templates", type=str, help="directory for the templates", required=True)
    parser.add_argument("-m", "--morphed", type=str, help="directory where the morphed results have been created", required=True)
    #parser.add_argument("-i", "--input",     type=str, help=".mesh file(s) to be reconstructed", nargs="+", required=True)
    parser.add_argument("-i", "--input",     type=str, help=".mesh file(s) to be reconstructed", required=True)
    args = parser.parse_args()
    args.templates = os.path.abspath(args.templates)
    args.morphed = os.path.abspath(args.morphed)
    args.input = os.path.abspath(args.input)


    #args.input = [os.path.abspath(n) for n in args.input]
    #print(args.input)

    #Template files
    templateNames = ["masseter", "mandible", "skull", "sphere", "morphing_face", "morphing_skull", "box"]
    templates     = {}
    for d in templateNames:
        templates[d] = os.path.abspath(os.path.join(args.templates, d + ".mesh"))

    return args, templates

if __name__ == "__main__":

    #Get the templates and arguments
    args, templates = init()
    NAME = "reconstruction"
    ipt = args.input.split("/")[-1]
    print(ipt)

    """
    # 1 - If needed, convert the .obj or .stl objects to .mesh
    for i,f in enumerate(args.input):
        if f.endswith(".obj") or f.endswith(".stl"):
            lib_exe.execute( lib_exe.python_cmd("convert.py") + "-i %s -o %s" % (f, f.replace(f[-3:], "mesh")))
            args.input[i] = f.replace(f[-3:], "mesh")

    # 2 - If needed, merge everything together
    if len(args.input)>1:
        lib_exe.execute( lib_exe.python_cmd("merge.py") + "-i %s -o %s" % (" ".join(args.input), NAME + ".mesh"))
    else:
        shutil.copyfile(args.input[0], NAME + ".mesh")

    # 3 - Transform to an object between 0.1 and 0.9
    mesh = lib_msh.Mesh(NAME + ".mesh")
    S = 0.8 / np.max(mesh.dims)
    C = mesh.center
    lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % (NAME + ".mesh", "tmp.mesh", -C[0], -C[1], -C[2]) )
    lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -s %f %f %f" % ("tmp.mesh", "tmp.mesh", S, S, S))
    lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -t %f %f %f" % ("tmp.mesh", NAME + ".scaled.mesh", 0.5, 0.5, 0.5) )
    os.remove("tmp.mesh")

    # 4 - Remesh
    HAUSD = 0.0025
    lib_exe.execute(lib_exe.mmgs + "%s -nr -nreg -hausd %f -out %s > /dev/null 2>&1" % (NAME + ".scaled.mesh", HAUSD, NAME + ".remeshed.mesh"))

    # 5 - Align
    lib_exe.execute( lib_exe.python_cmd("icp.py") + "-s %s -t %s -m %s" % (NAME + ".remeshed.mesh", templates["skull"], NAME + ".matrix.txt"))
    lib_exe.execute( lib_exe.python_cmd("transform.py") + "-i %s -o %s -m %s" % (NAME + ".remeshed.mesh", NAME + ".aligned.mesh", NAME + ".matrix.txt"))


    # 6 - Warp
    lib_exe.execute( lib_exe.python_cmd("warp.py")
        + "-i %s -o %s -t %s"
        % (NAME + ".aligned.mesh", NAME + ".warped.mesh", templates["sphere"])
    )


    # 7 - Signed distance
    lib_exe.execute( lib_exe.python_cmd("signed.py")
        + "-i %s -o %s -v %s -p"
        % (NAME + ".warped.mesh", NAME + ".signed.mesh", templates["box"])
    )


    # 8 - Morph the template to this warped skull
    lib_exe.execute( lib_exe.python_cmd("morph.py")
        + "-t %s -s %s -o %s --icotris %d --icotets %d --fixtris %d -n %d"
        % (templates["morphing_skull"], NAME + ".signed.mesh", NAME + ".morphed.mesh", 10, 2, 0, 1500)
    )
    """
    # 9 - Find the closest of all the skulls that was warped before
    def scalar(d1,d2):
        return np.sum(np.multiply(d1,d2)) / (np.linalg.norm(d1)*np.linalg.norm(d2))
    def cov(d):
        return np.array([[scalar(x,y) for x in d] for y in d])

    DATA = []
    mesh = lib_msh.Mesh(args.input)
    DATA.append(mesh.verts[:,:3])
    FILES = [f for f in os.listdir(args.morphed)]
    print(FILES)
    for f in FILES:
        if f!= ipt:
            mesh = lib_msh.Mesh(os.path.join(args.morphed, f))
            DATA.append(mesh.verts[:,:3])
    DATA = np.array(DATA)

    A = cov(DATA)
    print("/n Matrice A VarCoVar /n",A)

    B= []
    for i in range(len(A[0])):
        if A[i,0] < 0.99999999 and A[i,0] not in B:
            B.append(A[i,0])
    max = np.amax(B)
    res = np.where(A == max)
    print("/n Valeur max de B /n", max)
    print("/n Localisation de la valeur max de A /n", res)
    liste = list(zip(res[0], res[1]))
    print(liste[0][1])
    case = []
    num = []
    case.append(FILES[liste[0][1]].split("-")[0])
    num.append(liste[0][1])
    B= []
    for i in range(len(A[0])):
        if A[i,liste[0][1]] < 0.99999999 and A[i,liste[0][1]] not in B:
            B.append(A[i,liste[0][1]])
    min1 = np.amin(B)
    res = np.where(A == min1)
    print("/n Valeur min de B /n", min1)
    print("/n Localisation de la valeur min de B/n", res)
    liste1 = list(zip(res[0], res[1]))
    print(liste1[0][1])
    case.append(FILES[liste1[0][1]].split("-")[0])
    num.append(liste1[0][1])
    B= []
    for i in range(len(A[0])):
        if A[i,liste[0][1]] < 0.99999999 and A[i,liste1[0][1]] < 0.99999999:
            B.append((A[i,liste[0][1]] + A[i,liste1[0][1]])/2)
        else:
            B.append(1.0)
    min2 = np.amin(B)
    res = np.where(B == min2)

    print("/n Valeur min de B /n", min2)
    print("/n Localisation de la valeur min de B/n", res)
    liste2 = list(zip(res[0]))
    print(liste2[0][0])
    case.append(FILES[liste2[0][0]].split("-")[0])
    num.append(liste2[0][0])
    print(case)
    print(num)


    alpha = np.array([scalar(DATA[0],y) for y in DATA[num]])
    print(alpha)

    sys.exit()



    """
    def distance(a,b):
        return ( (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2 ) **0.5
    mesh = lib_msh.Mesh(NAME + ".morphed.mesh")
    MORPHED = [f for f in os.listdir(args.morphed) if "Skull.mesh" in f]
    MORPHED.sort()
    MEANS = []
    for i,f in enumerate(MORPHED):
        morphed = lib_msh.Mesh(os.path.join(args.morphed, f))
        if len(morphed.verts)>=len(mesh.verts):
            morphed.tris = morphed.tris[morphed.tris[:,-1]!=10]
            morphed.tets = np.array([])
            morphed.discardUnused()
            mean = np.mean([distance(v1,v2) for v1,v2 in zip(morphed.verts, mesh.verts)])
            print(i,mean, f)
            MEANS.append([i, mean, f])
    case = MORPHED[MEANS[np.argmin([mean[1] for mean in MEANS])][0]].split("-")[0]
    print(case)
    """


    #JUSTE CAR JE N4AI PAS TOUS LES MASQUES J4EN CHOISI UN AUTRE ASSEZ "PROCHE"
    #case = "ADASA"

    #Create the elasticity file
    with open(NAME + "_la_masque.elas", "w") as f:
        f.write("Dirichlet\n1\n1 vertex f\n\n")
        f.write("Lame\n1\n2 186000. 3400.\n\n")

    # 11 - Run the elasticity with the given input = last step
    lib_exe.execute( lib_exe.elasticity
        + "%s -s %s -p %s -o %s -n %d +v -r %.20f"
        % (os.path.join("/home/lydieuro/Bureau/FaciLe-DataRecons/DATA-base/masked", case + "_la_masque.mesh"), os.path.join("/home/lydieuro/Bureau/FaciLe-DataRecons/DATA-base/masked", case + "_la_masque.sol"), NAME + "_la_masque.elas", NAME + ".elasticity.sol", 2000, 0.00000001)
    )
    shutil.copyfile(os.path.join("/home/lydieuro/Bureau/FaciLe-DataRecons/DATA-base/masked", case + "_la_masque.mesh"), NAME + ".elasticity.mesh")

    #Adjust the final reconstruction
    mesh = lib_msh.Mesh(NAME + ".elasticity.mesh")
    mesh.readSol()
    mesh.verts[:,:3] += mesh.vectors
    mesh.tets = np.array([])
    mesh.tris = mesh.tris[mesh.tris[:,-1]==2]
    mesh.discardUnused()
    mesh.write(NAME + ".final.mesh")
