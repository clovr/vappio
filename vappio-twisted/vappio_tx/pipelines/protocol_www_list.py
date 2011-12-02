
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
      ?batch_mode: boolean
    }
    Output:
    [{ protocol: string, config: [ { key/value } ]}]
    """
    def _removeAlwaysHidden(protocolConfig):
        return [pc
                for pc in protocolConfig
                if pc[1].get('visibility') != 'always_hidden']

    # Create a criterial filter called protocolF
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

    # Get all protocols and filter out the ones we don't need
    protocols = [p
                 for p in protocol_format.protocols(request.state.machineconf)
                 if protocolF(p)]

    if request.body.get('batch_mode'):
        batchConfig = [func.updateDict(c[1], {'name': c[0]})
                       for c in _removeAlwaysHidden(protocol_format.load(request.state.machineconf,
                                                                         'clovr_batch_wrapper'))]
    else:
        batchConfig = []
    
    protocolConfs = []
    for p in protocols:
        protocolConfig = protocol_format.load(request.state.machineconf, p)
        wrapperName = pipeline_misc.determineWrapper(request.state.machineconf, p)
        if wrapperName != p:
            protocolConfig += protocol_format.load(request.state.machineconf, wrapperName)

        if request.body.get('detail', False):
            conf = [func.updateDict(c[1], {'name': c[0]})
                    for c in _removeAlwaysHidden(protocolConfig)]
            if request.body.get('batch_mode', False):
                conf = batchConfig + [func.updateDict(c, {'name': 'batch_pipeline.' + c['name']})
                                      for c in conf]
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
