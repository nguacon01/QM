#!/usr/bin/env python
# encoding: utf-8
"""
mini WEB server for QueueManager

see http://bottle.paws.de/docs/dev/index.html

Created by Marc-Andre on 2015-4-14 based on an early version 2011-01-26.

This code is Licenced under the Cecill licence code

"""


import bottle as b
from bottle import static_file
import time
from datetime import datetime, timedelta
from xml.sax import handler, make_parser
import glob
import os
import os.path as op
import sys
from ConfigParser import SafeConfigParser
from QueueManager import Job



def job_list(path, do_sort=True):
    " returns a list with all jobs in path"
    ll = []
    for i in os.listdir(path):
        if os.path.isdir(os.path.join(path,i)) :
            if True: #try:
                JJ = Job(path,i)
            # except:
            #     print "Job invalid: "+os.path.join(path,i)
            # else:
                ll.append( JJ )
    if do_sort:
        ll.sort(reverse=True, key=lambda j: j.date)   # sort by reversed date
    if debug:
        print ll
    return ll

def stat(dire):
    "compute usage statitics"
    from collections import defaultdict
    jobs = job_list(dire)
    cpu_users = defaultdict(int)    # collect cpu time
    job_users = defaultdict(int)    # collect nb of jobs
    for j in jobs:
        if j.e_mail == "":
            j.e_mail = "Anonymous"
        job_users[j.e_mail] += 1
        try:
            cpu_users[j.e_mail] += int(j.time())
        except ValueError:
            pass
    for u in cpu_users.keys():
        print u, job_users[u], cpu_users[u]
    return (job_users, cpu_users)

###### pages
# route defines URL
# view defines template file to use

@b.route('/static/:filename#.*#')
def static(filename):
    return static_file(filename, root='views/static/')
    
@b.route('/test')
def testl():
    id = b.request.GET['id']
    q = b.request.query_string
    return q, "\nId = ",id
    
@b.route('/')
@b.route('/QM')
@b.route('/QM/')
@b.view('QM')
def QM():
    "returns the front page of QM helper"
    running=0
    licence_to_kill = Licence_to_kill
    refresh = 9  # refresh rate
    now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
    done = job_list(QM_dJobs)
    waiting = job_list(QM_qJobs)
    r = job_list(QM_Jobs)
    if r:
        running = r[0]
    return locals()

@b.route()
def kill(fil="None", conf=False):  # implicite route : /kill/job(/True)  - third field is required for validation
    queue = "QM_Jobs"
    if debug: print "kill - %s - %s - %s -"%(queue, fil, conf)
    if conf:
        if debug:
            print "killed %s"%fil
            print "kill `ps | awk '/NPKDosy/ && ! /ps/ && // {print $1}'`"
        os.system("kill `ps | awk '/NPKDosy/ && ! /ps/ && // {print $1}'`")
        if debug: print op.join(ROOT,queue,fil,'ldir*')
        for i in glob.glob( op.join(ROOT,queue,fil,'ldir*') ):
            os.system("touch %s/dosy.gs2"%i)    # simulate end of processing
    return b.template("Confirm", queue=queue, fil=fil, conf=conf)

@b.route()
def delete(queue="here", fil="None", conf=False):  # implicite route : /delete/here/job(/True)  - third field is required for validation
    "used to delete a job from Done Jobs list"
    import shutil
    if debug: print "delete - %s - %s - %s -"%(queue, fil, conf)
    d = op.join(ROOT,queue,fil)
    print d
    if op.isdir(d):
        if conf:
            if debug:
                print "deleting %s"%d
            shutil.rmtree(d)
        return b.template("Confirm", queue=queue, fil=fil, conf=conf)
    else:
        return b.HTTPError(404, "Job %s not found"%fil)

@b.route('/download/:fil')
def down(fil):
    """used to force download of zip files"""
    d = op.join(ROOT,'QM_dJobs',fil,fil+".zip")
    if op.isfile(d):
        if debug: print d
        return b.static_file(d, root='/', download=fil+".zip")
    else:
        return "File %s not found"%d

@b.route(':name#.+/$#')
@b.view('QM_dJobs')
def test(name):
    "returns the content of directories"
    import os.path as op
    now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
    fich = []
    dire = []
    base = op.join(ROOT,name)
    lb = len(base)
    path = op.join(base,"*")
    for f in glob.glob(path):
        if op.isfile(f):
            fich.append(f[lb:])
        if op.isdir(f):
            dire.append(f[lb:])
    return locals()     # all local variables can now be used in the template

@b.route()
@b.view('stats')
def stats():
    now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")
    (job_users, cpu_users) = stat(QM_dJobs)
    time_users = {u:timedelta(seconds=cpu_users[u]) for u in cpu_users.keys() }
    cputotal = sum(cpu_users.values())
    timetotal = timedelta(seconds=cputotal)
    jobtotal = sum(job_users.values())
    meanjob = timedelta(seconds=int(float(cputotal)/jobtotal))
    return locals()

@b.route(':file#.*#')
def fichier(file):
    "serve all other files as static files"
    if debug: print file
    return b.static_file(file, root=ROOT)



# read config
configfile = "QMserv.cfg"
config = SafeConfigParser()
config.readfp(open(configfile))
QM_FOLDER = config.get( "QMServer", "QM_FOLDER")
QM_qJobs = op.join(QM_FOLDER,"QM_qJobs")
QM_Jobs = op.join(QM_FOLDER,"QM_Jobs")
QM_dJobs = op.join(QM_FOLDER,"QM_dJobs")

job_file = config.get("QMServer", "job_file")
if job_file.endswith('.xml'):
    job_type = 'xml'
elif job_file.endswith('.cfg'):
    job_type = 'cfg'
else:
    raise Exception("job_file should be either .xml or .cfg")
mailactive = config.getboolean("QMServer", "MailActive")

Job.job_file = job_file    # inject into Job class
Job.job_type = job_type


ROOT = QM_FOLDER
debug = config.getboolean( "WEB_QMserver", "Debug")
Host = config.get( "WEB_QMserver", "Host")
try:
    The_Port = config.getint( "WEB_QMserver", "The_Port")
except:
    The_Port =  8000
try:
    Licence_to_kill = config.getboolean( "WEB_QMserver", "Licence_to_kill")
except:
    Licence_to_kill = False
b.debug(debug)
b.run(host=Host, port=The_Port, reloader=debug)

