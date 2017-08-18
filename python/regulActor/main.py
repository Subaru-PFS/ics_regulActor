#!/usr/bin/env python

from datetime import datetime as dt

from actorcore.Actor import Actor
from actorcore.QThread import QThread
from regulActor.utils import getMean


class RegulActor(Actor):
    def __init__(self, name, productName=None, configFile=None, debugLevel=30):
        # This sets up the connections to/from the hub, the logger, and the twisted reactor.
        #
        self.cu = "r0"
        Actor.__init__(self, name,
                       productName=productName,
                       configFile=configFile, modelNames=['xcu_%s' % self.cu])

        self.allThreads = {}
        self.t0 = dt.now()
        self.period = 600
        self.kp = 1.
        self.setpoint = None
        self.loopOn = False
        controlLoop = QThread(self, "controlLoop")
        controlLoop.handleTimeout = self.manageLoop
        self.allThreads["controlLoop"] = controlLoop
        controlLoop.start()

    def startLoop(self, setpoint, period, kp):
        self.setpoint = setpoint
        self.period = period
        self.kp = kp
        self.loopOn = True
        self.regulCooler()

    def stopLoop(self):
        self.loopOn = False

    def manageLoop(self):
        xcuKeys = self.actor.models['xcu_%s' % self.cu]
        [setpoint, reject, tip, power] = xcuKeys.keyVarDict['coolerTemps'].getValue()
        if (dt.now() - self.t0).total_seconds() > self.period and self.loopOn:
            self.regulCooler()

    def regulCooler(self):
        self.t0 = dt.now()
        detector = getMean("xcu_%s__temps" % self.cu, "val1_0")
        tip = getMean("xcu_%s__coolertemps" % self.cu, "tip")
        new_tip = tip + self.kp * (self.setpoint - detector)

        self.safeCall(actor='xcu_%s' % self.cu, cmdStr="cooler on setpoint=%.2f" % new_tip, timeLim=60)

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
