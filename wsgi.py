# import app as queueManager
import os
import shutil
from pathlib import Path

import app as queueManager

def index():
    queueManager.get_QM()

def email():
    # import yagmail
    # yag = yagmail.SMTP('dungdm91@gmail.com',"mjgvaophvtmvoljm")
    # yag.send('dungdm6191@gmail.com', subject = None, contents = 'Hello')
    return True

def move_file():
    source = Path(os.getcwd()) / 'QM_files' / 'QM_dJobs' / 'test_2.j'
    des = Path(os.getcwd()) / 'QM_files' / 'QM_qJobs' / 'test_2.j'
    shutil.move(src=source, dst=des, copy_function=shutil.copytree)
    return 'done'

if __name__ == '__main__':
    index()
    # move_file()
    # app.run(host='0.0.0.0', port=9999, debug=True)