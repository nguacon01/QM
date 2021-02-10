#!/usr/bin/env python
# encoding: utf-8
"""

mini QueueManager

Created by Marc-Andre' on 2015-4-14 loosely inspired from an early version from 2009.

Ported to python 3 in dec 2020

organized around 3 folders

QM_qJobs    queuing jobs
QM_Jobs     running jobs
QM_dJobs    done jobs

jobs itself are folders, they contain all the need information to run code.
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
from __future__ import print_function, division
import os
import os.path as op
import subprocess
import time
import datetime
import sys
import glob
import logging
from configparser import ConfigParser
from xml.sax import handler, make_parser
from datetime import datetime, timedelta
import shutil
import yagmail

__version__ = 0.4

debug = False

QUEUE_JOBS = "QM_qJobs"
RUNNING_JOBS = "QM_Jobs"
ERROR_JOBS = "QM_lost+found"
DONE_JOBS = "QM_dJobs"

class XmlInfo(handler.ContentHandler):
    "used to parse infos.xml files"
    def __init__(self, job, keylist):
        self.job = job
        self.keylist = keylist
    def startElement(self, name, attrs):
        if name in self.keylist:
            value = attrs.get("value")
            setattr(self.job, name, value)
class Job(object):
    """this class holds every thing to describe a job"""
    job_type = 'cfg'  # these entries will be overwriten at start-up
    job_file = 'proc_config.cfg'
    print ('in beginnng of Job')
    def __init__(self, loc, name):
        self.loc = loc      # QM_xJobs
        self.name = name    # the job directory name
        self.date = os.stat(self.myjobfile) [8]   # will be used for sorting - myjobfile stronger than url
        self.nicedate = datetime.fromtimestamp(self.date).strftime("%d %b %Y %H:%M:%S")
        self.timestarted = time.time()
        # the following will be modified by parsexml/parsecfg
        self.nb_proc = 1
        self.e_mail = "unknown"
        self.info = "unknown"
        self.script = "unknown"
        self.priority = 0
        self.size = "undefined"
        keylist = ["nb_proc", "e_mail", "info", "script", "priority", "size"]  # adapt here
        self.keylist = keylist
        if debug:
            print ('self.loc ',  self.loc)
            print ('self.name ', self.name)
            print ('self.nb_proc ', self.nb_proc)
            print ('self.e_mail ', self.e_mail)
            print ('self.info ', self.info)
            print ('self.script ', self.script)
            print ('self.priority', self.priority)
            print ('self.size', self.size)
        # and get them
        if self.job_type == "xml":
            self.parsexml()
        if self.job_type == "cfg":
            self.parsecfg()
        for intkey in ["nb_proc", "priority", "size"]:
            try:
                setattr(self, intkey, int(getattr(self,intkey)))
            except ValueError:
                setattr(self, intkey, "undefined")

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
        config = ConfigParser()
        with open(self.myjobfile) as F:
            config.read_file( F )
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
    def avancement(self):
        """   
            analyse log file, return avancement as a string 0 ... 100   
        """
        import re
        av = 0.0
        with open(self.mylog,'r') as F:
            for l in F.readlines():
                m = re.search(r"\s+(\d+)\s*/\s*(\d+)",l)   ### Processing col 8154   5 / 32
                if m:
                    av = float(m.group(1))/float(m.group(2))
        if debug: print ("avancement", av)
        return "%.f"%(100.0*av)
    def time(self):
        """   analyse log file, return elapsed time as a string """
        import re
        tt = "- undefined -"
        with open(self.mylog, 'r') as F:
            for l in F.readlines():
                m = re.search(r"time:\s*(\d+)",l)   #
                if m:
                    tt = m.group(1)
        return tt
    def run1(self):
        "run the job - shell script way - blocking"
        Script = self.script+">> process.log 2>&1"
        try:
            self.retcode = subprocess.call(Script, shell=True)
        except OSError as e:
            logging.error("Execution failed:"+ str(e))
            self.retcode = -1
    def run2(self):
        "run the job - Popen way - blocking"
        logfile = open("process.log",'w')
        print('Job started by QM at: ',datetime.now().isoformat(timespec='seconds'), file=logfile)
        logfile.flush()
        Script = self.script.split() #"python"
        if True:
            # sub process in which we run job's scripts
            p1 = subprocess.Popen(Script, stdout=logfile, stderr=subprocess.STDOUT)
            response = p1.communicate()
            self.retcode = p1.returncode
            ok =  True
            if self.retcode != 0:
                ok = False
                print(f'Script could not be run, aborted, with retcode is {self.retcode}, message: {response}', file=logfile)
                return self.retcode
            while ok:
                self.retcode = p1.poll()
                if self.retcode is None:
                    time.sleep(1.0)
                else:
                    print ("Job finished at: %s with code %d"%(datetime.now().isoformat(timespec='seconds'), self.retcode), file=logfile)
                    break
        logfile.close()
        return self.retcode
    run = run2
    def launch(self):
        """
        Launch the job - not blocking
        use self.poll() or self.wait() to monitor the end of the process
        and self.close() to close logfile
        """
        self.logfile = open("process.log",'w')
        Script = self.script.split() #"python"
        self.process = subprocess.Popen(Script, stdout=self.logfile, stderr=subprocess.STDOUT)
    def poll(self):
        return self.process.poll()
    def wait(self):
        return self.process.wait()
    def close(self):
        return self.logfile.close()
    def __repr__(self):
        p = ["JOB  %s"%self.name]
        for k in ["nicedate", "nb_proc", "e_mail", "info", "script", "priority", "myjobfile"]:
            try:
                p.append("    %s : %s"%(k, getattr(self, k)) )
            except:
                pass
        return "\n".join(p)
    
    __str__ = __repr__

class Jobs(object):
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager

    def _get_jobs_folder_path(self, type):
        """
            type must be: "queue", "running", "done", "error" or None
        """
        jobs_folder = ''
        if type==QUEUE_JOBS:
            return os.path.join(self.queue_manager.qm_folder, QUEUE_JOBS)
        elif type==ERROR_JOBS:
            return os.path.join(self.queue_manager.qm_folder, ERROR_JOBS)
        elif type==DONE_JOBS:
            return os.path.join(self.queue_manager.qm_folder, DONE_JOBS)
        elif type==RUNNING_JOBS:
            return os.path.join(self.queue_manager.qm_folder, RUNNING_JOBS)
        else:
            return self.queue_manager.qm_folder
            
    # get jobs by type. This function is used to replace function job_list
    # job name will be autolatically generated by mscf file generator
    # with form : 2021-02-09T15:50:13-job_name-of-project-folder_name-of-mscf-file.j
    def get_jobs(self, type=None):
        """
        get jobs in "queue", "running", "done", "error"
        return an array of jobs
        """
        jobs_folder = self._get_jobs_folder_path(type)
        jobs = glob.glob(jobs_folder+'/*.j')
        jobs_data = []
        for job_path in jobs:
            loc, name = os.path.split(job_path)
            job = Job(loc=loc, name=name)
            jobs_data.append(job)
        # in case there is nothing in jobs_data list, job_data.reverse() will return None. So it need to be checked here
        if len(jobs_data) == 0:
            return jobs_data
        return jobs_data.reverse()
class Email(object):
    def __init__(self, config, receiver, body, subject):
        self.config = config
        self.receiver = receiver
        self.body = body
        self.sender = self.config.get('QMServer', 'SendMail')
        self.pwd = self.config.get('QMServer', 'SecKey')
        self.subject = subject

    def sendMail(self):

        receiver = self.receiver
        body = self.body

        yag = yagmail.SMTP(self.config.get('QMServer', 'SendMail'), self.config.get('QMServer', 'SecKey'))
        yag.send(
            to=receiver,
            subject=self.subject,
            contents=body
        )
class QueueManager(object):
    """
    class that deals with all incoming jobs
    It calls sequentially scout that waits for new jobs in the queue
    Then it verifies that no other NPK Job is running
    and it launches the new job
    
    everything is maintained in a self.joblist lists - top job is the first to be run
    """
    def __init__(self, config):
        self.config = config
        self.debug = self.config.getboolean( "QMServer", "Debug")
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        # name of variable should be in lowercase, upercase should be used for constants
        self.qm_folder = self.config.get("QMServer", "QM_FOLDER")
        self.MaxNbProcessors = int(self.config.get("QMServer", "MaxNbProcessors"))
        self.launch_type = self.config.get("QMServer", "launch_type")
        self.job_file = self.config.get("QMServer", "job_file")
        if self.job_file.endswith('.xml'):
            self.job_type = 'xml'
        elif self.job_file.endswith('.cfg'):
            self.job_type = 'cfg'
        else:
            raise Exception("job_file should be either .xml or .cfg")
        self.mailactive = config.getboolean("QMServer", "MailActive")

        # dmd
        self.jobs = Jobs(self)
        # dmd
        self.nap_time = 3.0       # in second
    
    def __str__(self):
        return f"Queue with {self.MaxNbProcessors} processor, job type is {self.job_type}, with {len(self.jobs.get_jobs(type=QUEUE_JOBS))} jobs are in queue"
    __repr__ = __str__

    def run(self):
        "the way to start to QM endless loop"
        if self.launch_type == "blocking":
            while True :
                next_one = self.wait_for_job()
                self.run_job(next_one)
        elif self.launch_type == "non-blocking":
            print ('self.launch_type == "non-blocking"')
            while True :
                N = self.clean_running_n_count()
                # self.queue_jobs = job_list(self.qJobs, self.dJobs)
                self.queue_jobs = self.jobs.get_jobs(type=QUEUE_JOBS)
                if self.queue_jobs:
                    next_one = self.queue_jobs.pop()
                    if N + min(next_one.nb_proc, self.MaxNbProcessors) <= self.MaxNbProcessors:  # if there is room
                        self.run_job(next_one)
                self.nap()
        else:
            raise Exception("error in configuration for launch_type")

    def nap(self):
        "waiting method for spooling"
        time.sleep(self.nap_time)
    def wait_for_job(self):
        """
        method that waits for something to show up in QM_qJobs folder
        and returns an ordered list of present jobs.
        oldest (most prio) first
        """
        while len(self.jobs.get_jobs(type=QUEUE_JOBS)) == 0:
            self.nap()
        next_job = self.jobs.get_jobs(type=QUEUE_JOBS).pop()
        return next_job
    def clean_running_n_count(self):
        """
        go through running job list, close finished ones, and count total CPU burden
        """
        N = 0
        job_list = self.running_jobs
        for j in job_list:
            if j.poll() is not None:  # means it's finished
                j.close()
                self.job_clean(j)
            else:
                N +=  min(self.MaxNbProcessors, j.nb_proc)  # cannot be larger than self.MaxNbProcessors
        if self.debug and N>0:
            counttag = "%s clean_running_n_count() found %d"%(datetime.now().strftime("%d %b %Y %H:%M:%S"),N)
            logging.debug(counttag)
            print (counttag)
        return N
            
    def run_job(self, job):
        """
        method that deals with moving job to do around and running  job.script 
        loanch in blocking or non-blocking mode depending on global flag
        """
        if self.config.get('QMServer', 'Debug'):
            print ('QM [%s] Starting job "%s" by %s'%(datetime.now().isoformat(timespec='seconds'), job.name, job.e_mail))
            print ('job.nb_proc ', job.nb_proc)
            print ('job.info ', job.info)
            print ('job.script ', job.script)
            print ('job.priority', job.priority)
            print ('job.size', job.size)
        # self.running_jobs.append(job)
        logging.info('Starting job "%s" by %s'%(job.name,job.e_mail) )
        logging.debug(repr(job))
        source_qJobs = op.join(self.qm_folder, QUEUE_JOBS, job.name)
        to_Jobs = op.join(self.qm_folder, RUNNING_JOBS, job.name)
        # to_dJobs = op.join(self.QM_FOLDER, DONE_JOBS, job.name)
        
        # move job from queue folder to running folder
        shutil.move(src=source_qJobs, dst=to_Jobs, copy_function=shutil.copytree)
        # os.rename(to_qJobs, to_Jobs)    # First move job to work dir
        job.loc = to_Jobs
        os.chdir(to_Jobs)           # and cd there
        if job.script == "unknown":
            job.script = 'echo no-script; pwd; sleep 10; ls -l'
            logging.warning("undefined script in info file")
        if job.nb_proc > self.MaxNbProcessors:    
            msg = "Nb of processors limited to %d"%self.MaxNbProcessors
            logging.warning( msg )
            with open("process.log","w") as F:
                F.write(msg)
            job.nb_proc = self.MaxNbProcessors
        os.putenv("NB_PROC", str(job.nb_proc))  # very primitive way of limiting proc number !
        if self.launch_type == "blocking":
            retcode = job.run()
            self.job_clean(job)
        if self.launch_type == "non-blocking":
            job.launch()
            # clean will be done later, by clean_running_n_count

    def job_clean(self, job):
        """
        closes and move the job folder to done_Jobs
        maybe also send e-mail once the job is done ... 
        """
        source_Jobs = op.join(self.qm_folder, RUNNING_JOBS, job.name)
        now = datetime.now().isoformat(timespec='seconds')
        to_dJobs = op.join(self.qm_folder, DONE_JOBS, now+'-'+job.name)
        to_errorJobs = op.join(self.qm_folder, ERROR_JOBS, now+'-'+job.name)
        # os.chdir(self.qJobs)         # we might be in to_Jobs, so we cd away.
        # os.chdir(to_Jobs)
        if job.retcode != 0:
            # move job from running folder to error folder in case it has any error
            shutil.move(src=source_Jobs, dst=to_errorJobs, copy_function=shutil.copytree)
            # os.rename(to_Jobs, to_errorJobs)
            subject = f"Your job {job.name} is not completed"
            body = f"""The job named - {job.name} - started on QueueManager is not finished
                        Please check your elements"""
        else:
            # move job from running folder to done folder
            shutil.move(src=source_Jobs, dst=to_dJobs, copy_function=shutil.copytree)
            # os.rename(to_Jobs, to_dJobs)
            subject = f"Your job {job.name} is completed"
            body = f"""The job named - {job.name} - started on QueueManager is finished 
                    Info : {job.info}
                    Result can be found here : {to_dJobs}
                    Virtually yours,
                    The QueueManager"""
        
        if self.mailactive:
            receiver = job.e_mail
            try:
                info_mail = Email(config = self.config, receiver=receiver, body=body, subject=subject)
                mes = info_mail.sendMail()
                logging.error("Sent mail to %s"%receiver)
            except:
                logging.error("Mail to %s could not be sent"%receiver)
        logging.info('Finished job "%s" with code %d'%(job.name, job.retcode))

def start_logger():
    "configurate and start logger"
    # create logger
    logging.basicConfig(level=logging.INFO, \
        format="%(asctime)s %(levelname)s %(message)s", filename="QueueManager.log")

def get_QM(config_file_path):
    """
        Get queue of jobs
    """
    config = ConfigParser()
    if not os.path.isfile(config_file_path) and not config_file_path.endswith('.cfg'):
        raise('file config did not existed')
    config.read(config_file_path)

    queue = QueueManager(config)
    queue.run()

if  __name__ == '__main__':
    
    start_logger()
    get_QM('/home/nguacon01/work/QM/QMserv.cfg')
    # q =  QM("QMserv.cfg")
    # # if q.mailactive:
    # #     from sendgmail import mail               # otherwise, copy it here
    # queue_jobs = job_list(q.qJobs, q.dJobs)
    # # print listing
    # if q.debug:
    #     logging.debug( "Dump queue content at start-up" )
    #     while queue_jobs:
    #         logging.debug( repr(queue_jobs.pop()) )

    # # then loop for ever
    # q.run()
