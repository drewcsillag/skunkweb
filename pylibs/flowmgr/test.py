# Time-stamp: <02/09/04 14:47:06 smulloni>
# $Id$

import parser as P
parser=P.FlowDefParser()
parser.parse(open('flowtest.xml').read())
f=parser.getFlowDef()
flow=f.flows[0]
state={'x' : 2}
def go(flow, state):
    stage=flow.evaluate(state)
    print "stage: %s; state: %s" % (getattr(stage, 'id', None), state)
    if stage:
        state[P.STAGE_MARKER]=stage.id
    return stage

while 1:
    stage=go(flow, state)
    if stage:
        print stage
    else:
        break
