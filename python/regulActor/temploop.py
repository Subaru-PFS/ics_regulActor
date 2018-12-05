import time
from datetime import datetime as dt

import numpy as np
from actorcore.QThread import QThread
from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager
from sps_engineering_Lib_dataQuery.dates import date2astro


class TempLoop(QThread):
    def __init__(self, actor, xcu):
        QThread.__init__(self, actor, xcu)
        self.setpoint = 151
        self.period = 3600
        self.kp = 1
        self.loopOn = False
        self.t0 = time.time()
        self.handleTimeout = self.manageLoop
        self.start()

    @property
    def elapsedTime(self):
        return time.time() - self.t0

    def startLoop(self, setpoint, period, kp):
        self.setpoint = setpoint
        self.period = period
        self.kp = kp
        self.loopOn = True
        self.regulate()

    def stopLoop(self):
        self.loopOn = False

    def manageLoop(self):
        xcuKeys = self.actor.models[self.name]
        [setpoint, reject, tip, power] = xcuKeys.keyVarDict['coolerTemps'].getValue()
        if power < 70:
            self.stopLoop()
        if self.elapsedTime > self.period and self.loopOn:
            self.regulate()

    def regulate(self):
        self.t0 = time.time()
        detector = self.getData("%s__temps" % self.name, "val1_0")
        tip = self.getData("%s__coolertemps" % self.name, "tip")
        new_tip = tip + self.kp * (self.setpoint - detector)

        self.actor.safeCall(actor=self.name, cmdStr="cooler on setpoint=%.2f" % new_tip, timeLim=60)

    def getStatus(self):
        return "%s,%s,%.2f,%.2f,%.2f,%.2f" % (self.name, self.loopOn, self.setpoint,
                                              self.kp, self.period, self.elapsedTime)

    def getData(self, table, col, nbSec=1800, method=np.median):
        db = DatabaseManager('tron', 5432, '')
        db.init()
        tai = date2astro(dt.utcnow())
        where = 'WHERE (tai >= %f and tai < %f)' % (tai - nbSec, tai)
        order = 'order by raw_id asc'
        df = db.pfsdata(table, col, where=where, order=order)
        fdf = df.dropna().query('50<%s<300' % col)
        db.close()
        if len(fdf) < (nbSec / 60):
            self.stopLoop()
            raise Exception("No Data")

        return method(fdf[col])
