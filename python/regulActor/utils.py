import traceback as tb
from functools import partial

import numpy as np
import psycopg2
from matplotlib.dates import date2num


def threaded(func):
    def wrapper(self, *args, **kwargs):
        self.actor.allThreads[self.name].putMsg(partial(func, self, *args, **kwargs))

    return wrapper


def formatException(e, traceback):
    """ Format the caught exception as a string

    :param e: caught exception
    :param traceback: exception traceback
    """

    def clean(string):
        return str(string).replace("'", "").replace('"', "")

    return "%s %s %s" % (clean(type(e)), clean(type(e)(*e.args)), clean(tb.format_tb(traceback, limit=1)[0]))


import datetime as dt


def convertTimetoAstro():
    offset = 50000 - date2num(dt.datetime(1995, 10, 10))
    return (date2num(dt.datetime.now()) + offset) * 86400


def getMean(tableName, keyword):
    prop = "dbname='%s' user='pfs' host='%s' port='%i'" % ("archiver", "10.1.1.1", 5432)
    conn = psycopg2.connect(prop)
    database = conn.cursor()

    datenum = convertTimetoAstro()
    nb_sec = 1800
    request = """select %s from reply_raw inner join %s on %s.raw_id=reply_raw.id WHERE (tai >= %f and tai < %f) order by raw_id asc""" % (
        keyword, tableName, tableName, datenum - nb_sec, datenum)
    database.execute(request)
    res = np.array(database.fetchall())
    if len(res) > 0:
        return np.mean(res)
    else:
        raise Exception("No Data")


class CmdSeq(object):
    def __init__(self, actor, cmdStr, timeLim=60, doRetry=False, tempo=1.0):
        object.__init__(self)
        self.actor = actor
        self.cmdStr = cmdStr
        self.timeLim = timeLim
        self.doRetry = doRetry
        self.tempo = tempo

    def build(self, cmd):
        return {"actor": self.actor,
                "cmdStr": self.cmdStr,
                "forUserCmd": cmd,
                "timeLim": self.timeLim,
                "doRetry": self.doRetry,
                }
