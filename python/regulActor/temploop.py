import time
from datetime import datetime as dt

import numpy as np
from actorcore.QThread import QThread
from sps_engineering_Lib_dataQuery.databasemanager import DatabaseManager
from sps_engineering_Lib_dataQuery.dates import date2astro


class TempLoop(QThread):
    def __init__(self, actor, xcuActor):
        QThread.__init__(self, actor, xcuActor)
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

    @property
    def cam(self):
        __, cam = self.name.split('_')
        return cam

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
        detector = self.ccdTemps()
        tip = self.coolerTip()
        new_tip = tip + self.kp * (self.setpoint - detector)

        print(dict(actor=self.name, cmdStr="cooler on setpoint=%.2f" % new_tip, timeLim=60))

        #self.actor.safeCall(actor=self.name, cmdStr="cooler on setpoint=%.2f" % new_tip, timeLim=60)

    def getStatus(self):
        return "%s,%s,%.2f,%.2f,%.2f,%.2f" % (self.name, self.loopOn, self.setpoint,
                                              self.kp, self.period, self.elapsedTime)

    def ccdTemps(self, nbSec=1800, method=np.median):
        df = self.getData('ccd_%s__ccdtemps' % self.cam, 'ccd0,ccd1', nbSec=nbSec)
        df['ccd'] = (df['ccd0'] + df['ccd1']) / 2
        return self.getOneValue(df, col='ccd', nbSec=nbSec, method=method)

    def coolerTip(self, nbSec=1800, method=np.median):
        df = self.getData("%s__coolertemps" % self.name, "tip", nbSec=nbSec)
        return self.getOneValue(df, col='tip', nbSec=nbSec, method=method)

    def getData(self, table, cols, nbSec):
        db = DatabaseManager('tron', 5432, '')
        db.init()
        tai = date2astro(dt.utcnow())
        where = 'WHERE (tai >= %f and tai < %f)' % (tai - nbSec, tai)
        order = 'order by raw_id asc'
        db.close()
        return db.pfsdata(table, cols, where=where, order=order)

    def getOneValue(self, df, col, nbSec, method):
        fdf = df.dropna().query('50<%s<300' % col)

        if len(fdf) < (nbSec / 60):
            self.stopLoop()
            raise Exception("No Data")

        return method(fdf[col])
