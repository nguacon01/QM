# import app as queueManager
from flask import Flask, json, redirect, request, jsonify
import os
import shutil
from pathlib import Path
from configparser import ConfigParser
import logging
import random
import string

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return 'this is queue manager server'

def start_logger():
    "configurate and start logger"
    # create logger
    logging.basicConfig(level=logging.INFO, \
        format="%(asctime)s %(levelname)s %(message)s", filename="web.log")
    

def read_config():
    config = ConfigParser()
    config.read('QMserv.cfg')
    return config

@app.route('/create_job', methods=['POST','GET'])
def create_job():
    logging.info('===create a job in queue===')
    if request.method == 'GET':
        logging.info('incomming method is GET')
        return jsonify({'msg':'Method must be POST'}), 401

    params = request.json
    job_name = params.get('job_name')
    email = params.get('email')
    directory = params.get('directory')
    mscf_file = params.get('mscf_file')
    # ?
    # username = request.args.get('username')

    if not job_name or not email or not directory:
        logging.info('Not enough information for a job')
        return jsonify({'msg':'Not enough information for a job'}), 402
    
    config = read_config()

    queue_root = config.get('QMServer', 'QM_FOLDER')
    queue_folder_path = Path(queue_root) / 'QM_qJobs'

    # Here we need to create a tmp job folder before creating job folder .j
    # Because even if there is not any file in job folder .j, queue manager will launch it
    # So here we create a tmp job folder with a random name, then create all corresponds files, then cope them into job folder .j
    # tmp job folder will be removed after all
    # create a tmp job folder
    chars = string.ascii_uppercase
    random_name = ''.join(random.choice(chars) for _ in range(6))
    job_folder_temp = Path(queue_folder_path) / random_name
    # check if tmp job folder existed
    if os.path.exists(job_folder_temp):
        logging.info('Job tmp folder existed')
        return jsonify({'msg':'Job existed'}), 403
    # create tmp job folder
    os.mkdir(job_folder_temp)
    logging.info(f'Job folder .j is created with path:{job_folder_temp}')

    # create job folder .j
    job_folder = Path(queue_folder_path) / job_name
    # check if job folder existed
    if os.path.exists(job_folder):
        logging.info('Job folder .j existed')
        return jsonify({'msg':'Job existed'}), 403

    # create proc_config.cfg file
    proc_config_path = Path(job_folder_temp)/'proc_config.cfg'
    proc_conf = ConfigParser()
    proc_conf['Proc'] = {
        'username' : 'euftcasc4de', 
        'directory' : directory,
        'mscf_file' : mscf_file
    }
    proc_conf['QMOptions'] = {
        'nb_proc' : 4,
        'e_mail' : email,
        'info': 'can be inserted here',
        'script' : 'python LauncheEUFTICR.py proc_config.cfg'
    }
    with open(proc_config_path, 'w') as f:
        proc_conf.write(f)

    # create LauchEUFTICR.py file
    shutil.copy(src='job_EUFT/LaunchEUFTICR.py', dst=job_folder_temp)

    shutil.copytree(src=job_folder_temp, dst=job_folder, copy_function=shutil.copy)
    logging.info('copy files from tmp job to job folder .j')
    shutil.rmtree(job_folder_temp)
    logging.info('remove files from tmp job')

    logging.info('===Finish creating job in queue===')
    return jsonify({'msg':'Job is in the queue'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)
    logging = start_logger()