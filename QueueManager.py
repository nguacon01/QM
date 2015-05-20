#!/usr/bin/env python
# encoding: utf-8
"""

mini QueueManager

Created by Marc-Andre' on 2015-4-14 loosely inspired from an early version 2009.

organized around 3 folders

QM_qJobs    queuing jobs
QM_Jobs     running jobs
QM_dJobs    done jobs

jobs are folders, they contain all the need information to run code.
Minimum job is
    - a info file, either in xml or cfg format (defined in QMserv.cfg)
    - a script to launch
but you can put in there everything you need (data, code, etc...)

The info file should contain :

typical xml is:
<PARAMETER>
    <nb_proc value="12"/>
    <e-mail value="me@gmail.com"/>
    <script value="python process.py param1 param2"/>
    <info value="some description of the job"/>
</PARAMETER>

typical cfg is:
[QMOptions]
nb_proc : 12
e_mail : me@gmail.com
info : some description of the job
script : python process.py param1 param2

The only required entry is script
You can use this file for your own entries


pool QM_qJobs and launch associated prgm
prgm runs inside the job folder, which may contain any associated files

Queue Manager itself is parametrized with QMserv.cfg file
(as well as the associated WEB_QMserver.py which allows to monitor what is going on)

This code is Licenced under the Cecill licence code
"""

import os
import os.path as op
import subprocess
import time
import sys
import glob

import logging
from ConfigParser import SafeConfigParser
from xml.sax import handler, make_parser
from datetime import datetime, timedelta

__version__ = 0.1

def start_logger():
    "configurate and start logger"
    global logger
    # create logger
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s", filename="QueueManager.log", filemode="w")
    #limit size, and add rotate
#    logger.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1024, backupCount=10)

class XmlInfo(handler.ContentHandler):
    "used to parse infos.xml files"
    def __init__(self, job, keylist):
        self.job = job
        self.keylist = keylist
    def startElement(self, name, attrs):
        if name in self.keylist:
            value = attrs.get("value")
            setattr(self.job, name, value)
# class job(object):
#     """
#     class that handles one job
#     """
#     def __init__(self, path, name):
#         "creates one empty jobs with located in path"
#     def run(self):
#         os.system(self.script)
# 
class Job(object):
    """this class holds every thing to describe a job"""
    job_type = None  # these entries will be overwriten at start-up
    job_file = None
    def __init__(self, loc, name):
        self.loc = loc      # QM_xJobs
        self.name = name    # the job directory name
        self.date = os.stat(self.myjobfile) [8]   # will be used for sorting - myjobfile stronger than url
        self.nicedate = datetime.fromtimestamp(self.date).strftime("%d %b %Y %H:%M:%S")
        self.timestarted = time.time()
        # the following will be modified by parsexml
        self.nb_proc = 1
        self.e_mail = "unknown"
        self.info = "unknown"
        self.script = "unknown"
        self.priority = 0
        keylist = ["nb_proc", "e_mail", "info", "script", "priority"]  # adapt here
        self.keylist = keylist
        # and get them
        if self.job_type == "xml":
            self.parsexml()
        if self.job_type == "cfg":
            self.parsecfg()
    @property
    def url(self):
        return op.join(self.loc,self.name)
    @property
    def started(self):
        return self.nicedate
    @property
    def myjobfile(self):
        return op.join(self.loc, self.name, self.job_file)
    def parsecfg(self):
        """    load info.cfg files    """
        config = SafeConfigParser()
        config.readfp( open(self.myjobfile) )
        for k in self.keylist:
            if config.has_option("QMOptions", k):
                val = config.get("QMOptions", k)
                setattr(self, k, val)
    def parsexml(self):
        """    load info.xml files    """
        parser = make_parser()
        handle = XmlInfo(self, self.keylist)     # inject values inside current Job
        parser.setContentHandler(handle)
        parser.parse(self.myjobfile)
    @property
    def mylog(self):
        return op.join(self.loc, self.name, "process.log")
    @property
    def size(self):
        tt = "undefined"
        try:
            for line in open(self.myparam,'r').readlines():
                infos = line.split("=")
                if len(infos) >= 2 and infos[0] == "col_list":
                    col_list = eval(infos[1])
            tt = "%d"%len(col_list)
        except:
            pass
        return tt
    def avancement(self):
        """   analyse log file, return avancement as a string 0 ... 100   """
        import re
        av = 0.0
        try:
            for l in open(self.mylog,'r').readlines():
                print l
                m = re.match("\s+(\d+)\s*/\s*(\d+)",l)   ### Processing col 8154   5 / 32
                if m:  av = float(m.group(1))/float(m.group(2))
        except:
            pass
        print "avancement", av
        return "%.f"%(100.0*av)
    def time(self):
        """   analyse log file, return elapsed time as a string """
        import re
        tt = "- undefined -"
        try:
            for l in open(self.mylog, 'r').readlines():
                m = re.search("time:\s*(\d+)",l)   #
                if m:  tt = m.group(1)
        except:
            pass
        return tt
    def run(self):
        Script = self.script+">> process.log 2>&1"
        try:
            retcode = subprocess.call(Script, shell=True)
        except OSError, e:
            logging.error("Execution failed:"+ str(e))
            retcode = -1
        return retcode
    def __repr__(self):
        p = ["JOB  %s"%self.name]
        for k in ["nicedate", "nb_proc", "e_mail", "info", "script", "priority", "myjobfile"]:
            try:
                p.append("    %s : %s"%(k, getattr(self, k)) )
            except:
                pass
        return "\n".join(p)

