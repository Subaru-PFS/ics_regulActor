import time
from datetime import datetime as dt

import numpy as np
from actorcore.QThread import QThread
from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager
from sps_engineering_Lib_dataQuery.dates import date2astro


class TempLoop(QThread):
    def __init__(self, actor, xcuActor, setpoint, period, kp):
        QThread.__init__(self, actor, xcuActor, timeout=15.0)
        self.setpoint = setpoint
        self.period = period
        self.kp = kp

        self.t0 = 0
        self.handleTimeout = self.manageLoop
        self.start()

    @property
    def loopOn(self):
        return not self.exitASAP

    @property
    def elapsedTime(self):
        return time.time() - self.t0

    def startLoop(self, setpoint, period, kp):
        self.setpoint = setpoint
        self.period = period
        self.kp = kp
        self.regulate()

    def stopLoop(self):
        self.exitASAP = True

    def manageLoop(self):
        xcuKeys = self.actor.models[self.name]
        try:
            [setpoint, reject, tip, power] = xcuKeys.keyVarDict['coolerTemps'].getValue()
        except ValueError:
            power = None

        if power is None or power < 70:
            self.actor.bcast.warn(f'text="Cooler power : {power}, turning control loop OFF')
            self.stopLoop()

        if self.exitASAP:
            raise SystemExit()

        if self.elapsedTime > self.period:
            self.regulate()

    def regulate(self):
        try:
            detector = self.detectorBox()
            tip = self.coolerTip()
            new_tip = tip + self.kp * (self.setpoint - detector)
            self.actor.safeCall(actor=self.name, cmdStr='cooler on setpoint=%.2f' % new_tip, timeLim=60)
            self.t0 = time.time()
        except Exception as e:
            self.actor.bcast.warn('text=%s' % self.actor.strTraceback(e))

    def getStatus(self):
        return '%s,%s,%.2f,%.2f,%.2f,%.2f' % (self.name, self.loopOn, self.setpoint,
                                              self.kp, self.period, self.elapsedTime)

    def coolerTip(self, nbSec=1800, method=np.median):
        df = self.getData('%s__coolertemps' % self.name, 'tip', nbSec=nbSec)
        return self.getOneValue(df, col='tip', nbSec=nbSec, method=method)

    def detectorBox(self, nbSec=1800, method=np.median):
        df = self.getData('%s__temps' % self.name, 'val1_0', nbSec=nbSec)
        return self.getOneValue(df, col='val1_0', nbSec=nbSec, method=method)

    def getData(self, table, cols, nbSec):
        db = DatabaseManager()
        tai = date2astro(dt.utcnow())
        where = 'WHERE (tai >= %f and tai < %f)' % (tai - nbSec, tai)
        order = 'order by raw_id asc'
        db.close()
        return db.pfsdata(table, cols, where=where, order=order)

    def getOneValue(self, df, col, nbSec, method):
        vmin, vmax = 50, 300
        fdf = df.dropna().query(f'{vmin}<{col}<{vmax}')

        if len(fdf) < (nbSec / 60):
            self.stopLoop()
            raise ValueError('No Data')

        return method(fdf[col])
