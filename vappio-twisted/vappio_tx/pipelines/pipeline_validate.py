from twisted.internet import defer

from igs.utils import functional as func

from igs_tx.utils import defer_utils

from vappio_tx.pipelines import pipeline_types

class Error(Exception):
    pass

def _determineTypeCallback(typ):
    sTyp = typ.split()
    if len(sTyp) == 2:
        nTyp, modifier = sTyp
        if nTyp in pipeline_types.TYPES and modifier in pipeline_types.TYPE_MODIFIERS:
            typF = pipeline_types.TYPES[nTyp]
            modifierF = pipeline_types.TYPE_MODIFIERS[modifier]
            return lambda state, value, params : modifierF(state, typF, value, params)
        else:
            raise Exception('Unknown type: %r' % typ)
    elif len(sTyp) == 1:
        if typ in pipeline_types.TYPES:
            return pipeline_types.TYPES[typ]
        else:
            raise Exception('Unknown type: %r' % typ)
    else:
        raise Exception('Unknown type: %r' % typ)

@defer.inlineCallbacks
def _validateType(state, pipelineConf, configParam):
    if not configParam[1].get('type'):
        raise Error('Unknown type for %s: %r' % (configParam[10], configParam[1].get('type')))
    typeCallback = _determineTypeCallback(configParam[1]['type'])
    try:
        newValue = yield typeCallback(state,
                                      pipelineConf[configParam[0]],
                                      configParam[1].get('type_params', {}))
        if not newValue and configParam[1].get('require_value', False):
            defer.returnValue([dict(message='A value is required for this option',
                                    keys=[configParam[0]])])
        else:
            transformName = configParam[1].get('type_params', {}).get('transform_name', configParam[0])
            pipelineConf[transformName] = newValue
            defer.returnValue([])
    except pipeline_types.InvalidPipelineValue, err:
        defer.returnValue([dict(message=str(err),
                                keys=[configParam[0]])])
    except pipeline_types.InvalidPipelineValueList, err:
        defer.returnValue([dict(message=str(e), keys=[configParam[0]]) for e in err.errorList])
        
def validate(state, protocolConf, pipelineConf):
    @defer.inlineCallbacks
    def _validateElements(acc, elms):
        values = yield defer.DeferredList(map(lambda elm : _validateType(state, pipelineConf, elm),
                                              elms))
        success = [v for s, v in values if s]
        failure = [f for s, f in values if not s]

        # If there are any failures just throw the first one
        if failure:
            failure[0].raiseException()

        res = []
        for i in success:
            res.extend(i)
        defer.returnValue(acc + res)

    # Validate 10 config options at a time
    return defer_utils.fold(_validateElements,
                            [],
                            func.chunk(10, protocolConf))
                            
