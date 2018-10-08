import os
from functools import wraps
import subprocess as sp
import multiprocessing as mp
import time
import tempfile

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

def parallel(func, items, ncpus=128):
    num = min( ncpus, min(len(items), mp.cpu_count()-1 ))
    print('\033[95m' + "## EXECUTING '" + func.__name__ + "' on " + str(len(items)) + " cases and " + str(num) + " process(es)." + '\033[0m')
    res = mp.Pool(processes=num).map(func, items )
    return res

def execute(cmd, msg="erreur"):
    print("Running '" + cmd + "'")
    process  = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    out, err = process.communicate()
    code     = process.returncode
    if code:
        print("Error running '" + cmd + "'\n" + "OUTPUT:\n" + str(out) + "ERROR:\n" + str(err))
        raise Exception(msg)