def job_list(path, error, do_sort=True):
    " returns a list with all jobs in path"
    ll = []
    for i in os.listdir(path):
        if os.path.isdir(os.path.join(path,i)) :
            try:
                JJ = Job(path,i)
            except:
                msg = "Job invalid: "+os.path.join(path,i)
                logging.warning(msg)
                with open(os.path.join(path,i, "process.log"), "w") as F:
                    F.write(msg)
                
                os.rename(os.path.join(path,i), os.path.join(error,i) )
                logging.warning("Job %s moved to %s"%(os.path.join(path,i),error) )
            else:
                ll.append( JJ )
    if do_sort:
        ll.sort(reverse=True, key=lambda j: j.date)   # sort by reversed date
    return ll

class QM(object):
    """
    class that deals with all incoming jobs
    It calls sequentially scout that waits for new jobs in the queue
    Then it verifies that no other NPK Job is running
    and it launches the new job
    
    everything is maintained in a self.joblist lists - top job is the first to be run
    """
    def __init__(self, configfile):
        logging.info("QueueManager Initialization")
        # read config
        self.configfile = configfile
        self.config = SafeConfigParser()
        self.config.readfp(open(configfile))
        self.QM_FOLDER = self.config.get("QMServer", "QM_FOLDER")
        self.MaxNbProcessors = self.config.get("QMServer", "MaxNbProcessors")
        self.job_file = self.config.get("QMServer", "job_file")
        if self.job_file.endswith('.xml'):
            self.job_type = 'xml'
        elif self.job_file.endswith('.cfg'):
            self.job_type = 'cfg'
        else:
            raise Exception("job_file should be either .xml or .cfg")
        self.mailactive = self.config.getboolean("QMServer", "MailActive")
        Job.job_file = self.job_file    # inject into Job class
        Job.job_type = self.job_type
        self.ROOT = self.QM_FOLDER
        self.debug = self.config.getboolean( "QMServer", "Debug")
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        self.qJobs = op.join(self.QM_FOLDER,"QM_qJobs")
        self.Jobs = op.join(self.QM_FOLDER,"QM_Jobs")
        self.dJobs = op.join(self.QM_FOLDER,"QM_dJobs")
        self.queue_jobs = []
        self.nap_time = 1.0

    def run(self):
        "the way to start to QM endless loop"
        while True :
            next_one = self.wait_for_job()
            self.run_job(next_one)
    def nap(self):
        "waiting method for spooling"
        time.sleep(self.nap_time)
    def wait_for_job(self):
        """
        method that waits for something to show up in QM_qJobs folder
        and returns an ordered list of present jobs.
        oldest (most prio) first
        """
        self.queue_jobs = []
        while len(self.queue_jobs) == 0:
            self.queue_jobs = job_list(self.qJobs, self.dJobs)
            self.nap()
        next_job = self.queue_jobs.pop()
        return next_job

    def run_job(self, job):
        """
        method that deals with moving job to do around and running  job.script 
        maybe also send e-mail once the job is done ... 
        """
        logging.info("Starting %s\n%s"%(job.name,repr(job)) )
        to_qJobs = op.join(self.qJobs, job.name)
        to_Jobs = op.join(self.Jobs, job.name)
        to_dJobs = op.join(self.dJobs, job.name)
        
        os.rename(to_qJobs, to_Jobs)
        job.loc = self.Jobs
        os.chdir(to_Jobs)
        if job.script == "unknown":
            job.script = 'echo no-script; pwd; sleep 10; ls -l'
            logging.warning("undefined script in info file")
        if int(job.nb_proc) > int(self.MaxNbProcessors):
            msg = "Nb of processors limited to %d"%int(self.MaxNbProcessors)
            logging.warning( msg )
            with open("process.log","w") as F:
                F.write(msg)
            job.nb_proc = self.MaxNbProcessors
        os.putenv("NB_PROC", str(job.nb_proc))
        job.run()
        os.chdir(self.qJobs)
        os.rename(to_Jobs, to_dJobs)
        if self.mailactive:
            address = job.e_mail
            subject = "QM Job - %s - finished"%job.name
            to_mail = """
The job named - {0} - started on QueueManager is finished

Info : {4}

The processing took :      {1}
Result can be found here : {2}
QueueManager host is :     {3}

Virtually yours,

The QueueManager
""".format(job.name, job.time(), to_dJobs, os.uname()[1], job.info )
            try:
                mail(address, subject, to_mail )
            except:
                logging.error("Mail to %s could not be sent"%address)
        logging.info( "Job Finished")

if  __name__ == '__main__':
    start_logger()
    q =  QM("QMserv.cfg")
    if q.mailactive:
        try:
            from spike.util.sendgmail import mail    # if spike available
        except ImportError:
            from sendgmail import mail               # otherwise, copy it here
            logging.warning( "Using local version of sendgmail.mail")
    queue_jobs = job_list(q.qJobs, q.dJobs)
    # print listing
    if q.debug:
        logging.debug( "Dump of queue at start-up" )
        while queue_jobs:
            logging.debug( repr(queue_jobs.pop()) )
    # then loop for ever
    q.run()
