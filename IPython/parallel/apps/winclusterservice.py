#!/usr/bin/env python
# encoding: utf-8
"""
The IPython cluster windows service

Authors:

* Jan Schulz

Based on code from http://code.activestate.com/recipes/576451-how-to-create-a-windows-service-in-python/ 
(MIT licenced)

Needs pywin32 from http://sourceforge.net/projects/pywin32/ or http://www.lfd.uci.edu/~gohlke/pythonlibs/#pywin32

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from IPython.parallel.apps.ipclusterapp import (IPClusterStart, IPClusterStop,ALREADY_STOPPED)
from IPython.parallel.apps.baseapp import PIDFileError

from subprocess import check_call, CalledProcessError, PIPE

import os

# The pywin32 service classes
try:
    import win32service
    import win32serviceutil
    import win32api
    import win32con
    import win32event
    import win32evtlogutil
except:
    print "Required dependency pywin32 is not installed - please install it!"

#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------


default_config_file_name = u'ipclusterservice_config.py'



class IPClusterServiceApp(IPClusterStart):
    """Configures the cluster app into a windows service"""

    # get the kill routine combined with IPClusterStart
    kill_cluster = IPClusterStop.start.im_func
    
    def exit(self,  exit_status=0):
        self.log.debug("Exiting application: %s" % self.name)
        raise Exception(exit_status)


class IPClusterService(win32serviceutil.ServiceFramework):

    _svc_name_ = "IPClusterService"
    _svc_display_name_ = "IPython cluster"
    _svc_description_ = "IPython cluster service for parallel computing"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)


    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)


    def SvcDoRun(self):
        import servicemanager
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        # Start the cluster
        import sys
        # Clean up the commandline args so that the ipython app don't hrow an error
        pythonservice_path = sys.executable
        print(sys.executable)
        sys.executable = u"C:\\portabel\\Python27\\python.exe" # TODO: change to figure it out!
        sys.argv = [sys.argv[0], "--log-level=DEBUG", "--log-to-file=True", "--reuse"]
        # TODO: Add only reuse and log-to-file
        servicemanager.LogInfoMsg(str(sys.argv))
        self.clusterapp = IPClusterServiceApp.instance()
        #self.clusterapp.log_level = 0 # debug
        self.clusterapp.initialize()
        self.clusterapp.start()
        
        
        self.timeout = 30000
        
        # TODO: without a loop? Just use it for restarting?
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                # kill the cluster
                # Todo: is there another way? Stop both launcher?
                self.clusterapp.kill_cluster()
                #self._kill_cluster(self.clusterapp)
                servicemanager.LogInfoMsg(self._svc_name_ + "- STOPPED")
                break
            else:
                servicemanager.LogInfoMsg(self._svc_name_ + "- is alive and well")


def ctrlHandler(ctrlType):
    return True

def launch_new_instance():
    """Create and run the IPython cluster service commandline app."""
    print("Call 'ipython profile create --parallel' as the desired user and configure the profile before starting the service!")
    win32api.SetConsoleCtrlHandler(ctrlHandler, True)
    win32serviceutil.HandleCommandLine(IPClusterService)

if __name__ == '__main__':
    launch_new_instance()
