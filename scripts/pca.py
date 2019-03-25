import numpy as np
from scipy.spatial.distance import cdist
import os
import argparse
import sys
import lib_msh as msh

def scalar(d1,d2):
    return np.sum(np.multiply(d1,d2))
def read_data(filename):
    with open(filename,"r") as f:
        return np.array([[float(x) for x in l.split()] for l in f.readlines()[:4859]])
    return None
def center_data(d):
    return d - np.mean(d,axis=0)
def cov(d):
    return np.array([[scalar(x,y) for x in d] for y in d])
def eig(c):
    eVal, eVec = np.linalg.eig(c)
    eVec = eVec.transpose()
    idx = eVal.argsort()[::-1]
    eVal = eVal[idx]
    eVec = eVec[idx,:]
    return eVal, eVec
def get_principal_components(v, d):
    pc  = np.array([np.sum([v[i,j]*d[j] for j in range(len(d))],axis=0) for i in range(len(d))])
    pcn = [x/np.sqrt(scalar(x,x)) for x in pc]
    return pc, pcn
def reconstruct(pcn, d, n=None):
    alpha = np.array([[scalar(x,y) for y in pcn] for x in d])
    print(alpha)
    if n:
        return np.array([np.sum([alpha[i,j] * pcn[j] for j in range(n)], axis=0) for i in range(len(d))])
    else:
        return np.array([np.sum([alpha[i,j] * pcn[j] for j in range(len(d))], axis=0) for i in range(len(d))])
def PCA(d, u, n, debug=False):
    A = cov(d)
    eVal, eVec = eig(A)
    PC,PCN = get_principal_components(eVec, d)
    N = reconstruct(PCN, np.append(d,[u],axis=0), n)
    return N[-1]


if __name__ == "__main__":

    # Arguments
    parser = argparse.ArgumentParser(description="Runs a PCA")
    parser.add_argument("-t", "--training", help="training set", nargs="+", type=str, required=True)
    parser.add_argument("-u", "--unknown",  help="unknown mesh to reconstruct", type=str, required=True)
    parser.add_argument("-o", "--output",   help="output file to write the reconstructed mesh", type=str, required=True)
    args = parser.parse_args()

    # Transform the input dataset for PCA
    DATA = []
    for f in args.training:
        if f!= args.unknown:
            mesh = msh.Mesh(os.path.abspath(f))
            DATA.append(mesh.verts[:,:3])
    DATA = np.array(DATA)

    #Run the PCA to reconstruct the unknown mesh
    unknown = msh.Mesh(args.unknown)
    X = PCA(DATA, unknown.verts[:,:3], n=5)

    #Write it
    mesh=msh.Mesh()
    mesh.verts   = np.array([[x[0],x[1],x[2],0] for x in X])
    mesh.scalars = np.array([ np.sqrt(np.sum([(x-y)**2 for x,y in zip(v1,v2)])) for v1,v2 in zip(unknown,X)])
    mesh.tris    = unknown.tris
    mesh.write(args.output)
    mesh.writeSol(args.output.replace(".mesh", ".sol"))

    #Run a least square approcimation as a bonus
    B = np.linalg.norm(unknown,axis=1)
    A = np.transpose(np.array([np.linalg.norm(D,axis=1) for D in DATA]))
    scalars = np.linalg.lstsq(A, B)
    coefs = np.array(scalars[0])
    #Reduce it to a reduced least squares (only a few coefficients)
    n = 5
    inds = np.abs(coefs).argsort()[-n:][::-1]
    A = np.transpose(np.array([np.linalg.norm(D,axis=1) for D in DATA[inds]]))
    scalars = np.linalg.lstsq(A, B)
    coefs = np.array(scalars[0])
    #Create the final mesh from the least squares
    result = np.sum([ c * d for c,d in zip(coefs, DATA[inds]) ], axis=0) / n
    mesh=msh.Mesh()
    mesh.verts   = np.array([[x[0],x[1],x[2],0] for x in results])
    #mesh.scalars = np.array([ np.sqrt(np.sum([(x-y)**2 for x,y in zip(v1,v2)])) for v1,v2 in zip(unknown,proposed)])
    mesh.tris    = unknown.tris
    mesh.write(args.output.replace(".mesh", ".lstq.mesh"))
    mesh.writeSol(args.output.replace(".mesh", ".lstq.sol"))
