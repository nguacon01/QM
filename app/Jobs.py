from .Job import Job
import glob
import os

QUEUE_JOBS = "QM_qJobs"
RUNNING_JOBS = "QM_Jobs"
ERROR_JOBS = "QM_lost+found"
DONE_JOBS = "QM_dJobs"

class Jobs(object):
    def __init__(self, QM):
        self.QM = QM

    def _get_jobs_folder_path(self, type):
        """
            type must be: "queue", "running", "done", "error" or None
        """
        jobs_folder = ''
        if type==QUEUE_JOBS:
            return os.path.join(self.QM.Qm_Folder, QUEUE_JOBS)
        elif type==ERROR_JOBS:
            return os.path.join(self.QM.Qm_Folder, ERROR_JOBS)
        elif type==DONE_JOBS:
            return os.path.join(self.QM.Qm_Folder, DONE_JOBS)
        elif type==RUNNING_JOBS:
            return os.path.join(self.QM.Qm_Folder, RUNNING_JOBS)
        else:
            return self.QM.Qm_Folder
            
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

        return jobs_data
    