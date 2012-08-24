#!/usr/bin/env python
# encoding: utf-8
"""
The IPython cluster windows service

Authors:

* Jan Schulz

Loosly based on the example from 
from http://code.activestate.com/recipes/576451-how-to-create-a-windows-service-in-python/ 
(MIT licensed)

Needs pywin32 from http://sourceforge.net/projects/pywin32/ or 
http://www.lfd.uci.edu/~gohlke/pythonlibs/#pywin32

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


class IPClusterServiceApp(IPClusterStart):
    """Configures the cluster app into a windows service"""

    # HACK: get the kill routine from IPClusterStop combined with IPClusterStart
    # TODO: refactor IPCluster{Start,Stop}?
    kill_cluster = IPClusterStop.start.im_func
    
    # Overwrite as the original one exits
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
        # Clean up the commandline args so that the ipython app doesn't throw an error
        # add log-to-file because the service is not visible to the user and reuse so that
        # one does not need to copy the files around.
        # everything else must be configured in the config files
        sys.argv = [sys.argv[0], "--log-to-file=True", "--reuse"]
        servicemanager.LogInfoMsg("New commandline: "+ str(sys.argv))
        self.clusterapp = IPClusterServiceApp.instance()
        #self.clusterapp.log_level = 0 # debug
        self.clusterapp.initialize()
        # TODO: Output the used config file?
        servicemanager.LogInfoMsg("Using profile-dir: "+str(self.clusterapp.profile_dir))
        servicemanager.LogInfoMsg("Using work-dir: "+str(self.clusterapp.work_dir))
        self.clusterapp.start()
        
        # ToDo: implement a while loop and look for the engines and restart them if they went down...
        
        # The start command needs to wait otherwise windows thinks that we stopped.
        # Wait for service stop signal
        rc = win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        # Check to see if self.hWaitStop happened
        if rc == win32event.WAIT_OBJECT_0:
            # Stop signal encountered: kill the cluster
            self.clusterapp.kill_cluster()
            servicemanager.LogInfoMsg(self._svc_name_ + "- Stopped")
            break
        else:
            # We can't do anything about it :-(
            servicemanager.LogInfoMsg(self._svc_name_ + "- SOMETHING BAD HAPPENED...")


def ctrlHandler(ctrlType):
    return True

def launch_new_instance():
    """Create and run the IPython cluster service commandline app."""
    print("Call 'ipython profile create --parallel' as the desired user and configure the profile before starting the service!")
    win32api.SetConsoleCtrlHandler(ctrlHandler, True)
    win32serviceutil.HandleCommandLine(IPClusterService)

if __name__ == '__main__':
    launch_new_instance()
