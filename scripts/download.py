import os
from ftplib import FTP
import argparse
import sys
import lib_exe

args = None

def rename(f):
    #Get the number
    num = f.split(".")[1].zfill(3)
    #Get the root (face, bone...)
    root = "unidentified"
    names = [
        ["OsB","bone"],
        ["SkullB","bone"],
        ["MandB","mand"],
        ["BTeeB","btee"],
        ["HTeeB","htee"],
        ["Mass","mass"],
        ["FatB","face"]
    ]
    for n in names:
        if n[0] in f:
            root = n[1]
            break
    return "%d_%s%s" % (num, root, os.path.splitext(f)[1])

def ftp_copy(f):

    ftp = FTP(args.ip, args.user, args.pwd)
    ftp.cwd(ftpDir)

    localFile = os.path.join(args.output, rename(f))

    if not os.path.exists(localFile):
        with open(localFile, 'wb') as ff:
            ftp.retrbinary('RETR %s' % f, ff.write)

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Download .stl, .obj and .mesh files from a FTP folder")
    parser.add_argument("-a", "--ip",     type=str, help="FTP IP adress", required=True)
    parser.add_argument("-u", "--user",   type=str, help="FTP username",  required=True)
    parser.add_argument("-p", "--pass",   type=str, help="FTP password",  required=True)
    parser.add_argument("-i", "--input",  type=str, help="FTP folder",    required=True)
    parser.add_argument("-o", "--output", type=str, help="Output folder", required=True)
    args = parser.parse_args(sys.argv[1:])

    #List the .mesh and .stl files in the FTP directory
    ftp = FTP(args.ip, args.user, args.pwd)
    ftp.cwd(args.input)
    files = [ f for f in ftp.nlst() if ".mesh" in f or ".stl" in f or ".obj" in f]
    files = [ f for f in files if not os.path.exists( os.path.join(args.output, f.split(".")[1].zfill(3) + "_" + rename(f) + ".mesh") )]
    files.sort(key=lambda f: int(f.split(".")[1]))

    #Copy the files to the local directory
    lib_exe.parallel(ftp_copy, files)

    # I.3 - Clean the meshes in rawFolder
    files = [os.path.join(directories["raw"], f) for f in os.listdir(directories["raw"]) if ".mesh" in f] if len(files) else []
    files.sort()
    run(cleanMesh, files)
