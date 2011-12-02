import os
import json

def load(batchStateFile):
    if not os.path.exists(batchStateFile):
        return dump(batchStateFile, {})
    else:
        fin = open(batchStateFile)
        batchState = json.loads(fin.read())
        batchState = dict([(int(k), v)
                           for k, v in batchState.iteritems()])
        fin.close()
        return batchState

def dump(batchStateFile, batchState):
    fout = open(batchStateFile, 'w')
    fout.write(json.dumps(batchState, indent=1))
    fout.close()
    return batchState
