import os
import sys

# def job_list(path, error, do_sort=True):
#     " returns a list with all jobs in path"
#     ll = []
#     if debug: print ('in job list',path)
#     for i in os.listdir(path):
#         if debug: print (i)
#         if os.path.isdir(os.path.join(path,i)) :
#             try:
#                 if debug: print ("JJ = Job(path,i)")
#                 JJ = Job(path,i)
#             except:
#                 msg = "Job invalid: "+os.path.join(path,i)
#                 logging.warning(msg)
#                 with open(os.path.join(path,i, "process.log"), "w") as F:
#                     F.write(msg)
                
#                 os.rename(os.path.join(path,i), os.path.join(error,i) )
#                 logging.warning("Job %s moved to %s"%(os.path.join(path,i),error) )
#             else:
#                 if debug: print ('append new job to ll ')
#                 ll.append( JJ )
#     if do_sort:
#         ll.sort(reverse=True, key=lambda j: j.date)   # sort by reversed date
#     return ll

def to_utf8(obj):
    return obj

def utf8lize(obj):
    if isinstance(obj, dict):
        return {k: to_utf8(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [to_utf8(x) for x in obj]
    return obj