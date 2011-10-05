
from igs.utils import functional as func

from igs_tx.utils import defer_pipe

from vappio_tx.utils import queue

from vappio_tx.pipelines import protocol_format
from vappio_tx.pipelines import pipeline_misc

def handleWWWListProtocols(request):
    """
    Input:
    { cluster: string
      ?criteria: { key/value }
      ?detail: boolean
    }
    Output:
    [{ protocol: string, config: [ { key/value } ]}]
    """
    def _removeAlwaysHidden(protocolConfig):
        return [pc
                for pc in protocolConfig
                if pc[1].get('visibility') != 'always_hidden']

    if 'criteria' in request.body:
        if '$or' in request.body['criteria']:
            protocolNames = [p['protocol'] for p in request.body['criteria']['$or']]
            protocolF = lambda p : p in protocolNames
        elif 'protocol' in request.body['criteria']:
            protocolF = lambda p : p == request.body['criteria']['protocol']
        else:
            protocolF = lambda _ : True
    else:
        protocolF = lambda _ : True
    
    protocols = [p
                 for p in protocol_format.protocols(request.state.machineconf)
                 if protocolF(p)]

    protocolConfs = []
    for p in protocols:
        protocolConfig = protocol_format.load(request.state.machineconf, p)
        wrapperName = pipeline_misc.determineWrapper(request, p)
        if wrapperName != p:
            protocolConfig += protocol_format.load(request.state.machineconf, wrapperName)

        if request.body.get('detail', False):
            conf = [func.updateDict(c[1], {'name': c[0]})
                    for c in _removeAlwaysHidden(protocolConfig)]
        else:
            conf = []
            
        protocolConfs.append({'protocol': p, 'config': conf})
    
    return defer_pipe.ret(request.update(response=protocolConfs))

def subscribe(mq, state):
    processListProtocols = queue.returnResponse(defer_pipe.pipe([queue.keysInBody(['cluster',
                                                                                   'user_name']),
                                                                 pipeline_misc.forwardToCluster(state.conf,
                                                                                                state.conf('pipelines.listprotocols_www')),
                                                                 handleWWWListProtocols]))
    queue.subscribe(mq,
                    state.conf('pipelines.listprotocols_www'),
                    state.conf('pipelines.concurrent_listprotocols'),
                    queue.wrapRequestHandler(state, processListProtocols))
