#!/usr/bin/env python

from actorcore.Actor import Actor
from regulActor.temploop import TempLoop


class RegulActor(Actor):
    def __init__(self, name, productName=None, configFile=None, debugLevel=30):
        # This sets up the connections to/from the hub, the logger, and the twisted reactor.
        #
        Actor.__init__(self, name,
                       productName=productName,
                       configFile=configFile)

        self.loops = {}

    def startLoop(self, xcuActor, setpoint, period, kp):
        try:
            self.loops[xcuActor].stop()
        except KeyError:
            pass

        self.loops[xcuActor] = TempLoop(self, xcuActor, setpoint, period, kp)
        self.loops[xcuActor].start()

    def stopLoop(self, xcuActor):
        self.loops[xcuActor].stop()
        self.loops.pop(xcuActor, None)

    def status(self, cmd):
        for i, (xcuActor, looptemp) in enumerate(self.loops.items()):
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
