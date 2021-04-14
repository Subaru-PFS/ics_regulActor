import time
from datetime import datetime as dt
from datetime import timedelta

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
        self.t0 = None

    @property
    def elapsedTime(self):
        try:
            delta = time.time() - self.t0
        except TypeError:
            delta = 0

        return round(delta)

    def start(self):
        self.actor.addModels([self.name])
        self.regulate(doRaise=True)
        QThread.start(self)

    def stop(self):
        self.t0 = None
        self.exit()

    def handleTimeout(self):
        xcuKeys = self.actor.models[self.name]
        try:
            [setpoint, reject, tip, power] = xcuKeys.keyVarDict['coolerTemps'].getValue()
        except ValueError:
            power = None

        if power is None or power < 70:
            self.actor.bcast.warn(f'text="Cooler power : {power}, turning control loop OFF')
            self.stop()

        if self.exitASAP:
            raise SystemExit()

        if self.elapsedTime > self.period:
            self.regulate()

    def regulate(self, doRaise=False):
        try:
            detector = self.detectorBox()
            tip = self.coolerTip()
            new_tip = tip + self.kp * (self.setpoint - detector)
            self.actor.safeCall(actor=self.name, cmdStr='cooler on setpoint=%.2f' % new_tip, timeLim=60)
            self.t0 = time.time()
        except Exception as e:
            if doRaise:
                raise
            else:
                self.actor.bcast.warn('text=%s' % self.actor.strTraceback(e))

    def getStatus(self):
        return f'{self.name},{self.isAlive()},{self.setpoint},{self.kp},{self.period},{self.elapsedTime}'

    def coolerTip(self):
        return self.getValue(f'{self.name}__coolertemps', 'tip')

    def detectorBox(self):
        return self.getValue(f'{self.name}__temps', 'val1_0')

    def extractData(self, table, cols, nbSec=None):
        nbSec = self.period / 2 if nbSec is None else nbSec
        db = DatabaseManager()
        now = dt.utcnow()
        past = now - timedelta(seconds=nbSec)
        df = db.dataBetween(table, cols, start=past.isoformat())
        db.close()
        return df

    def getValue(self, table, col, samplingTime=None, method=np.median, doFilter=True, vmin=70, vmax=200):
        df = self.extractData(table, col, samplingTime)
        fdf = df.dropna().query(f'{vmin}<{col}<{vmax}') if doFilter else df

        if len(fdf) < 10:
            self.stop()
            raise ValueError(f'{table}({col}) data contain only {len(fdf)} samples, stopping control loop ...')

        return method(fdf[col])
