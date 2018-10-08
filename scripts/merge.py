import os
import argparse
import lib_msh

if __name__ == "__main__":

    #arguments
    parser = argparse.ArgumentParser(description="Merges multiple .mesh together")
    parser.add_argument("-i", "--input",  type=str, nargs="+", help="Input .mesh files", required=True)
    parser.add_argument("-o", "--output", type=str, help="Output .mesh file", required=True)
    args = parser.parse_args()


    original = lib_msh.Mesh(args.input[0])
    for other in args.input[1:]:
        original.fondre(lib_msh.Mesh(other))
    original.write(args.output)
