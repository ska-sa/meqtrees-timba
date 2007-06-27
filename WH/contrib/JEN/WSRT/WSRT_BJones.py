# file: ../WSRT/WSRT_BJones.py

# History:
# - 15jun2007: creation (from Grunting/WSRT_Joneset.py)

# Description:

# WSRT BJones matrix module, derived from Grunt.Joneset22, with TDLOptions

# Copyright: The MeqTree Foundation


#======================================================================================
# Preamble:
#======================================================================================

from Timba.TDL import *
from Timba.Meq import meq

from Timba.Contrib.JEN.Grunt import Joneset22


#=================================================================================================


def TDL_parmgroups(full=False):
    """Return the available groups of MeqParms"""
    pg = [None,'BJones'] 
    return TDLCompileOption('TDL_BJones_solvable', 'groups of solvable BJones parms',pg,
                            doc='select group(s) of solvable BJones parms ...')


#--------------------------------------------------------------------------------------------

TDLCompileOption('TDL_tfdeg',"tfdeg",
                 [[0,5],[0,4],[1,4]],
                 doc='rank of time/freq polynomial')

#--------------------------------------------------------------------------------------------

class BJones (Joneset22.BJones):
    """Class that represents a set of 2x2 WSRT BJones matrices.
    In principle, BJones models on the electronic IF bandpass,
    but in practice it usually absorbs other frequency effects as well"""

    def __init__(self, ns, name='BJones',quals=[], 
                 tfdeg=None,
                 override=None,
                 stations=None, simulate=False):

        if tfdeg==None: tfdeg = TDL_tfdeg
        
        # Just use the generic BJones in Grunt/Joneset22.py
        Joneset22.BJones.__init__(self, ns, quals=quals, name=name,
                                  telescope='WSRT',
                                  polrep='linear',
                                  tfdeg=tfdeg,
                                  override=override,
                                  stations=stations, simulate=simulate)
        return None






     
#===============================================================
# Test routine (with meqbrowser):
#===============================================================

def _define_forest(ns):

    cc = []

    jones = BJones(ns, quals=[], simulate=False)
    cc.append(jones.visualize())
    jones.display(full=True)
        
    ns.result << Meq.Composer(children=cc)
    return True

#---------------------------------------------------------------

def _tdl_job_execute (mqs, parent):
    """Execute the forest, starting at the named node"""
    domain = meq.domain(1.0e8,1.1e8,1,1000)                            # (f1,f2,t1,t2)
    cells = meq.cells(domain, num_freq=1, num_time=100)
    request = meq.request(cells, rqtype='ev')
    result = mqs.meq('Node.Execute',record(name='result', request=request))
    return result
       


#===============================================================
# Test routine (standalone):
#===============================================================

if __name__ == '__main__':
    ns = NodeScope()


    if 1:
        J = BJones(ns, quals=['xxx'], tfdeg=TDL_tfdeg)
        J.display(full=True)


#===============================================================
    