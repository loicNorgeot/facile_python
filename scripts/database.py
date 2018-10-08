import lib_exe
import lib_msh
import os
import argparse

#Fonction pour créer les commandes (à ajuster e fonction du chemin de blender par exemple)
def python(f):
    return "python3.5 " + os.path.abspath(os.path.join(os.path.dirname(__file__),f)) + " "
def blender(f):
    return "blender --background --python " + os.path.abspath(os.path.join(os.path.dirname(__file__),f)) + " -- "

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
        "raw",
        "mesh",
        "scaled",
        "remeshed",
        "merged",
        "aligned",
        "warped",
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

#Fonction pour lancer l'ensemble du process
def run():
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
    lib_exe.execute( python("download.py") + "-a %s -u %s -p %s -i %s -o %s" % (IP, USR, PWD, DIR, OUT))
    """

    # 2 - Convert all the downloaded files to .mesh
    def convert(f):
        IN  = os.path.join(directories["raw"], f)
        OUT = os.path.join(directories["mesh"], f.replace("obj","mesh").replace("stl","mesh"))
        lib_exe.execute( python("convert.py") + "-i %s -o %s" % (IN, OUT))
    FILES = [f for f in os.listdir(directories["raw"]) if os.path.splitext(f)[1] in [".obj", ".stl"]]
    FILES = [f for f in FILES if f.replace(".obj", ".mesh").replace(".stl",".mesh") not in os.listdir(directories["mesh"])]
    lib_exe.parallel(convert, FILES)

    # 3 - Scale everything
    def scale(group):
        center = lib_msh.Mesh([os.path.join(directories["mesh"], g) for g in group if "bone" in g][0]).center
        for g in group:
            IN    = os.path.join(directories["mesh"], g)
            OUT   = os.path.join(directories["scaled"], g)
            SCALE = 0.0035
            TRANS = -center + 0.5
            lib_exe.execute( python("transform.py") + "-i %s -o %s -s %f %f %f -t %f %f %f" % (IN, OUT, SCALE, SCALE, SCALE, TRANS[0], TRANS[1], TRANS[2]))
    cases = set([f[:3] for f in os.listdir(directories["mesh"])])
    FILES = [[f for f in os.listdir(directories["mesh"]) if f.startswith(case)] for case in cases]
    FILES = [f for f in FILES if f not in os.listdir(directories["scaled"])]
    lib_exe.parallel(scale, FILES)

    # 4 - Remesh all the files
    def remesh(f):
        IN    = os.path.join(directories["scaled"], f)
        HAUSD = 0.0025
        OUT   = os.path.join(directories["remeshed"], f)
        lib_exe.execute("mmgs_O3 %s -nr -nreg -hausd %f -o %s > /dev/null 2>&1" % (IN, HAUSD, OUT))
    FILES = [f for f in os.listdir(directories["scaled"]) if ".mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories["remeshed"])]
    lib_exe.parallel(remesh, FILES)

    # 5 - Merge the bones (skull, mandibles and teeth) together
    def merge(group):
        OUT   = os.path.join(directories["merged"], group[0][:4] + "bone.mesh")
        lib_exe.execute( python("merge.py") + "-i %s -o %s" % (" ".join([os.path.join(directories["remeshed"], g) for g in group]), OUT))
    cases = set([f[:3] for f in os.listdir(directories["remeshed"])])
    GROUPS = [[f for f in os.listdir(directories["remeshed"]) if f.startswith(case) and f.endswith(".mesh") and "mass" not in f and "face" not in f] for case in cases]
    lib_exe.parallel(merge, GROUPS)

    # 6 - Align the models
    def align(group):
        SOURCE = os.path.join(directories["merged"], [g for g in group if "bone" in g][0])
        TARGET = templates["bone"]
        FILE   = os.path.join(directories["merged"], group[0][:4] + "icp_matrix.txt")
        lib_exe.execute( python("icp.py") + "-s %s -t %s -m %s" % (SOURCE, TARGET, FILE))
        for g in group:
            IN  = os.path.join(directories["merged"], g)
            OUT = os.path.join(directories["aligned"], g)
            lib_exe.execute( python("transform.py") + "-i %s -o %s -m %s" % (IN, OUT, FILE))
    cases = set([f[:3] for f in os.listdir(directories["merged"])])
    GROUPS = [[f for f in os.listdir(directories["merged"]) if f.startswith(case) and f.endswith(".mesh")] for case in cases]
    lib_exe.parallel(align, GROUPS)

    # 7 - Warp the bones
    def warp(f):
        IN   = os.path.join(directories["aligned"], f)
        NIT  = 150
        LOAD = 40
        os.system("cp " + templates["sphere"] + " ./sphere.mesh")
        lib_exe.execute("warping %s -p -nit %d -load %d > /dev/null 2>&1" % (IN, NIT, LOAD))
        warped = msh.Mesh("./sphere.d.mesh")
        ext_ref = 2
        warped.tris = warped.tris[warped.tris[:,-1] != ext_ref]
        warped.tets = np.array([])
        warped.discardUnused()
        warped.write(os.path.join(directories["warped"],f))
    FILES = [f for f in os.listdir(directories["aligned"]) if ".mesh" in f]
    FILES = [f for f in FILES if f not in os.listdir(directories["warped"])]
    lib_exe.parallel(warp, FILES)

    # 8 - Compute the signed distances on the warped bones...
    def signed(f):
        IN  = os.path.join(directories["warped"], f)
        OUT = os.path.join(directories["signed"], f)
        BOX = templates["box"]
        lib_exe.execute( python("signed.py") + "-i %s -o %s -v %s" % (IN, OUT, BOX))
    FILES = [f for f in os.listdir(directories["warped"]) if "bone" in f and f.endswith(".mesh")]
    FILES = [f for f in FILES if f not in os.listdir(directories["signed"])]
    lib_exe.parallel(signed, FILES)

    # 9 - ... and on the faces
    def signed(f):
        IN  = os.path.join(directories["aligned"], f)
        OUT = os.path.join(directories["signed"], f)
        BOX = templates["box"]
        lib_exe.execute( python("signed.py") + "-i %s -o %s -v %s" % (IN, OUT, BOX))
    FILES = [f for f in os.listdir(directories["aligned"]) if "face" in f and f.endswith(".mesh")]
    FILES = [f for f in FILES if f not in os.listdir(directories["signed"])]
    lib_exe.parallel(signed, FILES)

    # 10 - Morph the template skull to every skull...
    def morph(f):
        IN  = os.path.join(directories["signed"], f)
        OUT = os.path.join(directories["morphed"], f)
        TMP = templates["morphingSkull"]
        lib_exe.execute( python("morph.py") + "-t %s -s %s -o %s" % (TMP, IN, OUT))
    FILES = [ os.path.join(directories["signed"],f) for f in os.listdir(directories["signed"]) if "bone" in f and f.endswith("mesh") ]
    FILES = [f for f in FILES if f not in os.listdir(directories["morphed"])]
    lib_exe.parallel(morph, FILES)

    # 11 - ... and the templace face to every face
    def morph(f):
        IN  = os.path.join(directories["signed"], f)
        OUT = os.path.join(directories["morphed"], f)
        TMP = templates["morphing"]
        lib_exe.execute( python("morph.py") + "-t %s -s %s -o %s" % (TMP, IN, OUT))
    FILES = [ os.path.join(directories["signed"],f) for f in os.listdir(directories["signed"]) if "face" in f and f.endswith("mesh") ]
    FILES = [f for f in FILES if f not in os.listdir(directories["morphed"])]
    lib_exe.parallel(morph, FILES)

    # 12 - Generate the masks
    def mask(group):
        faces = [ os.path.join(directories["morphed"],f) for f in os.listdir(directories["morphed"]) if "face.mesh" in f]
        bones = [ os.path.join(directories["morphed"],f) for f in os.listdir(directories["morphed"]) if "bone.mesh"  in f]
        files = [[b,f] for b in bones for f in faces if f.split("/")[-1][:3]==b.split("/")[-1][:3]]
        files.sort()
        files = [f for f in files if f[0].split("/")[-1][:3] + "_mask.mesh" not in "".join(os.listdir(directories["masked"]))]
        lib_exe.parallel(mask, GROUPS)
    FILES = [ os.path.join(directories["signed"],f) for f in os.listdir(directories["signed"]) if "face" in f and f.endswith("mesh") ]
    FILES = [f for f in FILES if f not in os.listdir(directories["masked"])]
    lib_exe.parallel(mask, FILES)

    ################################################################################
    # 2 - Prepare the mandibles and masseters (cut them in half and position)
    ################################################################################

    # 1 - Cut the raw mandibles and masseters in half
    def split(f):
        #Scale to one unit and center
        IN    = os.path.join(directories["mesh"], f)
        TMP   = os.path.join(directories["splitted"], f.replace(".mesh", ".tmp.mesh"))
        lib_exe.execute( python("transform.py") + "-i %s -o %s -c" % (IN, TMP))
        #Split in half
        TMP_R = os.path.join(directories["splitted"], f.replace(".mesh", ".tmp.R.mesh"))
        TMP_L = os.path.join(directories["splitted"], f.replace(".mesh", ".tmp.L.mesh"))
        lib_exe.execute(blender("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_R, 1))
        lib_exe.execute(blender("split.py") + "-i %s -o %s -x %d" %  (TMP, TMP_L, -1))
        #Move the halves to .5 .5 .5
        OUT_R = os.path.join(directories["splitted"], f.replace(".mesh", ".R.mesh"))
        OUT_L = os.path.join(directories["splitted"], f.replace(".mesh", ".L.mesh"))
        lib_exe.execute( python("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_R, OUT_R, .75, .5, .5))
        lib_exe.execute( python("transform.py") + "-i %s -o %s -t %f %f %f" % (TMP_L, OUT_L, .75, .5, .5))
        #Remove the temporary files
        os.remove(TMP)
        os.remove(TMP_L)
        os.remove(TMP_R)
    FILES = [f for f in os.listdir(directories["mesh"]) if "mand" in f or "mass" in f]
    FILES = [f for f in FILES if f.replace(".mesh", ".R.mesh") not in os.listdir(directories["splitted"])]
    lib_exe.parallel(split, FILES)

#Fonction pour tester une étape
def test():
    args = get_arguments()
    templates, directories = create_templates_and_directories(args)

    #directories
    input_dir = "/home/norgeot/test/"
    output_dir = "/home/norgeot/test_sortie/"

    #Create a function to translate one .mesh file on the Y axis by 2, and remesh with mmgs
    def move(filepath):
        #Get the input and output paths
        IN  = os.path.join(input_dir, f)
        OUT = os.path.join(output_dir, f)

        #Open the .mesh file
        mesh = lib_msh.Mesh( IN )
        #Move the vertices by 2 on the Y axis
        mesh.verts[:,1] += 2
        #Change the reference of the tetrahedron to 3
        mesh.tets[:,-1] = 3
        #Write the mesh to a temporary file
        mesh.write("tmp.mesh")

        #Run mmgs
        lib_exe.execute("mmgs_O3 %s -o %s -hausd 0.1" % ("tmp.mesh", OUT))

        #Remove the unnecessary files
        os.remove("tmp.mesh")
        os.remove(OUT.replace(".mesh", ".sol"))

    #List the files in the input directory, which have "toto" and .mesh in their names
    FILES = [f for f in os.listdir(input_dir) if "toto" in f and ".mesh" in f]

    #Remove the files from the list which are already in the  output directory
    FILES = [f for f in FILES if f not in os.listdir(output_dir)]

    #Run the function "move" on all the files in parallel
    lib_exe.parallel(move, FILES)

    #list the files in the output directory
    print("Fichiers de sortie:")
    for f in os.listdir(output_dir):
        print(f)

if __name__ == "__main__":
    run()
    #test()
