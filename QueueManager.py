#!/usr/bin/env python
# encoding: utf-8
"""

mini QueueManager

Created by Marc-Andre' on 2015-4-14 loosely inspired from an early version 2009.

organized around 3 folders

QM_qJobs    queuing jobs
QM_Jobs     running jobs
QM_dJobs    done jobs

jobs are a folder containing a infos.xml file and all related information

minimal infos.xml is :
<PARAMETER>
    <NbProcessors value="12"/>
    <E-mail value="me@gmail.com"/>
    <Script value="python process.py param1 param2"/>
</PARAMETER>

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
import sys, string
import glob

import logging
from ConfigParser import SafeConfigParser
from xml.sax import handler, make_parser
from datetime import datetime, timedelta


__version__ = 0.1
class param(object):
    "This class is a generic holder for parameters"
    def report(self):
        "print a formatted report"
        print "------------ processing parameters ------------------"
        for i in dir(self):
            if not i.startswith('_'):
                v = getattr(self,i)
                if not callable(v):
                    print i, ' :', v
        print "-----------------------------------------------------"

class AnalInfo(handler.ContentHandler):
    "used to parse infos.xml files"
    def __init__(self, job, keylist):
        self.job = job
        self.keylist = keylist
    def startElement(self, name, attrs):
        if name in self.keylist:
            value = attrs.get("value")
            setattr(self.job, name, value)
class job(object):
    """
    class that handles one job
    """
    def __init__(self, path):
        "creates one empty jobs with located in path"
    def run(self):
        os.system(self.script)

class Job(object):
    """this class holds every thing to describe a job"""
    def __init__(self, loc, name):
        self.loc = loc      # QM_xJobs
        self.name = name    # the job directory name
        self.date = os.stat(self.myxml) [8]   # will be used for sorting - myxml stronger than url
        self.nicedate = datetime.fromtimestamp(self.date).strftime("%d %b %Y %H:%M:%S")
        self.timestarted = time.time()
        # the following will be modified by parsexml
        self.NbProcessors = 1
        self.E_mail = "unknown"
        self.Type = "unknown"
        self.Script = "unknown"
        self.priority = 0
        keylist = ["NbProcessors", "E_mail", "Type", "Script"]  # adapt here
        self.keylist = keylist
        self.parsexml(keylist)
    @property
    def url(self):
        return op.join(self.loc,self.name)
    @property
    def started(self):
        return self.nicedate
    @property
    def myxml(self):
        return op.join(self.loc,self.name,"infos.xml")
    def parsexml(self, keylist):
        """    analyses info.xml files    """
        parser = make_parser()
        handler = AnalInfo(self, self.keylist)     # inject values inside current Job
        parser.setContentHandler(handler)
        try:
            parser.parse(self.myxml)
        except:
             print "ERROR in reading infos.xml for job", self.name
    @property
    def mylog(self):
        return op.join(self.loc,self.name,"NPKDosy0.log")
    def avancement(self):
        av = (time.time-self.timestarted)/30  # assumes 30 sec jobs
        return "%.f"%(100.0*av)
    def time(self):
        """   analyse log file, return elapsed time as a string """
        import re
        tt = "undefined"
        try:
            for l in open(self.mylog,'r').readlines():
                m = re.search("time:\s*(\d+)",l)   #
                if m:  tt = m.group(1)
        except:
            pass
        return tt
    @property
    def myparam(self):
        return op.join(self.loc,self.name,"param.gtb")
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
    def __repr__(self):
        p = ["JOB  %s"%self.name]
        for k in ["nicedate", "NbProcessors","E_mail","Type","Script","myxml"]:
            try:
                p.append("    %s : %s"%(k, getattr(self, k)) )
            except:
                pass
        return "\n".join(p)
def job_list(path, sorted=True):
    " returns a list with all jobs in dire"
    ll = []
    for i in os.listdir(path):
        if os.path.isdir(os.path.join(path,i)) :
            ll.append( Job(path,i) )
    if sorted:
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
        print "init"
        # read config
        self.configfile = configfile
        self.config = SafeConfigParser()
        self.config.readfp(open(configfile))
        self.QM_FOLDER = self.config.get("QMServer", "QM_FOLDER")
        self.MaxNbProcessors = self.config.get("QMServer", "MaxNbProcessors")
        self.ROOT = self.QM_FOLDER
        self.debug = self.config.getboolean( "QMServer", "Debug")
        self.qJobs = op.join(self.QM_FOLDER,"QM_qJobs")
        self.Jobs = op.join(self.QM_FOLDER,"QM_Jobs")
        self.dJobs = op.join(self.QM_FOLDER,"QM_dJobs")
        self.nap_time = 1.0

    def run(self):
        "the way to start to QM endless loo"
        while True :
            next = self.wait_for_job()
            self.run_job(next)            
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
            self.queue_jobs = job_list(self.qJobs)
            self.nap()
        next_job = self.queue_jobs.pop()
        return next_job
    def watch_procs(self):
        """
        method that watches procs and finishs when no proc is calculating
        """
        jobs = self.determine_Jobs()
        
        while len(jobs) > 0:
            self.nap()
            jobs = self.determine_Jobs()
        print directory_qJobs,directory_Jobs
        os.mkdir(directory_Jobs)
        
        os.rename(directory_qJobs,directory_Jobs)
        
    def run_job(self, job):
        """
        method that deals with moving job to do around and running NPK 
        maybe also send e-mail once the job is done ... 
        """
        print "###########\nStarting :\n", job
        to_qJobs = op.join(self.qJobs, job.name)
        to_Jobs = op.join(self.Jobs, job.name)
        to_dJobs = op.join(self.dJobs, job.name)
        
        os.rename(to_qJobs, to_Jobs)
        job.loc = self.Jobs
        os.chdir(to_Jobs)
        if job.Script == "unknown":
            job.Script = 'echo no-script; pwd; sleep 10; ls -l'
            print "empty job"
        if job.NbProcessors > self.MaxNbProcessors:
            msg = "###########\nNb of processors limited to %d\n###########\n"%self.MaxNbProcessors
            print msg
            with open("process.log","w") as F:
                F.write(msg)
            job.NbProcessors = self.MaxNbProcessors
        putenv("NB_PROC", str(job.NbProcessors))
        Script = job.Script+">> process.log 2>&1"
        try:
            retcode = subprocess.call(Script, shell=True)
        except OSError, e:
            print "Execution failed:", e
        os.chdir(self.qJobs)
        os.rename(to_Jobs, to_dJobs)


if  __name__ == '__main__':
    q = QM("QMserv.cfg")
    queue_jobs = job_list(q.qJobs)
    while queue_jobs:
        print queue_jobs.pop()
    q.run()
