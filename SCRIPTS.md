# FACILE

Voici une description et l'usage des scripts utilisés dans le script "global", database.py:

* carve.py: reconstruit une enveloppe grossière voxelisée d'un fichier .mesh
* convert.py: Transforme un fichier .stl ou .obj en .mesh
* distance.py: créé un .sol contenant la distance euclidienne entre deux fichiers .mesh
* donwload.py: Télécharge les fichiers depuis le serveur FTP
* fill.py: remplit une surface avec un maillage volumétrique et une icosphère au centre pour le morphing
* icp.py: calcule la matrice de transformation d'une ICP entre deux maillages
* levelset.py: extrait la surface levelset d'un résultat de mshdist
* mask.py: génère un masque volumique entre deux surfaces.
* merge.py: équivalent de ppfondre, fusionne plusieurs maillages en un
* morph.py: effectue un morphing entre un template et une distance signée
* pca.py: calcule les coefficients d'une PCA et reconstruit un objet avec une PCA sur un ensemble de .mesh
* shell.py: créé une enveloppe volumique autour d'un maillage surfacique, utile pour le warping
* signed.py: calcule une distance signée, éventuellement en adaptant un maillage 3D avant (wrapper autour de mshdist)
* split.ply: coupe proprement un fichier.mesh en deux sur l'axe X
* transform.py: Met à l'échelle, déplace, et applique une matrice de transformation à un fichier .mesh
* warp.py: effectue le warping d'une "coque" 3D vers un maillage surfacique

Certains sont encore à valider et il faudrait dans l'ensemble y rajouter des vérifications sur les arguments.

Dans l'ensemble des commandes ci dessous, les arguments entre crochets sont optionnels.

#### carve.py

Créé une enveloppe grossière d'un fichier .mesh avec une technique de "Space Carving", qui a pour effet de voxeliser l'objet. Peut être plus approprié qu'une enveloppe convexe pour préparer le warping et obtenir une surface manifold après remaillage par exemple.

```
python3 carve.py -i INPUT -o OUTPUT [-r RESOLUTION]
```
* INPUT: fichier .mesh à "carver"
* OUTPUT: fichier de sortie
* RESOLUTION: resolution de la grille de voxels à considérer, défaut à 51. Mettre une valeur plus petite si les points sont épars, on peut mettre une valeur plus grande pour un maillage très dense.

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

#### fill.py

Remplit une surface avec un maillage volumétrique et une icosphère au centre. Cette étape est nécessaire pour pouvoir effectuer le morphing.

```
python3 fill.py -i INPUT -o OUTPUT [-c cx cy cz] [-r RADIUS]
```
* INPUT: .mesh pour la surface à remplir
* OUTPUT: .mesh de sortie
* cx, cy, cz: coordonnées du centre de l'icosphère à inclure dans la surface (défaut 0,0,0)
* RADIUS: rayon de l'icosphère (défaut 0.1)

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

#### morph.py

Lance le morphing d'un maillage préparé auparavant avec preparemorph.py vers une distance signée.

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

#### shell.py
Creates a shell

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

#### warp.py
Warps!!!
