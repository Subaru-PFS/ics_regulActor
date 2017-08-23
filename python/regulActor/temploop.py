from datetime import datetime as dt

import numpy as np
import psycopg2
from actorcore.QThread import QThread
from matplotlib.dates import date2num


class TempLoop(QThread):
    def __init__(self, actor, xcu):
        QThread.__init__(self, actor, xcu)
        self.setpoint = 151
        self.period = 3600
        self.kp = 1
        self.loopOn = False
        self.t0 = dt.now()
        self.handleTimeout = self.manageLoop
        self.start()

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
        if (dt.now() - self.t0).total_seconds() > self.period and self.loopOn:
            self.regulate()

    def regulate(self):
        self.t0 = dt.now()
        detector = self.getData("%s__temps" % self.name, "val1_0")
        tip = self.getData("%s__coolertemps" % self.name, "tip")
        new_tip = tip + self.kp * (self.setpoint - detector)

        self.actor.safeCall(actor=self.name, cmdStr="cooler on setpoint=%.2f" % new_tip, timeLim=60)

    def getStatus(self):
        return "%s,%s,%.2f,%.2f,%.2f,%.2f" % (self.name, self.loopOn, self.setpoint, self.kp,
                                              self.period, (dt.now() - self.t0).total_seconds())

    def convertTimetoAstro(self):
        offset = 50000 - date2num(dt(1995, 10, 10))
        return (date2num(dt.now()) + offset) * 86400

    def getData(self, tableName, keyword, nb_sec=1800, method=np.mean):
        prop = "dbname='%s' user='pfs' host='%s' port='%i'" % ("archiver", "10.1.1.1", 5432)
        conn = psycopg2.connect(prop)
        database = conn.cursor()

        datenum = self.convertTimetoAstro()
        request = """select %s from reply_raw inner join %s on %s.raw_id=reply_raw.id WHERE (tai >= %f and tai < %f) order by raw_id asc""" % (
            keyword, tableName, tableName, datenum - nb_sec, datenum)
        database.execute(request)
        res = np.array(database.fetchall())
        if len(res) > nb_sec / 60:
            return method(res)
        else:
            self.stopLoop()
            raise Exception("No Data")
