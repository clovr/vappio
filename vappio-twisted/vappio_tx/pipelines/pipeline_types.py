#
# This implements validation for all of the types
# Every type takes a state containing the message queue and component config ad pipeline config,
# value, and type parameters
# On success, the new value is returned
# On failure, a useful error messages must be returned
import os
import time
import json

from twisted.internet import defer

from vappio_tx.pipelines import pipeline_type_utils as ptu

from vappio_tx.internal_client import credentials as cred_client

class InvalidPipelineValue(Exception):
    pass

class InvalidPipelineValueList(Exception):
    def __init__(self, errorList):
        self.errorList = errorList

def t_string(_state, value, _params):
    """
    string does nothing but evaluate to itself
    """
    return defer.succeed(value)

def t_restricted_string(_state, value, params):
    """
    restricted_string is limited to a set of choices
    """
    if 'choices' not in params:
        return defer.fail(InvalidPipelineValue('Must provide choices'))
    elif value not in params['choices'] and value != '':
        return defer.fail(InvalidPipelineValue('Option "%s" not in list of choices' % value))
    else:
        return defer.succeed(value)

def t_integer(_state, value, params):
    """
    The range of values can be restricted through min and max
    """
    if value:
        try:
            int(value)
        except ValueError:
            return defer.fail(InvalidPipelineValue('"%s" is not an integer' % str(value)))

        intValue = int(value)
        
        if 'max' in params and intValue > params['max'] or 'min' in params and intValue < params['min']:
            return defer.fail(InvalidPipelineValue('%d is outside the valid range' % intValue))
        else:
            return defer.succeed(value)
    else:
        return defer.succeed(value)
    
def t_float(_state, value, params):
    """
    Like integer, the range can be restricted by min and max
    """
    if value:
        try:
            float(value)
        except ValueError:
            return defer.fail(InvalidPipelineValue('"%s" is not a float' % str(value)))

        floatValue = float(value)
    
        if 'max' in params and floatValue > params['max'] or 'min' in params and floatValue < params['min']:
            return defer.fail(InvalidPipelineValue('%f is outside the valid range' % floatValue))
        else:
            return defer.succeed(value)
    else:
        return defer.succeed(value)
    
def t_boolean(_state, value, params):
    """
    Mappings can be provided for what true/false should be transformed into via 'true', and 'false'
    """
    if value.lower() not in ['true', 'false']:
        return defer.fail(InvalidPipelineValue('"%s" is not a valid boolean, must be true or false' % str(value)))

    # Transform it to a new value if there is a mapping otherwise
    # return the its value
    return defer.succeed(str(params.get(value.lower(), value)))

def t_dataset(state, value, params):
    """
    Incomplete
    """
    if value:
        tagPath = os.path.join(state.machineconf('dirs.tag_dir'), value)
        if os.path.exists(tagPath):
            # very cheap right now, move along nothing to see here
            tagMetadata = json.loads(open(tagPath + '.metadata').read())
            if 'urls' not in tagMetadata or ('urls' in tagMetadata and tagMetadata.get('urls_realized')):
                if params.get('transform_type') == 'prefix':
                    # tagToRefDBPath basically does what prefix does
                    return defer.succeed(ptu.tagToRefDBPath(tagPath))
                elif params.get('transform_type') == 'directory':
                    commonPrefix = ptu.tagToRefDBPath(tagPath)
                    if os.path.isdir(commonPrefix):
                        return defer.succeed(commonPrefix)
                    else:
                        return defer.succeed(os.path.dirname(commonPrefix))
                elif params.get('transform_type') == 'tag_base_dir':
                    return defer.succeed(tagMetadata['tag_base_dir'])
                else:
                    return defer.succeed(tagPath)
            else:
                return defer.succeed('undefined')
        elif os.path.exists(tagPath + '.phantom'):
            return defer.succeed('undefined')
        else:
            return defer.fail(InvalidPipelineValue('"%s" is not a valid tag' % str(value)))
    else:
        return defer.succeed('')

