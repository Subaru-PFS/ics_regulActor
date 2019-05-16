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
            ('start', '<cam> <setpoint> [<period>] [<kp>]', self.startLoop),
            ('stop', '<cam>', self.stopLoop),

        ]

        # Define typed command arguments for the above commands.
        self.keys = keys.KeysDictionary('regul_regul', (1, 1),
                                        keys.Key('setpoint', types.Float(), help='Detector temperature setpoint'),
                                        keys.Key('period', types.Float(), help='control loop period'),
                                        keys.Key('kp', types.Float(), help='control loop coefficient'),
                                        keys.Key('cam', types.String(), help='single camera to regulate'),
                                        )

    def ping(self, cmd):
        """Query the actor for liveness/happiness."""
        cmd.finish('text="Present and (probably) well"')

    def status(self, cmd):
        """Report status and version; obtain and send current data"""

        self.actor.status(cmd)
        cmd.finish()

    def startLoop(self, cmd):
        cmdKeys = cmd.cmd.keywords
        setpoint = cmdKeys['setpoint'].values[0]
        period = cmdKeys['period'].values[0] if 'period' in cmdKeys else 3600
        kp = cmdKeys['kp'].values[0] if 'kp' in cmdKeys else 1.

        if not 130 <= setpoint < 200:
            raise ValueError('130 <= setpoint < 200')
        if not 1800 <= period < 7200:
            raise ValueError('1800 <= period < 7200')
        if not 0.2 <= kp < 5:
            raise ValueError('0.2 <= kp < 5')

        cam = cmdKeys['cam'].values[0]

        self.actor.startLoop('xcu_%s' % cam, setpoint, period, kp)
        self.actor.status(cmd)

        cmd.finish('text="Detector %s temperature control loop On"' % cam)

    def stopLoop(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        self.actor.stopLoop('xcu_%s' % cam)
        self.actor.status(cmd)

        cmd.finish('text="Detector %s temperature control loop Off"' % cam)
