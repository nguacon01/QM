import sys
import time
sys.path.insert(0,'spike.zip')    # to show how a big project can be included
from spike.NPKConfigParser import NPKConfigParser

'''
Dummy processing,  as a test for QM
'''
def PROC(config):
    size = config.getint("Proc","Size")
    total = 0
    for i in range(size):
        print ("processing %d / %d"%(i+1,size) )  # produces : processing i / size   
        sys.stdout.flush()                        # this updates the log file, and allows to monitor how far we are so far
        total = total  + i*(total+i)
        time.sleep(30./size)                # this is just to slow the program down - for demo
    with open('results.txt','w') as F:
        F.write("Final result is :\n%d"%total)
    print ("Done")
if __name__=='__main__':
    configfile = sys.argv[1]
    config = NPKConfigParser()
    config.read(configfile)
    processing = PROC(config)
