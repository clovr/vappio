from twisted.internet import defer

from igs_tx.utils import defer_work_queue

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
        raise Error('Unknown type for %s: %r' % (configParam[0], configParam[1].get('type')))
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


@defer.inlineCallbacks
def validate(state, protocolConf, pipelineConf):
    success = []
    failure = []

    def _validateElement(elm):
        d = _validateType(state, pipelineConf, elm)
        d.addCallback(lambda v : success.extend(v))
        d.addErrback(lambda f : failure.append(f))
        return d

    def _validateElementFunc(elm):
        return lambda : _validateElement(elm)

    dwq = defer_work_queue.DeferWorkQueue(10)
    dwq.extend([_validateElementFunc(e) for e in protocolConf])
    yield defer_work_queue.waitForCompletion(dwq)

    if failure:
        failure[0].raiseException()

    defer.returnValue(success)
    
