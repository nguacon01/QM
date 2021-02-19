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
# import yagmail
import pwd
from pathlib import Path

__version__ = 0.4

debug = False


def start_logger():
    "configurate and start logger"
    # create logger
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", filename="QueueManager.log")
    # limit size, and add rotate
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


class Job(object):
    """this class holds every thing to describe a job"""
    job_type = None  # these entries will be overwriten at start-up
    job_file = None
    print('in beginnng of Job')

    def __init__(self, loc, name):
        self.loc = loc      # QM_xJobs
        self.name = name    # the job directory name
        # will be used for sorting - myjobfile stronger than url
        self.date = os.stat(self.myjobfile)[8]
        self.nicedate = datetime.fromtimestamp(
            self.date).strftime("%d %b %Y %H:%M:%S")
        self.timestarted = time.time()
        # the following will be modified by parsexml/parsecfg
        self.nb_proc = 1
        self.e_mail = "unknown"
        self.username = None
        self.info = "unknown"
        self.script = "unknown"
        self.priority = 0
        self.size = "undefined"
        keylist = ["nb_proc", "e_mail", "info",
                   "script", "priority", "size"]  # adapt here
        self.keylist = keylist
        if debug:
            print('self.loc ',  self.loc)
            print('self.name ', self.name)
            print('self.nb_proc ', self.nb_proc)
            print('self.e_mail ', self.e_mail)
            print('self.info ', self.info)
            print('self.script ', self.script)
            print('self.priority', self.priority)
            print('self.size', self.size)
        # and get them
        if self.job_type == "xml":
            self.parsexml()
        if self.job_type == "cfg":
            print('job type is cfg. Start parse config')
            self.parsecfg()
        for intkey in ["nb_proc", "priority", "size"]:
            try:
                setattr(self, intkey, int(getattr(self, intkey)))
            except ValueError:
                setattr(self, intkey, "undefined")

    @property
    def url(self):
        return op.join(self.loc, self.name)

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
            config.read_file(F)
        if config.has_option('Proc', 'username'):
            val = config.get('Proc', 'username')
            setattr(self, 'username', val)
            print('set username:', val)
        for k in self.keylist:
            if config.has_option("QMOptions", k):
                val = config.get("QMOptions", k)
                setattr(self, k, val)

    def parsexml(self):
        """    load info.xml files    """
        parser = make_parser()
        # inject values inside current Job
        handle = XmlInfo(self, self.keylist)
        parser.setContentHandler(handle)
        parser.parse(self.myjobfile)

    @property
    def mylog(self):
        return op.join(self.loc, self.name, "process.log")

    def avancement(self):
        """   analyse log file, return avancement as a string 0 ... 100   """
        import re
        av = 0.0
        with open(self.mylog, 'r') as F:
            for l in F.readlines():
                # Processing col 8154   5 / 32
                m = re.search(r"\s+(\d+)\s*/\s*(\d+)", l)
                if m:
                    av = float(m.group(1))/float(m.group(2))
        if debug:
            print("avancement", av)
        return "%.f" % (100.0*av)

    def time(self):
        """   analyse log file, return elapsed time as a string """
        import re
        tt = "- undefined -"
        with open(self.mylog, 'r') as F:
            for l in F.readlines():
                if l.startswith('elapsed time:'):
                    tt = l.strip().split(':')[-1]
        return tt

    def run1(self):
        "run the job - shell script way - blocking"
        Script = self.script+">> process.log 2>&1"
        try:
            self.retcode = subprocess.call(Script, shell=True)
        except OSError as e:
            logging.error("Execution failed:" + str(e))
            self.retcode = -1

    def demote(self, user_uid, user_gid):
        """
        Change user uid and user gid to run a sub process as other user
        """
        def set_ids():
            os.setgid(user_gid)
            os.setuid(user_uid)
        return set_ids

    def run2(self):
        "run the job - Popen way - blocking"
        logfile = open("process.log", 'w')
        time_start = time.time()
        print('Job started by QM at: ', datetime.now().isoformat(
            timespec='seconds'), file=logfile)
        logfile.flush()
        Script = self.script.split()  # "python"
        if True:
            preexec_fn = None
            if self.username is not None:
                user_uid = pwd.getpwnam(str(self.username)).pw_uid
                user_gid = pwd.getpwnam(str(self.username)).pw_gid
                print("user_uid:", user_uid, file=logfile)
                preexec_fn = self.demote(user_uid, user_gid)
            # run sub process as not root username which is declared in proc_config.cfg file
            try:
                p1 = subprocess.Popen(
                    Script, stdout=logfile, stderr=subprocess.STDOUT, preexec_fn=preexec_fn)
                ok = True
            except:
                ok = False
                print('Script could not be run, aborted', file=logfile)
                self.retcode = -1
            while ok:
                self.retcode = p1.poll()
                if self.retcode is None:
                    time.sleep(1.0)
                else:
                    print("Job finished at: %s with code %d" % (
                        datetime.now().isoformat(timespec='seconds'), self.retcode), file=logfile)
                    break
        time_finish = time.time()
        duration = time_finish - time_start
        logfile.write('elapsed time: ' + str(round(duration, 0)) + 's')
        logfile.close()
        return self.retcode
    run = run2

    def launch(self):
        """
        Launch the job - not blocking
        use self.poll() or self.wait() to monitor the end of the process
        and self.close() to close logfile
        """
        self.logfile = open("process.log", 'w')
        Script = self.script.split()  # "python"
        self.process = subprocess.Popen(
            Script, stdout=self.logfile, stderr=subprocess.STDOUT)

    def poll(self):
        return self.process.poll()

    def wait(self):
        return self.process.wait()

    def close(self):
        return self.logfile.close()

    def __repr__(self):
        p = ["JOB  %s" % self.name]
        for k in ["nicedate", "nb_proc", "e_mail", "info", "script", "priority", "myjobfile"]:
            try:
                p.append("    %s : %s" % (k, getattr(self, k)))
            except:
                pass
        return "\n".join(p)


