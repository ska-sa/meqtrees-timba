#!/usr/bin/python -O

#
#% $Id$ 
#
#
# Copyright (C) 2002-2007
# The MeqTree Foundation & 
# ASTRON (Netherlands Foundation for Research in Astronomy)
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>,
# or write to the Free Software Foundation, Inc., 
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

debuglevels = {};
options = {};

import Timba.utils
import os
import sys

if __name__ == "__main__":
  if not os.access('.',os.W_OK):
    print "You do not have write permissions to your current working directory,",os.getcwd();
    print "MeqTrees must be run in from a directory you can write to, such as your home dir." ;
    print "Please cd to a writable directory and try again." ;
    sys.exit(1);
  
  # tell verbosity class to not parse argv -- we do it ourselves here
  Timba.utils.verbosity.disable_argv(); 
  # parse options is the first thing we should do
  from optparse import OptionParser
  parser = OptionParser()
  parser.add_option("-p", "--port",dest="port",type="int",
                    default=4000+os.getuid(),
                    help="TCP port to listen on for connections from remote meqservers");
  parser.add_option("-s", "--socket",dest="socket",type="string",
                    default="meqbrowser-%d:1"%os.getuid(),
                    help="local Unix socket to listen on for connections from local meqservers, use None for none");
  parser.add_option("-d", "--debug",dest="debug",type="string",action="append",metavar="Context=Level",
                    help="(for debugging C++ code) sets debug level of the named C++ context. May be used multiple times.");
  parser.add_option("-v", "--verbose",dest="verbose",type="string",action="append",metavar="Context=Level",
                    help="(for debugging Python code) sets verbosity level of the named Python context. May be used multiple times.");
  (options, rem_args) = parser.parse_args();
  for optstr in (options.debug or []):
    opt = optstr.split("=") + ['1'];
    context,level = opt[:2];
    debuglevels[context] = int(level);
  Timba.utils.verbosity.disable_argv(); # tell verbosity class to not parse its argv
  for optstr in (options.verbose or []):
    opt = optstr.split("=") + ['1'];
    context,level = opt[:2];
    Timba.utils.verbosity.set_verbosity_level(context,int(level));

  print "Welcome to the MeqTree Browser!";
  print "Please wait a second while the GUI starts up.";

import sys

# first things first: setup app defaults from here and from
# command line (this has to go first, as other modules being imported
# may depend on app_defaults settings)
from Timba.Apps import app_defaults
from Timba.Apps import config

from Timba import qt_threading
from Timba import octopussy
from Timba.Apps import meqserver

import Timba.utils
#from Timba.GUI import app_proxy_gui
#from Timba.GUI.pixmaps import pixmaps
#app_proxy_gui.set_splash_screen(pixmaps.trees_splash.pm,"Starting MeqTimba Brower");

# ugly, but for some reason Purr objects to being imported from within TDL
try: import Purr
except: pass;

def importPlugin (name):
  name = 'Timba.Plugins.'+name;
  try:
    __import__(name,globals(),locals(),[]);
  except Exception,what:
    print "\n WARNING: couldn't import plugin '%s' (%s)"%(name,what);
    print '  This plugin will not be available.';
    
### import plug-ins
#importPlugin('node_execute');
importPlugin('array_browser');
importPlugin('array_plotter');
#importPlugin('histogram_plotter');
importPlugin('result_plotter');
importPlugin('quickref_plotter');
importPlugin('svg_plotter');
importPlugin('pylab_plotter');
importPlugin('collections_plotter');
importPlugin('history_plotter');
#importPlugin('parmfiddler');
# importPlugin('TableInspector');
#importPlugin('stream_control');

def meqbrowse (debug={},**kwargs):
  args = dict(app_defaults.args);
  args['spawn'] = False;
  for d,l in debug.iteritems():
    debuglevels[d] = max(debuglevels.get(d,0),l);
  
  # insert '' into sys.path, so that CWD is always in the search path
  sys.path.insert(1,'');
  if debuglevels:
    octopussy.set_debug(debuglevels);
    
  # start octopussy if needed
  port = options.port;
  sock = options.socket;
  if sock == "None" or sock == "none":
    sock = "";
    print "Not binding to a local socket."; 
  else:
    sock = "="+sock;
    print "Binding to local socket %s"%sock; 
  print "Binding to TCP port %d, remote meqservers may connect with gwpeer=<host>:%d"%(port,port); 
  if not octopussy.is_initialized():
    octopussy.init(gwclient=False,gwtcp=port,gwlocal=sock);
  if not octopussy.is_running():
    octopussy.start(wait=True);
  # start meqserver
  args['gui'] = True;
  mqs = meqserver.meqserver(**args);

#   try:
#     import psyco
#     psyco.log('psyco.log');
#     psyco.profile();
#     print "****** psyco enabled.";
#   except:
#     print "****** You do not have the psyco package installed.";
#     print "****** Proceeding anyway, things will run some what slower.";
#     pass;
  
  mqs.run_gui();  
  mqs.disconnect();
  octopussy.stop();
  
if __name__ == '__main__':
  meqbrowse();
  
#  thread = qt_threading.QThreadWrapper(meqbrowse);
#  print 'starting main thread:';
#  thread.start();
#  thread.join();
#  print 'main thread rejoined, exiting';

