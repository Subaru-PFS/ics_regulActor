#!/usr/bin/env python

from actorcore.Actor import Actor
from regulActor.temploop import TempLoop


class RegulActor(Actor):
    def __init__(self, name, productName=None, configFile=None, debugLevel=30):
        # This sets up the connections to/from the hub, the logger, and the twisted reactor.
        #
        cams = ['b1', 'r1']
        Actor.__init__(self, name,
                       productName=productName,
                       configFile=configFile, modelNames=['xcu_%s' % cam for cam in cams])

        self.threads = {}

    def startLoop(self, xcuActor, setpoint, period, kp):
        try:
            self.threads[xcuActor].stopLoop()
        except KeyError:
            pass

        self.threads[xcuActor] = TempLoop(self, xcuActor, setpoint, period, kp)

    def stopLoop(self, xcuActor):
        self.threads[xcuActor].stopLoop()
        self.threads.pop(xcuActor, None)

    def status(self, cmd):
        for i, (xcuActor, looptemp) in enumerate(self.threads.items()):
            cmd.inform('loopTemp%i=%s' % (i, looptemp.getStatus()))

    def safeCall(self, **kwargs):
        cmdVar = self.cmdr.call(**kwargs)

        if cmdVar.didFail:
            reply = cmdVar.replyList[-1]
            raise UserWarning("actor=%s %s" % (reply.header.actor,
                                               reply.keywords.canonical(delimiter=';')))


def main():
    actor = RegulActor('regul', productName='regulActor')
    actor.run()


if __name__ == '__main__':
    main()