def job_list(path, error, do_sort=True):
    " returns a list with all jobs in path"
    ll = []
    if debug:
        print('in job list', path)
    for i in os.listdir(path):
        if debug:
            print(i)
        if os.path.isdir(os.path.join(path, i)):
            try:
                if debug:
                    print("JJ = Job(path,i)")
                JJ = Job(path, i)
            except:
                msg = "Job invalid: "+os.path.join(path, i)
                logging.warning(msg)
                with open(os.path.join(path, i, "process.log"), "w") as F:
                    F.write(msg)

                os.rename(os.path.join(path, i), os.path.join(error, i))
                logging.warning("Job %s moved to %s" %
                                (os.path.join(path, i), error))
            else:
                if debug:
                    print('append new job to ll ')
                ll.append(JJ)
    if do_sort:
        ll.sort(reverse=True, key=lambda j: j.date)   # sort by reversed date
    return ll


class Email(object):
    """
    This class helps us to send mail whenever job is done or has error
    self.config : which is read from config file
    self.body: body of email
    self.sender: sender is loaded from config
    self.pwd : load from config
    self.subject: mail's subject
    """

    def __init__(self, config, receiver, body, subject):
        self.config = config
        self.receiver = receiver
        self.body = body
        # check MailSender and MailSecretKey in config file.
        # If it does not exist or does not have value, then we load it from env variables
        if self.config.has_option('QMServer', 'MailSender') and self.config.get('QMServer', 'MailSender') != '':
            self.sender = self.config.get('QMServer', 'MailSender')
        else:
            self.sender = os.environ['MailSender']
        if self.config.has_option('QMServer', 'MailSecretKey') and self.config.get('QMServer', 'MailSecretKey') != '':
            self.secretkey = self.config.get('QMServer', 'MailSecretKey')
        else:
            self.secretkey = os.environ['MailSecretKey']
        self.subject = subject

    def sendMail(self):
        """
            send email
        """
        import yagmail
        yag = yagmail.SMTP(self.sender, self.secretkey)
        print('Sending mail to ', self.receiver)
        yag.send(
            to=self.receiver,
            subject=self.subject,
            contents=self.body
        )
        print('Mail sent to ', self.receiver)


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
        self.config = ConfigParser()
        with open(configfile) as F:
            self.config.read_file(F)
        # self.QM_FOLDER = self.config.get("QMServer", "QM_FOLDER")

        # In priori, load QM_FOLDER path from environment variables. If it does not exist, load it from config file
        self.QM_FOLDER = os.environ.get(
            'QM_FOLDER', self.config.get("QMServer", "QM_FOLDER"))

        self.MaxNbProcessors = int(
            self.config.get("QMServer", "MaxNbProcessors"))
        print("MaxNbProcessors", self.MaxNbProcessors)
        self.launch_type = self.config.get("QMServer", "launch_type")
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
        print('self.job_type ', self.job_type)
        self.ROOT = self.QM_FOLDER
        print('self.ROOT', self.ROOT)
        self.debug = self.config.getboolean("QMServer", "Debug")
        if self.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        self.qJobs = op.join(self.QM_FOLDER, "QM_qJobs")
        self.Jobs = op.join(self.QM_FOLDER, "QM_Jobs")
        self.dJobs = op.join(self.QM_FOLDER, "QM_dJobs")
        self.lostJobs = op.join(self.QM_FOLDER, "QM_lost+found")
        for f in (self.qJobs, self.Jobs, self.dJobs, self.lostJobs):    # check set-up
            if not os.path.exists(f):
                os.makedirs(f)
        for f in glob.glob(self.Jobs + "/*"):  # clean left-overs
            b = datetime.now().isoformat(timespec='seconds') + os.path.basename(f)
            logging.warning('renaming left-over job "%s" to "%s"' %
                            (f, os.path.join(self.lostJobs, b)))
            os.rename(f, os.path.join(self.lostJobs, b))
        self.queue_jobs = []
        self.running_jobs = []
        self.nap_time = 3.0       # in second

    def run(self):
        "the way to start to QM endless loop"
        if self.launch_type == "blocking":
            while True:
                next_one = self.wait_for_job()
                self.run_job(next_one)
        elif self.launch_type == "non-blocking":
            print('self.launch_type == "non-blocking"')
            while True:
                N = self.clean_running_n_count()
                self.queue_jobs = job_list(self.qJobs, self.dJobs)
                if self.queue_jobs:
                    next_one = self.queue_jobs.pop()
                    # if there is room
                    if N + min(next_one.nb_proc, self.MaxNbProcessors) <= self.MaxNbProcessors:
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
        self.queue_jobs = []
        while len(self.queue_jobs) == 0:
            self.queue_jobs = job_list(self.qJobs, self.dJobs)
            self.nap()
        next_job = self.queue_jobs.pop()
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
                # cannot be larger than self.MaxNbProcessors
                N += min(self.MaxNbProcessors, j.nb_proc)
        if self.debug and N > 0:
            counttag = "%s clean_running_n_count() found %d" % (
                datetime.now().strftime("%d %b %Y %H:%M:%S"), N)
            logging.debug(counttag)
            print(counttag)
        return N

    def run_job(self, job):
        """
        method that deals with moving job to do around and running  job.script 
        loanch in blocking or non-blocking mode depending on global flag
        """
        print("=========== Start job {} ===========".format(job.name))
        if debug:
            print('QM [%s] Starting job "%s" by %s' % (
                datetime.now().isoformat(timespec='seconds'), job.name, job.e_mail))
            print('job.nb_proc ', job.nb_proc)
            print('job.info ', job.info)
            print('job.script ', job.script)
            print('job.priority', job.priority)
            print('job.size', job.size)
        self.running_jobs.append(job)
        logging.info('Starting job "%s" by %s' % (job.name, job.e_mail))
        logging.debug(repr(job))
        to_qJobs = op.join(self.qJobs, job.name)
        to_Jobs = op.join(self.Jobs, job.name)
        to_dJobs = op.join(self.dJobs, job.name)

        os.rename(to_qJobs, to_Jobs)    # First move job to work dir
        job.loc = self.Jobs
        os.chdir(to_Jobs)           # and cd there
        if job.script == "unknown":
            job.script = 'echo no-script; pwd; sleep 10; ls -l'
            logging.warning("undefined script in info file")
        if job.nb_proc > self.MaxNbProcessors:
            msg = "Nb of processors limited to %d" % self.MaxNbProcessors
            logging.warning(msg)
            with open("process.log", "w") as F:
                F.write(msg)
            job.nb_proc = self.MaxNbProcessors
        # very primitive way of limiting proc number !
        os.putenv("NB_PROC", str(job.nb_proc))
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
        to_Jobs = op.join(self.Jobs, job.name)
        now = datetime.now().isoformat(timespec='seconds')
        to_dJobs = op.join(self.dJobs, now+'-'+job.name)
        os.chdir(self.qJobs)         # we might be in to_Jobs, so we cd away.
        os.rename(to_Jobs, to_dJobs)

        # update job location after transfer it from QM_Jobs to QM_dJobs
        dJob_loc, dJob_name = os.path.split(to_dJobs)
        job.loc = dJob_loc
        job.name = dJob_name

        if self.mailactive:
            address = job.e_mail
            subject = "QM Job - %s - finished" % job.name
            to_mail = """
                The job named - {0} - started on QueueManager is finished

                Info : {3}

                The processing took :      {1}
                Result can be found here : {2}

                Virtually yours,

                The QueueManager
            """.format(job.name, job.time(), to_dJobs, job.info)
            try:
                mail = Email(config=self.config, receiver=address,
                             body=to_mail, subject=subject)
                mail.sendMail()
            except:
                logging.error("Mail to %s could not be sent" % address)
        logging.info('Finished job "%s" with code %d' %
                     (job.name, job.retcode))
        print('=========== Finished job "%s" with code %d ===========' %
              (job.name, job.retcode))
        self.running_jobs.remove(job)

if __name__ == '__main__':
    start_logger()
    q = QM("QMserv.cfg")
    queue_jobs = job_list(q.qJobs, q.dJobs)
    # print listing
    if q.debug:
        logging.debug("Dump queue content at start-up")
        while queue_jobs:
            logging.debug(repr(queue_jobs.pop()))

    # then loop for ever
    q.run()
