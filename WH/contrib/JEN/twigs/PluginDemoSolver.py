# file: ../twigs/PluginDemoSolver.py

# History:
# - 07sep2007: creation (from Plugin.py)

# Description:

"""The PluginDemoSolver class makes makes a subtree that takes an input node and
produces a new rootnode by .....
"""


#======================================================================================

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

from Timba.TDL import *
from Timba.Meq import meq

import Meow

from Timba.Contrib.JEN.twigs import Plugin
from Timba.Contrib.JEN.twigs import LeafParm
from Timba.Contrib.JEN.control import OptionManager
from Timba.Contrib.JEN.control import Executor

import math



#=============================================================================
#=============================================================================

class PluginDemoSolver(Plugin.Plugin):
    """Class derived from Plugin"""

    def __init__(self,
                 quals=None, kwquals=None,
                 submenu='compile',
                 OM=None, namespace=None,
                 **kwargs):

        Plugin.Plugin.__init__(self, name='PluginDemoSolver',
                               quals=quals, kwquals=kwquals,
                               submenu=submenu,
                               is_demo=True,
                               OM=OM, namespace=namespace,
                               **kwargs)

        # Use the LeafParm Plugin as the 'left-hand-side' of the equation(s).
        # It shares the OptionManager (OM), so the LeafParm menu is nested
        # in the Demo menu by giving the correct subsub menu name.
        subsubmenu = submenu+'.'+self.name
        self._lhs = LeafParm.LeafParm (submenu=subsubmenu, OM=self._OM)
        return None

    
    #====================================================================

    def define_compile_options(self, trace=True):
        """Specific: Define the compile options in the OptionManager.
        """
        if not self.on_entry (trace=trace):
            return self.bypass (trace=trace)
        #..............................................
        self._OM.define(self.optname('niter'), None,
                        prompt='nr of iterations',
                        opt=[None,1,2,3,5,10,20,30,50,100],
                        doc="""Nr of solver iterations.
                        """)
        # self._lhs.define_compile_options(trace=trace)
        #..............................................
        return self.on_exit(trace=trace)


    #--------------------------------------------------------------------

    def make_subtree (self, ns, node, trace=True):
        """Specific: Make the plugin subtree.
        """
        # Check the node, and make self.ns:
        if not self.on_input (ns, node, trace=trace):
            return self.bypass (trace=trace)
        #..............................................

        # Read the specified options:
        niter = self.optval('niter')
        if niter==None or niter<1:
            return self.bypass (trace=trace)

        # Make the subtree:
        lhs = self._lhs.make_subtree(self.ns, trace=trace)
        condeq = self.ns['condeq'] << Meq.Condeq(lhs,node)
        parm = ns.Search(tags='solvable', class_name='MeqParm')
        solver = self.ns['solver'] << Meq.Solver(condeq,
                                                 num_iter=niter,
                                                 solvable=parm)
        node = self.ns['reqseq'] << Meq.ReqSeq(children=[solver,node],
                                               result_index=1)
 
        #..............................................
        # Check the new rootnode:
        return self.on_output (node, internodes=[parm[0], lhs, condeq, solver],
                               trace=trace)





#=============================================================================
#=============================================================================
#=============================================================================
# Test routine (with meqbrowser):
#=============================================================================


pgt = None
if 1:
    xtor = Executor.Executor('Executor', namespace='test',
                             parentclass='test')
    # xtor.add_dimension('l', unit='rad')
    # xtor.add_dimension('m', unit='rad')
    xtor.make_TDLCompileOptionMenu()
    pgt = PluginDemoSolver()
    pgt.make_TDLCompileOptionMenu()
    # pgt.display()


def _define_forest(ns):

    global pgt,xtor
    if not pgt:
        xtor = Executor.Executor()
        xtor.make_TDLCompileOptionMenu()
        pgt = PluginDemoSolver()
        pgt.make_TDLCompileOptionMenu()

    cc = []

    # node = xtor.leafnode(ns)
    node = ns << Meq.Time() + Meq.Freq()
    rootnode = pgt.make_subtree(ns, node)
    cc.append(rootnode)

    if len(cc)==0: cc.append(ns.dummy<<1.1)
    ns.result << Meq.Composer(children=cc)
    xtor.make_TDLRuntimeOptionMenu(node=ns.result)
    return True



#---------------------------------------------------------------

Settings.forest_state.cache_policy = 100

def _tdl_job_execute (mqs, parent):
    """Execute the forest with the specified options (domain etc),
    starting at the named node"""
    return xtor.execute(mqs, parent)
    
def _tdl_job_display (mqs, parent):
    """Just display the current contents of the Plugin object"""
    pgt.display('_tdl_job')
       
def _tdl_job_display_full (mqs, parent):
    """Just display the current contents of the Plugin object"""
    pgt.display('_tdl_job', full=True)
       


       



#===============================================================
# Test routine (without meqbrowser):
#===============================================================


if __name__ == '__main__':
    ns = NodeScope()

    if 1:
        pgt = PluginDemoSolver()
        pgt.display('initial')

    if 0:
        pgt.make_TDLCompileOptionMenu()

    if 0:
        node = ns << 1.0
        pgt.make_subtree(ns, node, trace=True)

    if 1:
        pgt.display('final', OM=True, full=True)



#===============================================================
