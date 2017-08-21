#!/usr/bin/env python

import opscore.protocols.keys as keys
import opscore.protocols.types as types


class RegulCmd(object):
    def __init__(self, actor):
        # This lets us access the rest of the actor.
        self.actor = actor

        # Declare the commands we implement. When the actor is started
        # these are registered with the parser, which will call the
        # associated methods when matched. The callbacks will be
        # passed a single argument, the parsed and typed command.
        #
        self.vocab = [
            ('ping', '', self.ping),
            ('status', '', self.status),
            ('start', '@(r0|r1) <setpoint> [<period>] [kp]', self.startLoop),
            ('stop', '@(r0|r1)', self.stopLoop),

        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary("regul_regul", (1, 1),
                                        keys.Key("setpoint", types.Float(), help="Detector temperature setpoint"),
                                        keys.Key("period", types.Float(), help="control loop period"),
                                        keys.Key("kp", types.Float(), help="control loop coefficient"),
                                        )

    def ping(self, cmd):
        """Query the actor for liveness/happiness."""
        cmd.finish("text='Present and (probably) well'")

    def status(self, cmd):
        """Report status and version; obtain and send current data"""

        self.actor.status(cmd)
        cmd.finish()

    def startLoop(self, cmd):
        cmdKeys = cmd.cmd.keywords
        setpoint = cmdKeys['setpoint'].values[0]
        period = cmdKeys['period'].values[0] if 'period' in cmdKeys else 600
        kp = cmdKeys['kp'].values[0] if 'kp' in cmdKeys else 1.

        if not 140 <= setpoint < 160:
            raise Exception("valueError 140 <= setpoint < 160")
        if not 30 <= period < 7200:
            raise Exception("valueError 30 <= period < 7200")
        if not 0.5 <= kp < 5:
            raise Exception("valueError 0.5 <= kp < 5")

        if "r0" in cmdKeys:
            xcu = "xcu_r0"
        elif "r1" in cmdKeys:
            xcu = "xcu_r1"
        else:
            xcu = None
        self.actor.startLoop(xcu, setpoint, period, kp)
        cmd.finish("text='Detector %s temperature control loop On'" % xcu)

    def stopLoop(self, cmd):
        cmdKeys = cmd.cmd.keywords
        if "r0" in cmdKeys:
            xcu = "xcu_r0"
        elif "r1" in cmdKeys:
            xcu = "xcu_r1"
        else:
            xcu = None
        self.actor.stopLoop(xcu)
        cmd.finish("text='Detector %s temperature control loop Off'" % xcu)