t_paired_dataset = t_dataset

t_singleton_dataset = t_dataset

def t_blastdb_dataset(state, value, _params):
    """
    Incomplete
    """
    if value:
        tagPath = os.path.join(state.machineconf('dirs.tag_dir'), value)
        if os.path.exists(tagPath):
            # very cheap right now, move along nothing to see here
            tagMetadata = json.loads(open(tagPath + '.metadata').read())
            if 'urls' not in tagMetadata or ('urls' in tagMetadata and tagMetadata.get('urls_realized')):            
                return defer.succeed(ptu.tagToRefDBPath(tagPath))
            else:
                return defer.succeed('undefined')
        elif os.path.exists(tagPath + '.phantom'):
            return defer.succeed('undefined')
        else:
            return defer.fail(InvalidPipelineValue('"%s" is not a valid blastdb path' % str(value)))
    else:
        return defer.succeed('')

def t_organism(_state, value, params):
    """
    Organism simply must be 2 words
    """
    if len(value.split()) >= 2:
        return defer.succeed(value)
    else:
        return defer.fail(InvalidPipelineValue('"%s" must be two words' % str(value)))

def t_insert_size(_state, value, params):
    """
    Insert size must be 2 integers
    """
    spl = value.split()
    if len(spl) != 2:
        return defer.fail(InvalidPipelineValue('"%s" must be two integers seperated by a white space' % str(value)))

    try:
        return defer.succeed('%d %d' % (int(spl[0]), int(spl[1])))
    except ValueError:
        return defer.fail(InvalidPipelineValue('"%s" must be two integers separated by a white space' % str(value)))

@defer.inlineCallbacks
def t_credential(state, value, _params):
    """
    Ensure a credential exists
    """
    credClient = cred_client.CredentialClient(value,
                                              state.mq,
                                              state.conf)

    try:
        yield credClient.listInstances()
        defer.returnValue(value)
    except Exception:
        raise InvalidPipelineValue('"%s" is not a valid credential' % str(value))

def t_random_pipeline_name(_state, value, params):
    """
    Simply returns a pipeline name, if there already is one
    it returns that, otherwise a random one is created
    """
    if not value:
        return defer.succeed('pipeline_' + str(time.time()))
    else:
        return defer.succeed(value)


@defer.inlineCallbacks
def m_list(state, typCallback, value, params):
    values = [v.strip() for v in value.split(params.get('delimiter', ','))]
    values = yield defer.DeferredList(map(lambda v : typCallback(state, v, params),
                                          values))
    success = [v for s, v in values if s]
    failure = [f for s, f in values if not s]

    if failure:
        errorList = []
        for f in failure:
            try:
                f.raiseException()
            except InvalidPipelineValue, err:
                errorList.append(err)

        raise InvalidPipelineValueList(errorList)
    else:
        defer.returnValue(params.get('delimieter', ',').join([str(v) for v in success]))
        

# Maps type names to actual functions.  Most are the same
# but things like float are renamed so they don't interfere
# with the builtin type
TYPES = {'string': t_string,
         'restricted_string': t_restricted_string,
         'integer': t_integer,
         'float': t_float,
         'boolean': t_boolean,
         'dataset': t_dataset,
         'paired_dataset': t_paired_dataset,
         'singleton_dataset': t_singleton_dataset,
         'blastdb_dataset': t_blastdb_dataset,
         'organism': t_organism,
         'insert_size': t_insert_size,
         'credential': t_credential,
         'random_pipeline_name': t_random_pipeline_name,
         }

# Modifiers for types, these are given an extra parameter,
# a callback for the type this is modifing.  This callback can
# be called to validate the inner type.  For example if the type
# is `string list` then the `list` modifer will be called with the
# `string` callback.
TYPE_MODIFIERS = {'list': m_list}
