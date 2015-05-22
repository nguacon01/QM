# QueueManager #

# Presentation
The QM (QueueManager) program implements a simplistic Queue Manager, i.e. it allows to run programs in batch, with a queueing system.

The program QM runs in background, with a very small CPU overhead, it waits for jobs to appear in the query folder, verify it, and launch it.
Once the job is finished, the results are moved to a folder were all done jobs are waiting for you for inspection.

To performed this task, job have to be packaged to run in a stand alone manner, indepently of the location from where they are started.
A small file giving some information describing the job has to be written.

QM has been tested and used on Linux, MacOsX, and Windows. It is written in python, but can laucnh codes written in any langages

QM comes with two independent programs :
* **QueueManager.py** is the QM program itself
* **WEB_QMserver.py** is a utility allowing to monitor QM through a web page - not fully debuged yet !



### Version
`__version__ = 0.2`

The current version is working, but still preliminary. Some features are still missing (see below)

This code is Licenced under the Cecill licence code


#Set-up

### dependences
* The QM program and the Web monitor rely only on standard libraries. They run on python 2.7 - python 3.x not tested (and probably not working)
* The Web monitor program requires the additional `bottle` program, which is packaged as a single file into this repository.

### program installation
simply download the repository anywhere on your disk

`hg clone https://delsuc@bitbucket.org/delsuc/qm`

should do it


### program setup
QM operations are organized around 3 folders, which should be created anywhere on your disk.
* `QM_qJobs`    queuing jobs
* `QM_Jobs`     running jobs
* `QM_dJobs`    done jobs

Then QM and the monitor are parametrized in by configuration file called `QMserv.cfg`

### `QMserv.cfg` content
This is a python configuration file, read by the `ConfigParser` python module
There are two sections `QMServer` and `WEB_QMserver`
####QMServer
contains the parameters for the QueueManager program
- `QM_FOLDER` :  the path where you have placed QM_* folders
- `MaxNbProcessors` : the maximum number of processors allowed for one job
- `job_file` : name of the job description file, file can be xml or cfg file types (see below)
- `MailActive` : If MailActive is TRUE, a mail is sent when a job is finished
- `Debug` : debug mode, should not be active in production mode

####WEB_QMserver
- `Host` : the hostname uder which the web page is served, if you choose `localhost` the page will available only on your local machine; if you put the complete name of your computer, the page will be seen on your local network
- `The_Port` : the port on which the server is serving, default is 8000
- `Licence_to_kill` : if True, the kill button will be present (to kill the running job) NOT FULLY DEBUGGED - use at your own risks
- `Debug` : debug mode, should not be active in production mode


#Creating and launching jobs

jobs are folders, they contain all the need information to run code.
Minimum job is
    - a info file, either in xml or cfg format (defined in QMserv.cfg)
    - a script to launch
but you can put in there everything you need (data, code, etc...)

The info file should contain :

typical xml is:
```
<PARAMETER>
    <nb_proc value="12"/>
    <e-mail value="me@gmail.com"/>
    <script value="python process.py param1 param2"/>
    <info value="some description of the job"/>
</PARAMETER>
```

typical cfg is:
```
[QMOptions]
nb_proc : 12
e_mail : me@gmail.com
info : some description of the job
script : python process.py param1 param2
```

The only required entry is script
You can use this file for your own entries

The job program is then runs inside the job folder, which may contain any associated files.
If you use `python` One nice trick you may use is to put there your python module as a zip file (remove all .pyc and .pyo files). Then write a little starter program, with the following line :
```
import sys
sys.path.insert(0,'mymodule.zip')
import mymodule
```
The python import will then be able to import your code directly from the zip file.



* Summary of set up
* Configuration
* Dependencies
* Database configuration
* How to run tests
* Deployment instructions


#contact

This ode has been written by Marc-André Delsuc (madelsuc@unistra.fr).
It is used