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
                                        keys.Key('period', types.Float(), help='control loop period (hours)'),
                                        keys.Key('kp', types.Float(), help='control loop coefficient'),
                                        keys.Key('cam', types.String(), help='single camera to regulate'),
                                        )

    def ping(self, cmd):
        """Query the actor for liveness/happiness."""
        cmd.finish('text="Present and (probably) well"')

    def status(self, cmd):
        """Report status and version; obtain and send current data"""
        self.actor.sendVersionKey(cmd)
        self.actor.status(cmd)
        cmd.finish()

    def startLoop(self, cmd):
        spmin, spmax = 150, 170
        pmin, pmax = 8, 12
        kmin, kmax = 1, 2
        cmdKeys = cmd.cmd.keywords
        setpoint = cmdKeys['setpoint'].values[0]
        period = cmdKeys['period'].values[0] if 'period' in cmdKeys else 8
        kp = cmdKeys['kp'].values[0] if 'kp' in cmdKeys else 1.1

        if not spmin <= setpoint < spmax:
            raise ValueError(f'{spmin} <= setpoint < {spmax}')
        if not 8 <= period < 12:
            raise ValueError(f'{pmin} <= period (hours) < {pmax}')
        if not 1 <= kp < 2.2:
            raise ValueError(f'{kmin} <= kp < {kmax}')

        cam = cmdKeys['cam'].values[0]

        self.actor.startLoop('xcu_%s' % cam, setpoint, period * 3600, kp)
        self.actor.status(cmd)

        cmd.finish('text="Detector %s temperature control loop On"' % cam)

    def stopLoop(self, cmd):
        cmdKeys = cmd.cmd.keywords
        cam = cmdKeys['cam'].values[0]
        self.actor.stopLoop('xcu_%s' % cam)
        self.actor.status(cmd)

        cmd.finish('text="Detector %s temperature control loop Off"' % cam)
