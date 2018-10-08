# FACILE

* 1 - Installation et dépendances
* 2 - Usage global et "philosophie"
* 3 - Modification et ajouts de nouveaux scripts
* 4 - Usage indépendant des scripts
* 5 - Problèmes


## 1 - Installation et dépendances

Les scripts sont écrits en **python 3**, attention à en avoir une version installée. Anaconda est le plus pratique et évite d'avoir à re-télécharger des librairies, mais python3 classique peut parfaitement suffire.

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

Il faut aussi avoir accès aux exécutables (qui doivent être dans le "PATH", et donc accessibles tels quels en ligne de commande):
* tetgen
* mmg3D_O3
* mmgs_O3
* blender (pour séparer les mandibules proprement en deux)
* meshlabserver (qui est normalement installé avec meshlab)

Et évidemment:
* warping
* morphing
* elasticity

Super4PCS (librairies d'alignement global), n'est plus maintenu et je l'ai pour l'instant enlevé du dépôt, ainsi qu'une librairie pour faire des ICP en C++ (la version inclue dans les scripts en python suffit pour l'ICP). Les logiciels (pas besoin de les installer donc) sont:
* [libICP](https://github.com/symao/libicp)
* [Super4PCS](https://github.com/nmellado/Super4PCS)
* [Le remplaçant de Super4PCS](https://github.com/STORM-IRIT/OpenGR)



## 2 - Usage global et "philosophie"

Dans le dossier [scripts](scripts/) sont présents l'ensemble des fichiers python nécessaires, qui peuvent s'exécuter comme des exécutables indépendants.

Ces scripts sont en fait appelés dans un fichier "global", ici [database.py](scripts/database.py), qui a vocation a gérer les différentes étapes de reconstruction (téléchargement, mise à l'échelle, alignement, warping, morphing... etc).

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

Voici une description et l'usage des scripts utilisés dans le script "global", database.py:

* donwload.py: Télécharge les fichiers depuis le serveur FTP
* convert.py: Transforme un fichier .stl ou .obj en .mesh
* transform.py: Met à l'échelle, déplace, et applique une matrice de transformation à un fichier .mesh
* merge.py: équivalent de ppfondre, fusionne plusieurs maillages en un
* icp.py: calcule la matrice de transformation d'une ICP entre deux maillages
* signed.py: calcule une distance signée, éventuellement en adaptant un maillage 3D avant (wrapper autour de mshdist)
* fill.py: remplit une surface avec un maillage volumétrique et une icosphère au centre pour le morphing
* morph.py: effectue un morphing entre un template et une distance signée
* split.ply: coupe proprement un fichier.mesh en deux sur l'axe X
* carve.py: reconstruit une enveloppe grossière voxelisée d'un fichier .mesh
* computeDistances.py: créé un .sol contenant la distance euclidienne entre deux fichiers .mesh
* levelset.py: extrait la surface levelset d'un résultat de mshdist
* mask.py: génère un masque volumique entre deux surfaces.
* pca.py: calcule les coefficients d'une PCA et reconstruit un objet avec une PCA sur un ensemble de .mesh

Certains sont encore à valider et il faudrait dans l'ensemble y rajouter des vérifications sur les arguments.

Dans l'ensemble des commandes ci dessous, les arguments entre crochets sont optionnels.

#### download.py

Télécharge tous les fichiers en ".stl" et ".mesh" depuis un dossier d'un serveur FTP, et les renomme en fonction de leur nom d'origine. "003_OsB.obj" sera ainsi téléchargé sous la forme de "003_bone.obj".

```
python3 download.py -a IP -u USER -p PWD -i FTPFOLDER -o LOCALFOLDER
```
* IP: adresse IP du serveur FTP
* USER: nom d'utilisateur sur le serveur
* PWD: mot de passe associé
* FTPFOLDER: chemin du dossier sur le serveur FTP depuis lequel télécharger les fichiers
* LOCALFOLDER: dossier local dans lequel télécharger les fichiers

par exemple:
```
python3 download.py -a 134.157.66.224 -u norgeot -p monmotdepasse -i Projets/FaciLe/Data/AllDataRaw -o /home/norgeot/facile_data
```

#### convert.py

Convertit un fichier .obj ou .stl en .mesh à l'aide de meshlabserver pour éviter les problèmes de fichiers binaires.

```
python3 convert.py -i INPUT -o OUTPUT
```
* INPUT: chemin vers le fichier .obj ou .stl
* OUTPUT: chemin du nouveau fichier .mesh

par exemple:
```
python3 convert.py -i monObjet.obj -o monObjet.mesh
```

#### transform.py

Peut être utilisé pour:
* mettre à l'échelle 1 (la dimension maximale de l'objet sera 1) et centrer un .mesh en .5 .5 .5
* simplement mettre à l'échelle et/ou déplacer un .mesh
* appliquer une matrice de transformation à un maillage (issue par exemple du calcul d'ICP)

```
python transform.py -i INPUT -o OUTPUT [-s sx sy sz] [-t tx ty tz] [-c] [-m MATRIX]
```
* INPUT: Fichier .mesh d'entrée
* OUTPUT: fichier .mesh transformé
* sx, sy, sz: facteur d'échelle selon x, y et z
* tx, ty, tz: translation selon x, y et z
* -c: flag booléen à utiliser seul pour mettre à l'échelle 1 et translater en .5 .5 .5 un .mesh
* MATRIX: fichier .txt contenant une matrice de transformation à appliquer à l'objet

par exemple:
```
python3 transform.py -i input.mesh -o transformed.mesh -c
python3 transform.py -i input.mesh -o transformed.mesh -s 0.0035 0.0035 0.0035
python3 transform.py -i input.mesh -o transformed.mesh -m matrix.txt
```

#### merge.py

Fusionne plusieurs .mesh en un. Equivalent de ppfondre.

```
python3 merge.py -i FILES -o OUTPUT
```
* FILES: liste de fichiers .mesh à fusionner. Supporte les wildcard: "toto*.mesh"
* OUTPUT: fichier fusionné

par exemple:
```
python3 merge.py -i /home/norgeot/*.mesh -o merged.mesh
python3 merge.pyt -i /home/norgeot/fichier1.mesh /home/norgeot/fichier2.mesh -o merged.mesh
```

#### icp.py

Calcule le résultat de la transformation par ICP d'un maillage source vers un maillage cible. Les deux maillages doivent déjà être "relativement" proches pour obtenir de bons résultats.

```
python3 icp.py -s SOURCE -t TARGET -m MATRIX [-mIts ITERATIONS] [-mPts MAXPTS] [-tol TOLERANCE]
```
* SOURCE: fichier .mesh de la source (objet à transformer)
* TARGET: fichier .mesh de la cible (fichier vers lequel transformer)
* MATRIX: fichier txt dans lequel écrire la matrice de transformation obtenue
* ITERATIONS: nombre d'itérations maximum, défaut 200
* MAXPTS: nombre maximum de points sur lesquels calculer l'ICP (pratique pour les gros maillages), défaut 5000
* TOLERANCE: tolérance pour la convergence, défaut 1e-4

par exemple:
```
python3 icp.py -s source.mesh -t target.mesh -m matrix.txt -mPts 15000
```

#### signed.py

Calcule la distance signée par rapport à un fichier .mesh, en créant ou adaptant un domaine de calcul au préalable.

```
python3 signed.py -i INPUT -o OUTPUT [-v VOLUME]
```
* INPUT: fichier .mesh représentant la surface à laquelle on souhaite calculer la distance
* OUTPUT: fichier .mesh qui contiendra le résultat
* VOLUME: .mesh contenant des tétrahèdres et sur lequel ser calculé la distance signée.

A noter que par défaut, un mailage volumique entourant l'objet est créé et adapté à l'objet cible. Cela permet par la suite à mshdist de calculer une distance signée sur un maillage dont les éléments sont plus petits aux abords de la surface.  

Si un volume est fourni, il est utilisé comme maillage de référence, mais est quand même remaillé pour adapter à la surface.

Il faudrait donc modifier le script pour calculer directement la distance signée sur le volume fourni, ce qui équivaudrait en fait à simplement exécuter mshdist.

#### fill.py

Remplit une surface avec un maillage volumétrique et une icosphère au centre. Cette étape est nécessaire pour pouvoir effectuer le morphing.

```
python3 fill.py -i INPUT -o OUTPUT [-c cx cy cz] [-r RADIUS]
```
* INPUT: .mesh pour la surface à remplir
* OUTPUT: .mesh de sortie
* cx, cy, cz: coordonnées du centre de l'icosphère à inclure dans la surface (défaut 0,0,0)
* RADIUS: rayon de l'icosphère (défaut 0.1)


#### morph.py

Lance le morphing d'un maillage préparé auparavant avec preparemorph.py vers une distance signée.

#### split.py

Coupe un fichier .mesh en son milieu sur l'axe des X, en gardant la partie des x positifs ou négatifs. Basé sur blender pour faire une coupe "nette", ce script est différent des autres en ce qu'il doit être exécuté via blender en ligne de commande.

```
blender --background -python split.py -- -i INPUT -o OUTPUT -x X
```
* INPUT: .mesh d'entrée à couper en son centre (doit donc être centré en X)
* OUTPUT: fichier de sortie à écrire
* X: +1 (pour garder la partie des x positifs et effectuer une symétrie) ou -1 (partie de gauche, pas d'autres transformations)

par exemple:
```
blender --background -python split.py -- -i mandibule.mesh -o mandibule.right.mesh -x 1
blender --background -python split.py -- -i mandibule.mesh -o mandibule.left.mesh -x -1
```

Attention, les fichiers ainsi créés ne sont pas centrés en 0,0,0!

#### carve.py

Créé une enveloppe grossière d'un fichier .mesh avec une technique de "Space Carving", qui a pour effet de voxeliser l'objet. Peut être plus approprié qu'une enveloppe convexe pour préparer le warping et obtenir une surface manifold après remaillage par exemple.

```
python3 carve.py -i INPUT -o OUTPUT [-r RESOLUTION]
```
* INPUT: fichier .mesh à "carver"
* OUTPUT: fichier de sortie
* RESOLUTION: resolution de la grille de voxels à considérer, défaut à 51. Mettre une valeur plus petite si les points sont épars, on peut mettre une valeur plus grande pour un maillage très dense.

#### distance.py

Calcule la distance euclidienne entre deux fichiers .mesh sous la forme d'un .sol. A noter que les deux maillages doivent avoir le même nombre de points.

```
python3 distance.py -i1 INPUT1 -i2 INPUT2 -o OUTPUT
```
* INPUT1: premier fichier .mesh
* INPUT2: second .mesh
* OUTPUT: fichier .mesh ou .sol à écrire. Si le format est .mesh, le fichier et son .sol associé seront créés, si .sol, seulement la solution.

par exemple:
```
python3 distance.py -i1 fichier1.mesh -i2 fichier2.mesh -o distance.sol
```

#### levelset.py

Extrait la surface correspondant à une valeur spécifiée de levelset (donc la surface de référence 10 suite à l'extraction avec mmg3d) pour un .mesh tétrahédrique contenant une information de distance signée.

```
python3 levelset.py -i INPUT -o OUTPUT [-d HAUSDORFF] [-l LEVELSET]
```
* INPUT: fichier.mesh d'entrée, doit correspondre à une sortie de mshdist
* OUTPUT: .mesh de sortie, ne contiendra que la surface
* HAUSDORFF: distance d'Hausdorff, défaut à 0.01
* LEVELSET: valeur pour le levelset, défaut à 0

#### mask.py

Génère un masque volumétrique à partir d'une surface intérieure et d'une surface extérieure.

```
python3 mask.py -i INTERIOR -e EXTERIOR -o OUTPUT [-t TEMPLATE]
```
* INTERIOR: surface intérieure
* EXTERIOR: surface extérieure
* OUTPUT: fichier de sortie
* TEMPLATE: fichier .mesh qui permettra d'écrire un .sol affecté à l'intérieur du masque (Dirichlet) correspondant au champ de déplacement entre la surface intérieure et ce fichier

A noter que les surfaces intérieure et extérieures doivent être manifold, et donc ne pas avoir d'intersections.

Pour l'écriture des conditions de Dirichlet, le .sol à écrire devrait en fait contenir les résultats du morphing.

#### pca.py

Lance une PCA pour reconstruire un maillage "inconnu" en se basant sur un ensemble de maillages.

```
python3 pca.py -t TRAINING -u UNKNOWN -o OUTPUT
```
* TRAINING: liste des fichiers .mesh permettant de calculer les composantes principales
* UNKNOWN: maillage inconnu à reconstruire dans l'espace créé
* OUTPUT: fichier .mesh de sortie

par exemple:
```
python3 pca.py -t warped/*.mesh -u unknownskull.mesh -o recon.mesh
```

Ce script n'est pas définitif, en ce que plusieurs actions peuvent être à réaliser avec:
* Calculer les coefficients uniquement
* Reconstruire un maillage dans une base existante en utilisant n composantes
* Enregistrer les coefficients de l'analyse
* ...

Par défaut, le script calcule ainsi une PCA sur les maillages d'entrée, reconstruit le maillage inconnu à l'aide des 15 premières composantes, et lance également une reconstruction à partir des maillages du set de training grâce à une méthode des moindre carrés réduite, qui n'est pas nécessairement pertinente pour l'algorithme (5 composants ici).

Le fichier de sortie en ".mesh" correspondra à la reconstruction via PCA, celui en ".lstq.mesh" via la méthode des moindres carrés.
