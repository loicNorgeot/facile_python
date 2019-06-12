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
    parser.add_argument("-d", "--data", type=str, help="directory where the morphed and la_masque results have been created", required=True)
    #parser.add_argument("-i", "--input",     type=str, help=".mesh file(s) to be reconstructed", nargs="+", required=True)
    parser.add_argument("-i", "--input",     type=str, help=".mesh file(s) to be reconstructed", required=True)
    args = parser.parse_args()
    args.templates = os.path.abspath(args.templates)
    args.data = os.path.abspath(args.data)
    args.input = os.path.abspath(args.input)


    #args.input = [os.path.abspath(n) for n in args.input]
    #print(args.data)


    #Template files
    templateNames = ["ellipsoide", "morphing_mass", "skull", "sphere", "morphing_face", "morphing_skullOnly", "morphing_skullRM", "morphing_skullPCA", "box"]
    templates     = {}
    for d in templateNames:
        templates[d] = os.path.abspath(os.path.join(args.templates, d + ".mesh"))

    #Create the directories to process files into
    dirNames = ["PcaMass","RealMass","SkullOnly", "reconstructed"]
    directories    = {}
    for d in dirNames:
        #print(d)
        directories[d] = os.path.abspath(os.path.join(args.data, d))
        if not os.path.exists(directories[d]):
            os.makedirs(directories[d])

    return args, templates, directories

if __name__ == "__main__":

    #Get the templates and arguments
    args, templates, directories = init()

    ipt = args.input.split("/")[-1]
    #print(ipt)
    NAME = ipt.split("-")[0]
    print(NAME)

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

    REALMASS = False
    PCAMASS = False
    SKULLONLY = True

    if SKULLONLY == True:
        dossier = "SkullOnly"
    if REALMASS == True:
        dossier = "RealMass"
    if PCAMASS == True:
        dossier = "PcaMass"

    # Chargement des meshs des cranes morphés de la base de données
    # en position 0 le mesh du crâne inconnu (attention si pas un crâne de la base il faut faire les étapes précédente et sélectionné le morphé)
    DATA = []
    meshIpt = lib_msh.Mesh(args.input)
    DATA.append(meshIpt.verts[:,:3])
    FILES = [f for f in os.listdir(directories[dossier]) if "Skull-morphed.mesh" in f]
    #print(FILES)
    nameFILES = []
    # count = 1
    for f in FILES:
        if f!= ipt:
            mesh = lib_msh.Mesh(os.path.join(directories[dossier], f))
            # print(f, count)
            # print(mesh.verts.shape)
            DATA.append(mesh.verts[:,:3])
            nameFILES.append(f.split("-")[0])
            # count += 1
    DATA = np.array(DATA)
    # Matrice de variance-covariance : calcul des produits scalaires qui me permet de déterminer les 3 plus proches (valeur la plus élevée)
    A = cov(DATA)
    #print("/n Matrice A VarCoVar /n",A)
    B= []
    for i in range(len(A[0])):
        if A[i,0] < 0.9999 and A[i,0] not in B:
            B.append(A[i,0])
    #max = np.amax(B)
    Bbis = sorted(B, reverse=True)
    res = []
    liste = []
    cases = []
    num = []
    N = 3
    for i in range(N):
        res.append(np.where(A == Bbis[i]))
        liste.append(list(zip(res[i][0], res[i][1])))
        num.append(liste[i][0][1]-1)
        cases.append(nameFILES[num[i]])
    #print(cases)


    #JUSTE CAR JE N4AI PAS TOUS LES MASQUES J4EN CHOISI UN AUTRE ASSEZ "PROCHE"
    #case = "BELNA"

    #Create the elasticity file : attention seulement une fois
    """
    with open(os.path.join(directories["reconstructed"], "parameters.elas"), "w") as f:
        f.write("Dirichlet\n1\n1 vertex f\n\n")
        f.write("Lame\n1\n2 186000. 3400.\n\n")
    """

    #Réalisation de 3 reconstructions à partir des masque sélectionné ci dessus comme les plus proches
    count = 0
    for case in cases:
    # Création des .sol sur les 3 masques sélectionnés comme les plus proches dans la bases de données
        maskCase = lib_msh.Mesh(os.path.join(directories[dossier], case + "-la_masque.mesh"))
        unknownMorphed = lib_msh.Mesh(args.input)
        unknownMorphed.tets = np.array([])
        unknownMorphed.discardUnused()
        n = len(maskCase.verts)
        maskCase.vectors = np.zeros((n,3))
        maskCase.vectors[:len(unknownMorphed.verts)] = unknownMorphed.verts[:,:3] - maskCase.verts[:len(unknownMorphed.verts),:3]
        maskCase.writeSol( os.path.join(directories[dossier], case + "to" + NAME + "-la_masque.sol") )
        #mesh.write( args.output )

    # Run the elasticity with the given input = last step
        IN = os.path.join(directories[dossier], case + "-la_masque.mesh")
        SOL = os.path.join(directories[dossier], case + "to" + NAME + "-la_masque.sol")
        OUT = os.path.join(directories["reconstructed"], NAME  + "-" + str(count) + "-" + dossier + "-elasticity.sol")
        PARAMETERS = os.path.join(directories["reconstructed"],"parameters.elas")
        lib_exe.execute( lib_exe.elasticity
            + "%s -s %s -p %s -o %s -n %d +v -r %.20f"
            % (IN, SOL, PARAMETERS, OUT, 1000, 0.00000001)
        )

        shutil.copyfile(os.path.join(directories[dossier], case + "-la_masque.mesh"), os.path.join(directories["reconstructed"], NAME + "-" + str(count) + "-" + dossier + "-elasticity.mesh"))

    # Adjust the final reconstruction
        mesh = lib_msh.Mesh(os.path.join(directories["reconstructed"], NAME + "-" + str(count) + "-" + dossier + "-elasticity.mesh"))
        mesh.readSol()
        mesh.verts[:,:3] += mesh.vectors
        mesh.tets = np.array([])
        mesh.tris = mesh.tris[mesh.tris[:,-1]==2]
        mesh.discardUnused()
        mesh.write(os.path.join(directories["reconstructed"], NAME + "-" + str(count) + "-" + dossier + "-recons.mesh"))

        os.remove(os.path.join(directories["reconstructed"], NAME + "-" + str(count) + "-" + dossier + "-elasticity.mesh"))
        os.remove(os.path.join(directories["reconstructed"], NAME + "-" + str(count) + "-" + dossier + "-elasticity.sol"))

        count += 1



    # Moyenne des reconstrcutions pour une version finale
    mesh = lib_msh.Mesh(os.path.join(directories["reconstructed"], NAME  + "-" + str(0) + "-" + dossier + "-recons.mesh"))
    RECONS = [f for f in os.listdir(directories["reconstructed"]) if NAME in f and "-recons.mesh" in f]
    #print(RECONS)
    mesh1 = lib_msh.Mesh(os.path.join(directories["reconstructed"], RECONS[0]))
    mesh2 = lib_msh.Mesh(os.path.join(directories["reconstructed"], RECONS[1]))
    mesh3 = lib_msh.Mesh(os.path.join(directories["reconstructed"], RECONS[2]))
    mesh.verts = (mesh1.verts + mesh2.verts + mesh3.verts)/3
    mesh.discardUnused()
    mesh.write(os.path.join(directories["reconstructed"], NAME + "-" + dossier + ".mesh"))

    # Suppression des maillages intermédiare
