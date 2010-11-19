#
# This receives tasklet work to do, creates any task information and then
# fires off the tasklet work in the background and waits for the result
import json

from vappio_tx.mq import client




def handleMsg(msg):
    request = json.loads(msg.body)
    

def makeService(conf):
    mqService = client.makeService(conf)
    mqService.mqFactory.subscribe(handleMsg, conf('tasklets.queue'), {'prefecth': int(conf('tasklets.concurrent_tasks'))})
    return mqService
    
