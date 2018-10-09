# FACILE

* 1 - Installation et dépendances
* 2 - Usage global et "philosophie"
* 3 - Modification et ajouts de nouveaux scripts
* 4 - Usage indépendant des scripts
* 5 - Problèmes actuels


## 1 - Installation et dépendances

Les scripts sont écrits en **python 3**, attention à en avoir une version installée. Anaconda est le plus pratique et évite d'avoir à re-télécharger des librairies, mais python3 classique peut parfaitement suffire.

#### 1.1 - librairies python

Les librairies python à installer sont:
* scipy
* numpy
* scikit-image

On peut les installer avec:
```
pip3 install scikit-image numpy scipy
ou
conda3 install scikit-image numpy scipy
```

#### 1.2 - executables

Il faut aussi avoir accès aux exécutables suivants (leur chemin **doit être** spécifié correctement dans le fichier [lib_exe.py](scripts/lib_exe.py), afin qu'ils soient invocables tels quels en ligne de commande):
* tetgen
* mmg3D
* mmgs
* blender (pour séparer les mandibules proprement en deux)
* meshlabserver (qui est normalement installé avec meshlab)
* warping
* morphing
* medit

Super4PCS (librairies d'alignement global), n'est plus maintenu et je l'ai pour l'instant enlevé du dépôt, ainsi qu'une librairie pour faire des ICP en C++ (la version inclue dans les scripts en python suffit pour l'ICP).
Les anciens logiciels et librairies (pas besoin de les installer donc) sont:
* [libICP](https://github.com/symao/libicp)
* [Super4PCS](https://github.com/nmellado/Super4PCS)
* [Le remplaçant de Super4PCS](https://github.com/STORM-IRIT/OpenGR)

## 2 - Usage global et "philosophie"

Dans le dossier [scripts](scripts/) sont présents l'ensemble des fichiers python nécessaires, qui peuvent s'exécuter comme des exécutables indépendants (cf [SCRIPTS.md](scripts.md)).

#### tests.py : fichier de test sur des données bidons

Le fichier [tests.py](scripts/test.py) permet de tester que tout est installé et que les différents sripts utilisés lors de la reconstruction fonctionnent.

Il se lance ainsi:
```
python3 scripts/tests.py -d tests/ [-m]
```
A noter que l'option -m ouvrira chaque résultat avec medit, utile pour vérifier que les distances signées soient bien calculées, que les références pour les masques soient les bonnes...

L'ensemble des scripts testés sont en fait invoqués dans un fichier "global", ici [database.py](scripts/database.py), qui a vocation a gérer les différentes étapes de reconstruction (téléchargement, mise à l'échelle, alignement, warping, morphing... etc).

#### database.py: fichier global

**Ce script est instable et dépend pour l'instant encore trop de différents paramètres, et il n'est donc pas "mûr" à être utilisé de manière sure, et incomplet.**

Il récupère les fichiers présents dans des dossiers, et leur fait subir les transformations requises les unes après les autres, en écrivant (presque) à chaque fois les résultats dans un dossier différent.

Le script s'éxecute ainsi:
```
python3 scripts/database.py -d DATA_DIRECTORY -t TEMPLATES_DIRECTORY
```

avec:

* **DATA_DIRECTORY**: dossier (qui doit être créé avant de lancer le script) dans lequel les fichiers seront processés. Dans ce dossier seront créés d'autres dossiers pour chaque étape (objets "bruts", objets "remaillés", objets "mis à l'échelle", résultats du warping...), remplis par les résultats des différents scripts.
* **TEMPLATES_DIRECTORY**: dossier contenant les fichier .mesh servant de template pour différentes étapes de l'algorithme (sphère utilisée pour le warping, mandibule de référence pour l'aignement... etc.)

J'en ai enlevé la majorité des étapes de vérification qui permettent de ne pas agir sur les cas problématiques, ou d'utiliser la liste .csv, mais qui rajoutent beaucoup de complexité pour modifier ce script et y faire des tests...

L'idée est donc d'essayer d'avoir, dès le départ, uniquement les fichiers qui doivent marcher dans le dossier "raw", et de passer l'étape de téléchargement dans le script database.py.

## 3 - Comment modifier / rajouter des étapes?

#### créer un script python standalone

Pour créer une nouvelle étape, l'idée est à chaque fois de créer, autant que faire se peut, un nouveau script python exécutable en "stand-alone" avec un certain nombre d'arguments en ligne de commande.

Le fichier [transform.py](scripts/transform.py) qui permet d'appliquer des transformations spatiales à un maillage est un bon exemple de départ pour créer un nouveau script.

Quelques pistes pour un nouveau script:
* gérer les arguments en igne de commande avec *argparse*
* vérifier que les arguments soient corrects (que les fichiers existent par exemple)
* utiliser mesh = lib_msh.Mesh("fichier.mesh") pour ouvrir un fichier .mesh
* utiliser mesh.write("sortie.mesh") pour écrire un fichier .mesh
* entre temps, modifier les mesh.verts, mesh.tris, mesh.scalars, mesh.tets... qui correspondent aux éléments du maillage. Ce sont des tableaux 2D, dont la première dimension est de taille égale au nombre d'éléments, et la seconde au nombre de coordonnées ou d'indices, +1 pour garder la référence:
  * mesh.verts[0] = [x,y,z,référence] pour le premier vertex
  * mesh.verts[0,:3] = [x,y,z] du premier vertex
  * mesh.tris[:10,-1] = références des dix premiers triangles
  * mesh.tets[:,:4] = indices de tous les tétrahèdres (sans les références)

#### incorporer un programme extérieur

Pour incorporer un programme extérieur dans un script python, le plus pratique est d'utiliser la fonction lib_exe.execute() du fichier [lib_exe.py](scripts/lib_exe.py). Par exemple:

```
lib_exe.execute("mmgs_O3 maillage.mesh -o sortie.mesh -hausd 0.01 -hgrad 1.23")
```
ou, sous forme plus pratique pour utiliser des vriables comme argument du programme:
```
lib_exe.execute("mmgs_O3 %s -o %s -hausd %f -hgrad %d" % (maillage.mesh, sortie.mesh, 0.01, 1.23))
```

#### lancer plusieurs fonctions ou scripts en parallèle

Lorsqu'il faut traiter de nombreux cas, et donc essayer de bénéficier de la parallélisation, le mieux est d'encapsuler les actions à effectuer en parallèle dans une fonction prenant un seul argument (c'est ce qui est fait dans le fichier database.py), et d'utiliser la fonction "parallel" du fichier lib_exe:
```
lib_exe.parallel(maFonction, mesArguments)
```
Cette fonction va faire une boucle sur "mesArguments" (qui doit donc être une liste), et va lancer la fonction "maFonction" sur chacun des éléments de "mesArguments", en parallèle.

A noter que la fonction utilisée peut contenir des appels à des programmes exécutés en lignes de commande.

#### gérer les différentes étapes, et les fichiers déjà processés

Le script databse.py effectue un ensemble d'appels de fonctions sur les fichiers contenus dans des dossiers.

Au début du script, on convertit par exemple tous les fichiers .stl et .obj en fichiers .mesh:
* On créé une fonction "convert" qui prend comme argument le nom du fichier à convertir.
* Dans cette fonction, on lance le script convert.py avec les arguments créés à partir du nom du fichier, auquel on a rajouté le chemin des dossiers pertinents.
* On créé la liste de tous les fichiers présents dans le dossier "raw"
* On ne garde dans cette liste que les fichiers dont le nom n'est pas déjà dans le dossier "mesh"

Pour tester ou n'effectuer que quelques étapes, le mieux est par exemple d'utiliser la fonction **test()** du fichier database.py en suivant l'exemple qui y est mis ou en reprenant des items de la fonction run(), et de décommenter la fonction test à la toute fin du script, après `if __name__ == "__main__":`

## 4 - Usage indépendant des scripts

Se référer à [cette page de documentation](SCRIPTS.md) pour plus de détails sur l'utilisation des scripts présents dans le dossier [scripts/](scripts/).


## 5 - Problèmes
* Problème du warping et de la création d'objets "non-intersectants"
* Problème du morphing long
* Toutes les étapes ne sont pas cohérentes
* Valider sur un jeu de données test (séparation, tout ça)
* Appliquer wrapping/morphing... aux demi mandibules
* (Peut être) utiliser la liste
