import os
from functools import wraps
import subprocess as sp
import multiprocessing as mp
import time
import tempfile
import sys

#Import des executables
from lib_paths import *

"""
for exe in [medit, mmgs, mmg3d, tetgen, mshdist, warping, morphing, python, blender, meshlabserver]:
    try:
        execute(exe + "--help")
    except:
        print("Error: " + exe + "is either:\n\tnot accessible from the command line as specified in lib_exe.py\n\tnot installed\n\tcan't run with the flag --help\nYou'll have to fix this!")
        sys.exit(1)
"""

class FacileError(Exception):
    pass

def debug():

    def true_decorator(f):

        @wraps(f)
        def wrapped(*args, **kwargs):

            print(f.__name__ + " : " + '\033[94m' + "RUNNING" + '\033[0m' + " on " + str(args))

            t   = time.time()
            r   = None
            cwd = os.getcwd()

            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    os.chdir(tmpdir)
                    r = f(*args, **kwargs)
                    print(f.__name__ + " : "+'\033[92m'+"SUCCESS"+'\033[0m'+" on " + str(args) + ", in " + str(int(time.time() - t)) + " s")

            except Exception as e:
                print(f.__name__ + " : "+'\033[91m'+"FAILURE"+'\033[0m'+" on " + str(args) + ": " + type(e).__name__ + ": " + str(e) + ", in " + str(int(time.time() - t)) + " s")
                pass

            finally:
                os.chdir(cwd)
                return r

        return wrapped

    return true_decorator

def parallel(func, items, ncpus = 14): #ncpus=128):
    if len(items)>0:
        num = min( ncpus, min(len(items), mp.cpu_count()-1 ))
        print('\033[95m' + "## EXECUTING '" + func.__name__ + "' on " + str(len(items)) + " cases and " + str(num) + " process(es)." + '\033[0m')
        res = mp.Pool(processes=num).map(func, items )
        return res
    else:
        print('\033[95m' + "## SKIPPING '" + func.__name__ + "', no data found." + '\033[0m')
        pass

def execute(cmd, msg="erreur"):
    try:
        print("Running '" + cmd + "'")
        process  = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = [x.strip() for x in process.communicate()]
        code     = process.returncode
        if code:
            print("Error running '" + cmd + "'\n" + "OUTPUT:\n" + str(out) + "ERROR:\n" + str(err))
            #raise Exception(msg)
    except:
        print("Error running '" + cmd + "'\n")

# Functions to create commands
def python_cmd(f):
    return python + os.path.abspath(os.path.join(os.path.dirname(__file__),f)) + " "
def blender_cmd(f):
    return blender + "--background --python " + os.path.abspath(os.path.join(os.path.dirname(__file__),f)) + " -- "
