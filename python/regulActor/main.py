#!/usr/bin/env python

from actorcore.Actor import Actor
from regulActor.temploop import TempLoop


class RegulActor(Actor):
    def __init__(self, name, productName=None, configFile=None, debugLevel=30):
        # This sets up the connections to/from the hub, the logger, and the twisted reactor.
        #
        Actor.__init__(self, name,
                       productName=productName,
                       configFile=configFile, modelNames=['xcu_r0',
                                                          'xcu_r1',
                                                          ])

        self.threads = {}

    def startLoop(self, xcu, setpoint, period, kp):
        temploop = self.threads[xcu] if xcu in self.threads.iterkeys() else TempLoop(self, xcu)
        temploop.startLoop(setpoint, period, kp)
        self.threads[xcu] = temploop

    def stopLoop(self, xcu):
        temploop = self.threads[xcu] if xcu in self.threads.iterkeys() else TempLoop(self, xcu)
        temploop.stopLoop()
        self.threads[xcu] = temploop

    def status(self, cmd):
        for i, (xcu, looptemp) in enumerate(self.threads.iteritems()):
            cmd.inform('loopTemp%i=%s' % (i, looptemp.getStatus()))

    def safeCall(self, **kwargs):
        cmd = self.bcast
        cmdVar = self.cmdr.call(**kwargs)

        status = cmdVar.lastReply.canonical().split(" ", 4)[-1]

        if cmdVar.didFail:
            cmd.warn(status)


def main():
    actor = RegulActor('regul', productName='regulActor')
    actor.run()


if __name__ == '__main__':
    main()
