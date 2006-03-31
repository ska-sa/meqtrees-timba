# MG_JEN_lsm.py

# Short description:
#   A script to explore the possibilities of the LSM

# Keywords: ....

# Author: Jan Noordam (JEN), Dwingeloo

# History:
# - 29 sep 2005: creation
# - 11 feb 2006: total overhaul
# - 22 mar 2006: standard lsm generation

# Copyright: The MeqTree Foundation

# Full description:


   





#********************************************************************************
#********************************************************************************
#**************** PART II: Preamble and initialisation **************************
#********************************************************************************
#********************************************************************************

from Timba.TDL import *
# from Timba.Meq import meq

from Timba.Trees import JEN_inarg
from Timba.Trees import JEN_inargGui

from numarray import *
# from string import *
from copy import deepcopy
from random import *

# Scripts needed to run a MG_JEN script: 
from Timba.Contrib.JEN import MG_JEN_exec
from Timba.Contrib.JEN import MG_JEN_forest_state

from Timba.LSM.LSM import *
from Timba.LSM.LSM_GUI import *
from Timba.Contrib.JEN import MG_JEN_Sixpack






#********************************************************************************
#********************************************************************************
#******************** PART II: Optional: Importable functions *******************
#********************************************************************************
#********************************************************************************



def nvss_3c343(ns, trace=True):
   """Make a lsm for 3C343 from an nvss txt-file"""
   nvss2lsm (ns, nvss_file='/LOFAR/Timba/LSM/test/3C343_nvss.txt', trace=trace)
   return True

#-----------------------------------------------------------------------------
   
def nvss_Abell963(ns, trace=True):
   """Make lsm(s) for Abell963 from nvss txt-file"""
   nvss2lsm (ns, nvss_file='/LOFAR/Timba/LSM/test/abel963.txt', trace=trace)
   if False:
      # Empty
      nvss2lsm (ns, nvss_file='/LOFAR/Timba/LSM/test/Abell963catb.txt', trace=trace)
   return True

#-----------------------------------------------------------------------------
   
def nvss_all(ns, trace=True):
   """Regenerate lsm(s) for all available nvss txt-files"""
   nvss_3c343(ns, trace=trace)
   nvss_Abell963(ns, trace=trace)
   return True

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

def nvss2lsm(ns, nvss_file=None, lsm_name=None, trace=True):
   """Make a lsm from the given nvss (txt) file"""

   if trace:
      print '\n**************************************************************'
      print '** nvss2lsm(',lsm_name,') <- nvss =',nvss_file
      print '**************************************************************\n'

   if not isinstance(nvss_file, str):
      print '** ERROR **: nvss_file =',nvss_file
      return False

   # Make the lsm (file) name from the input nvss_file:
   if not isinstance(lsm_name, str):
      ss = nvss_file.split('/')
      lsm_name = ss[len(ss)-1]                       # remove the directories
      lsm_name = lsm_name.split('.')[0]              # remove the file extension (.txt)
      lsm_name += '.lsm'                             # append .lsm extension
      
   # Use the global lsm.
   global lsm
   lsm = LSM()                                       # make a new one

   #---------------------------------------------------------------------------
   # Alternative:
   if True:
      home_dir = os.environ['HOME']
      infile_name = home_dir + nvss_file
      lsm.build_from_catalog(infile_name, ns)
      if trace:
         print '** Finished build_from_catalog()' 
      lsm.save('lsm_current.lsm')                        # 
      lsm.save(lsm_name)
      lsm.display()
      if trace:
         print '** Saved as:',lsm_name,'   (and lsm_current.lsm)'
         print '**************************************************************\n'
      return True
   #---------------------------------------------------------------------------

   # Read the nvss text-file:
   home_dir = os.environ['HOME']
   infile_name = home_dir + nvss_file
   infile = open(infile_name, 'r')
   all = infile.readlines()
   infile.close()

   # regexp pattern
   pp=re.compile(r"""
      ^(?P<col1>\S+)  # column 1 'NVSS'
      \s*             # skip white space
      (?P<col2>[A-Za-z]\w+\+\w+)  # source name i.e. 'J163002+631308'
      \s*             # skip white space
      (?P<col3>\d+)   # RA angle - hr 
      \s*             # skip white space
      (?P<col4>\d+)   # RA angle - min 
      \s*             # skip white space
      (?P<col5>\d+(\.\d+)?)   # RA angle - sec
      \s*             # skip white space
      (?P<col6>\d+(\.\d+)?)   # eRA angle - sec
      \s*             # skip white space
      (?P<col7>\d+)   # Dec angle - hr 
      \s*             # skip white space
      (?P<col8>\d+)   # Dec angle - min 
      \s*             # skip white space
      (?P<col9>\d+(\.\d+)?)   # Dec angle - sec
      \s*             # skip white space
      (?P<col10>\d+(\.\d+)?)   # eDec angle - sec
      \s*             # skip white space
      (?P<col11>\d+)   # freq
      \s*             # skip white space
      (?P<col12>\d+(\.\d+)?)   # brightness - Flux
      \s*             # skip white space
      (?P<col13>\d*\.\d+)   # brightness - eFlux
      \s*
      \S+
      \s*$""",re.VERBOSE)
 
   # read each source and insert to LSM
   linecount=0
   for eachline in all:
      v = pp.search(eachline)
      if v!=None:
         linecount+=1
         if trace:
            print linecount,':',v.group('col2'), v.group('col12')
         s=Source(v.group('col2'))
         source_RA=float(v.group('col3'))+(float(v.group('col5'))/60.0+float(v.group('col4')))/60.0
         source_RA*=math.pi/12.0
         source_Dec=float(v.group('col7'))+(float(v.group('col9'))/60.0+float(v.group('col8')))/60.0
         source_Dec*=math.pi/180.0

         my_sixpack = MG_JEN_Sixpack.newstar_source(ns, punit=s.name,
                                                    I0=eval(v.group('col12')),
                                                    SI=[random()], f0=1e6,
                                                    RA=source_RA,
                                                    Dec=source_Dec,
                                                    fsr_trace=False,
                                                    trace=False)
         if trace: print '  -> Sixpack:',my_sixpack.label()

         # First compose the sixpack before giving it to the LSM
         SourceRoot = my_sixpack.sixpack(ns)
         # my_sixpack.display()
         lsm.add_source(s, brightness=eval(v.group('col12')),
                        sixpack=my_sixpack,
                        ra=source_RA, dec=source_Dec)
   if trace:
      print "** Inserted %d sources" % linecount

   # Finishing touches:
   lsm.setNodeScope(ns)                           # remember node scope....(!)
   lsm.save('lsm_current.lsm')                        # 
   lsm.save(lsm_name)
   lsm.display()
   if trace:
      print '** Saved as:',lsm_name,'   (and lsm_current.lsm)'
      print '**************************************************************\n'
   return True





#=================================================================================

# Create an empty global lsm, just in case:
lsm = LSM()
# lsm.display()    # QPaintDevice: Must construct a QApplication before a QPaintDevice


#=================================================================================
#=================================================================================
#=================================================================================


def arcmin2rad(arcmin=None):
   """Convert arcmin to radians"""
   factor = pi/(60*180)                         # 180/pi = 57.2957795130....
   if not arcmin==None: return arcmin*factor    # if arcmin specified, convert
   return factor                                # return conversion factor

def deg2rad(deg=None):
   """Convert deg to radians"""
   factor = pi/180                              # 180/pi = 57.2957795130....
   if not deg==None: return deg*factor          # if deg specified, convert
   return factor                                # return conversion factor


#--------------------------------------------------------------------------------

def att (dRA_rad=0, dDec_rad=0, taper_deg=None, trace=False):
   """Calculate gaussian primary beam attenuation"""
   a = 1.0
   if not taper_deg==None: 
      drad = (dRA_rad**2 + dDec_rad**2)
      trad = deg2rad(taper_deg)**2
      a = exp(-drad/trad)
   if trace: print '** att(',dRA_rad,dDec_rad,taper_deg,'): ->',a
   return a
   
   
#--------------------------------------------------------------------------------

def add_single (ns=None, Sixpack=None, lsm=None, **inarg):
   """Add a test-source (Sixpack) to the given lsm"""

   qual = 'single'
   
   # Input arguments:
   pp = JEN_inarg.inarg2pp(inarg, 'MG_JEN_lsm::add_single()', version='10feb2006',
                           description=add_single.__doc__)

   JEN_inarg.nest(pp, MG_JEN_Sixpack.newstar_source(_getdefaults=True, _qual=qual))

   if JEN_inarg.getdefaults(pp): return JEN_inarg.pp2inarg(pp)
   if not JEN_inarg.is_OK(pp): return False
   funcname = JEN_inarg.localscope(pp)
   savefile = '<savefile>'                         # place-holder

   pp1 = MG_JEN_Sixpack.newstar_source(_getpp=True, _qual=qual)
   RA0 = pp1['RA']
   Dec0 = pp1['Dec']

   # Make an automatic .lsm file-name:
   savefile = str(int(100*RA0))+'+'+str(int(100*Dec0))
   savefile += '_single'
   savefile += '.lsm'

   # Create the source defined by pp:
   Sixpack = MG_JEN_Sixpack.newstar_source(ns, _inarg=pp, _qual=qual)

   # Compose the sixpack before adding it to the lsm:
   Sixpack.sixpack(ns)
   Sixpack.display()
   lsm.add_sixpack(sixpack=Sixpack)

   # Finished: Return the suggested .lsm savefile name:
   return savefile


#--------------------------------------------------------------------------------

def add_double (ns=None, Sixpack=None, lsm=None, **inarg):
   """Add a double test-source (Sixpack) to the given lsm"""

   qual = 'double'
   qual1 = qual+'_1'
   qual2 = qual+'_2'
   
   # Input arguments:
   pp = JEN_inarg.inarg2pp(inarg, 'MG_JEN_lsm::add_double()', version='10feb2006',
                           description=add_double.__doc__)

   JEN_inarg.nest(pp, MG_JEN_Sixpack.newstar_source(_getdefaults=True, _qual=qual1))
   JEN_inarg.nest(pp, MG_JEN_Sixpack.newstar_source(_getdefaults=True, _qual=qual2))
   JEN_inarg.define(pp, 'dRA', 20, choice=[],    
                    help='distance of 2nd source in RA (arcmin)')
   JEN_inarg.define(pp, 'dDec', 20, choice=[],    
                    help='distance of 2nd source in Dec (arcmin)')

   if JEN_inarg.getdefaults(pp): return JEN_inarg.pp2inarg(pp)
   if not JEN_inarg.is_OK(pp): return False
   funcname = JEN_inarg.localscope(pp)
   savefile = '<savefile>'                         # place-holder

   pp1 = MG_JEN_Sixpack.newstar_source(_getpp=True, _qual=qual1)
   RA0 = pp1['RA']
   Dec0 = pp1['Dec']

   # Put the first source at its own position:
   punit = qual1
   Sixpack = MG_JEN_Sixpack.newstar_source(ns, _inarg=pp, _qual=qual1,
                                           punit=punit, RA=RA0, Dec=Dec0) 
   Sixpack.sixpack(ns)
   Sixpack.display()
   lsm.add_sixpack(sixpack=Sixpack)

   # Put the second source at the offset position:
   RA = Dec0 + pp['dRA']*arcmin2rad()
   Dec = Dec0 + pp['dDec']*arcmin2rad()
   punit = qual2
   Sixpack = MG_JEN_Sixpack.newstar_source(ns, _inarg=pp, _qual=qual2,
                                           punit=punit, RA=RA, Dec=Dec)
   Sixpack.sixpack(ns)
   Sixpack.display()
   lsm.add_sixpack(sixpack=Sixpack)

   # Make an automatic .lsm file-name:
   savefile = str(int(100*RA0))+'+'+str(int(100*Dec0))
   savefile += '_double'
   savefile += '_'+str(pp['dRA'])+'_'+str(pp['dDec'])
   savefile += '.lsm'

   # Finished: Return the suggested .lsm savefile name:
   return savefile



#--------------------------------------------------------------------------------

def add_grid (ns=None, lsm=None, **inarg):
   """Add a rectangular grid of identical test-sources to the given lsm"""

   qual='grid'

   # Input arguments:
   pp = JEN_inarg.inarg2pp(inarg, 'MG_JEN_lsm::add_grid()', version='10feb2006',
                           description=add_grid.__doc__)

   JEN_inarg.define(pp, 'nRA2', 1, choice=[0,1,2,3],   
                    help='(half) nr of sources in RA direction')
   JEN_inarg.define(pp, 'nDec2', 1, choice=[0,1,2,3],   
                    help='(half) nr of sources in DEC direction')
   JEN_inarg.define(pp, 'dRA', 20, choice=[5,10,20],    
                    help='RA grid spacing (arcmin)')
   JEN_inarg.define(pp, 'dDec', 20, choice=[5,10,20],    
                    help='Dec grid spacing (arcmin)')
   JEN_inarg.define(pp, 'taper', 1.0, choice=[0.5,1,2,5,10,100,None],    
                    help='Scale (degr) of gaussian FOV taper')
   JEN_inarg.define(pp, 'relpos', 'trq',
                    choice=['center','top','bottom','left','right',
                            'tlq','trq','blq','brq'],    
                    help='Relative position w.r.t. the nominal punit (RA,Dec)')

   JEN_inarg.nest(pp, MG_JEN_Sixpack.newstar_source(_getdefaults=True, _qual=qual))
 
   if JEN_inarg.getdefaults(pp): return JEN_inarg.pp2inarg(pp)
   if not JEN_inarg.is_OK(pp): return False
   funcname = JEN_inarg.localscope(pp)
   savefile = '<savefile>'                         # place-holder

   # Get the internal argument-record for .newstar_source():
   pp1 = MG_JEN_Sixpack.newstar_source(_getpp=True, _inarg=pp, _qual=qual)
   RA0 = pp1['RA']
   Dec0 = pp1['Dec']
   punit = pp1['punit']

   rpos = pp['relpos']
   r2 = pp['nRA2']*pp['dRA']*arcmin2rad()
   d2 = pp['nDec2']*pp['dDec']*arcmin2rad()
   ii = range(-pp['nRA2'],pp['nRA2']+1)
   jj = range(-pp['nDec2'],pp['nDec2']+1)
   if rpos=='center':                              # centered
      pass                                         # ....
   elif rpos=='top':                     
      jj = range(0,2*pp['nDec2']+1)
   elif rpos=='bottom':                     
      jj = range(-2*pp['nDec2'],1)
   elif rpos=='left':
      ii = range(0,2*pp['nRA2']+1)
   elif rpos=='right':
      ii = range(-2*pp['nRA2'],1)
   elif rpos=='tlq':                               # top-left quarter
      ii = range(0,2*pp['nRA2']+1)
      jj = range(0,2*pp['nDec2']+1)
   elif rpos=='trq':                               # top-right quarter
      ii = range(-2*pp['nRA2'],1)
      jj = range(0,2*pp['nDec2']+1)
   elif rpos=='blq':                               # bottom-left quarter
      ii = range(0,2*pp['nRA2']+1)
      jj = range(-2*pp['nDec2'],1)
   elif rpos=='brq':                               # bottom-right quarter
      ii = range(-2*pp['nRA2'],1)
      jj = range(-2*pp['nDec2'],1)
   ii.reverse()                                    # RA increases to the left

   # Make an automatic .lsm file-name:
   savefile = str(int(100*RA0))+'+'+str(int(100*Dec0))
   savefile += '_'+str(punit)
   savefile += '_grid'+str(1+2*pp['nRA2'])+'x'+str(1+2*pp['nDec2'])
   savefile += '_'+str(pp['dRA'])+'x'+str(pp['dDec'])
   savefile += '_'+str(pp['relpos'])
   if pp['taper']: savefile += '_'+str(int(10*pp['taper']))
   savefile += '.lsm'

   # Create the sources defined by pp:
   for i in ii:
      RA = RA0 + i*pp['dRA']*arcmin2rad()
      for j in jj:
         Dec = Dec0 + j*pp['dDec']*arcmin2rad()
         flux_att = att(RA-RA0, Dec-Dec0, pp['taper'], trace=False)
         punit = 'grid:'+str(i)+':'+str(j)
         Sixpack = MG_JEN_Sixpack.newstar_source(ns, _inarg=pp, _qual=qual,
                                                 flux_att=flux_att,
                                                 punit=punit, RA=RA, Dec=Dec)
         # Compose the sixpack before adding it to the lsm:
         Sixpack.sixpack(ns)
         # lsm.add_sixpack(sixpack=Sixpack,ns=ns)
         lsm.add_sixpack(sixpack=Sixpack)

   # Finished: Return the suggested .lsm savefile name:
   return savefile



#--------------------------------------------------------------------------------

def add_spiral (ns=None, lsm=None, **inarg):
   """Add a spiral pattern of identical test-sources to the given lsm"""

   qual = 'spiral'

   # Input arguments:
   pp = JEN_inarg.inarg2pp(inarg, 'MG_JEN_lsm::add_spiral()', version='10feb2006',
                           description=add_spiral.__doc__)

   JEN_inarg.define(pp, 'nr_of_sources', 5, choice=[2,3,4,5,10],   
                    help='nr of sources')
   JEN_inarg.define(pp, 'rstart', 20, choice=[1,2,5,10,20,50,100],   
                    help='start position radius (arcmin)')
   JEN_inarg.define(pp, 'astart', 0, choice=[0,30,45,90,180,270],   
                    help='start position angle (deg)')
   JEN_inarg.define(pp, 'rmult', 1.1, choice=[1.01,1.1,1.2,1.5,2],    
                    help='radius multiplication factor')
   JEN_inarg.define(pp, 'ainc', 10, choice=[10,20,30,45,90,180,360,0],    
                    help='position angle increment (deg)')
   JEN_inarg.define(pp, 'taper', 1.0, choice=[0.5,1,2,5,10,100,None],    
                    help='Scale (degr) of gaussian FOV taper')

   JEN_inarg.nest(pp, MG_JEN_Sixpack.newstar_source(_getdefaults=True, _qual=qual))

   if JEN_inarg.getdefaults(pp): return JEN_inarg.pp2inarg(pp)
   if not JEN_inarg.is_OK(pp): return False
   funcname = JEN_inarg.localscope(pp)
   savefile = '<savefile>'                         # place-holder

   # Get the internal argument-record for .newstar_source():
   pp1 = MG_JEN_Sixpack.newstar_source(_getpp=True, _inarg=pp, _qual=qual)
   RA0 = pp1['RA']
   Dec0 = pp1['Dec']
   punit = pp1['punit']

   # Make an automatic .lsm file-name:
   savefile = str(int(100*RA0))+'+'+str(int(100*Dec0))
   savefile += '_'+str(punit)
   savefile += '_spiral'+str(pp['nr_of_sources'])
   savefile += '_r'+str(pp['rstart'])
   savefile += '_a'+str(pp['astart'])
   if pp['taper']: savefile += '_t'+str(int(10*pp['taper']))
   savefile += '.lsm'

   # Create the sources defined by pp:
   r = 0.0
   a = 0.0
   for i in range(pp['nr_of_sources']):
      RA = RA0 + r*cos(a)
      Dec = Dec0 + r*sin(a)
      flux_att = att(RA-RA0, Dec-Dec0, pp['taper'])
      punit = 'spiral:'+str(i)
      Sixpack = MG_JEN_Sixpack.newstar_source(ns, _inarg=pp, _qual=qual,
                                              flux_att=flux_att,
                                              punit=punit, RA=RA, Dec=Dec)
      # Compose the sixpack before adding it to the lsm:
      Sixpack.sixpack(ns)
      lsm.add_sixpack(sixpack=Sixpack)

      # Calculate the position of the next source:
      if i==0:
         r = pp['rstart']*arcmin2rad()
         a = pp['astart']*deg2rad()
      else:
         r *= pp['rmult']
         a += pp['ainc']*deg2rad()

   # Finished: Return the suggested .lsm savefile name:
   return savefile






#================================================================================
#================================================================================
#================================================================================
# Predefined inarg records:
#================================================================================


def predefine_inargs():
   """Modify the default inarg record (MG) to predefined inarg record files"""
   global MG
   print '\n** Predefining',MG['script_name'],'inarg records...\n'
   lsm_single(deepcopy(MG), trace=True)
   lsm_double(deepcopy(MG), trace=True)
   lsm_grid(deepcopy(MG), trace=True)
   lsm_spiral(deepcopy(MG), trace=True)
   print '\n** Predefined',MG['script_name'],'inarg records (incl. protected)\n'
   return True

#--------------------------------------------------------------------

def lsm_single(inarg, trace=True):
   """Predefined inarg record for adding a single test-source to an LSM."""
   filename = 'MG_JEN_lsm_single'
   if trace: print '\n** predefine inarg record:',filename
   JEN_inarg.specific(inarg, lsm_single.__doc__)
   JEN_inarg.modify(inarg,
                    # input_LSM='lsm_current.lsm',
                    save_as_current=True,
                    test_pattern='single',
                    _JEN_inarg_option=dict(trace=trace))     
   JEN_inarg.save(inarg, filename, trace=trace)
   JEN_inarg.save(inarg, filename, protected=True, trace=trace)
   return True

#--------------------------------------------------------------------

def lsm_double(inarg, trace=True):
   """Predefined inarg record for adding two (different) test-sources to an LSM"""
   filename = 'MG_JEN_lsm_double'
   if trace: print '\n** predefine inarg record:',filename
   JEN_inarg.specific(inarg, lsm_double.__doc__)
   JEN_inarg.modify(inarg,
                    # input_LSM='lsm_current.lsm',
                    save_as_current=True,
                    test_pattern='double',
                    _JEN_inarg_option=dict(trace=trace))     
   JEN_inarg.callback_punit(inarg, 'unpol', qual='double_1')
   JEN_inarg.callback_punit(inarg, 'QU', qual='double_2')
   JEN_inarg.save(inarg, filename, trace=trace)
   JEN_inarg.save(inarg, filename, protected=True, trace=trace)
   return True

#--------------------------------------------------------------------

def lsm_grid(inarg, trace=True):
   """Predefined inarg record for adding a rectangular grid of test-sources to an LSM"""
   filename = 'MG_JEN_lsm_grid'
   if trace: print '\n** predefine inarg record:',filename
   JEN_inarg.specific(inarg, lsm_grid.__doc__)
   JEN_inarg.modify(inarg,
                    # input_LSM='lsm_current.lsm',
                    save_as_current=True,
                    test_pattern='grid',
                    _JEN_inarg_option=dict(trace=trace))     
   JEN_inarg.save(inarg, filename, trace=trace)
   JEN_inarg.save(inarg, filename, protected=True, trace=trace)
   return True

#--------------------------------------------------------------------

def lsm_spiral(inarg, trace=True):
   """Predefined inarg record for adding a spiral patternof test-sources to an LSM"""
   filename = 'MG_JEN_lsm_spiral'
   if trace: print '\n** predefine inarg record:',filename
   JEN_inarg.specific(inarg, lsm_spiral.__doc__)
   JEN_inarg.modify(inarg,
                    # input_LSM='lsm_current.lsm',
                    save_as_current=True,
                    test_pattern='spiral',
                    _JEN_inarg_option=dict(trace=trace))     
   JEN_inarg.save(inarg, filename, trace=trace)
   JEN_inarg.save(inarg, filename, protected=True, trace=trace)
   return True







#********************************************************************************
#********************************************************************************
#************* PART III: MG control record (may be edited here)******************
#********************************************************************************
#********************************************************************************

#----------------------------------------------------------------------------------------------------
# Intialise the MG control record with some overall arguments 
#----------------------------------------------------------------------------------------------------

def description ():
    """MG_JEN_lsm.py is used to create (or modify) Local Sky Models by hand.
    The result may be inspected via the LSM GUI, which pops up automatically.
    The new LSM may be saved in a user-defined .lsm file, for later use. 
    
    It can generate the following patterns of test-sources (in either a new
    or an existing LSM):
      -) A single source at an arbitrary position.
      -) Two sources (they may be different).
      -) A rectangular grid of identical sources.
      -) A spiral pattern of identical sources.
    The sources have NEWSTAR parametrisation. The user may choose from a small
    collection of predefined sources, whose parameters (position, flux, SI, RM)
    may then be edited.
    The larger patterns may have a kind of 'primary beam' applied to them,
    i.e. a gaussian that attenuates their flux as a function of distance to
    the central position (of the pattern!)
    """
    return True


def default_inarg ():
    """This default inarg record does nothing specific in its present form.
    Of course it may be edited to create (or modify) a wide range of Local
    Sky Models. But it is often more convenient to use one of the predefined
    inarg records for this TDL script as a starting point (use Open).

    However, this default inarg is useful for generating various standard
    Local Sky Models. Just press the Proceed button, and select any of the
    TDL execute options."""
    return True


#-------------------------------------------------------------------------

MG = JEN_inarg.init('MG_JEN_lsm', description=description.__doc__,
                    inarg_specific=default_inarg.__doc__)
JEN_inarg.define (MG, 'last_changed', 'd30jan2006', editable=False)

JEN_inarg.define (MG, 'input_LSM', None, browse='*.lsm',
                  choice=['lsm_current.lsm','3c343_nvss.lsm',
                          'abel963.lsm','D1.lsm',None],
                  help='(file)name of the Local Sky Model to be used')

JEN_inarg.define (MG, 'save_as_current', tf=False,
                  help='Save the new LSM afterwards as lsm_current.lsm')

JEN_inarg.define (MG, 'saveAs', '<automatic>', browse='*.lsm',
                  choice=['<automatic>',None,'lsm_current.lsm'],
                  help='Save the (modified) LSM afterwards as...')

# Optional: add test-source(s) to the given lsm:
JEN_inarg.define (MG, 'test_pattern', None,
                  choice=[None,'single','double','grid','spiral'],
                  help='pattern of test-sources to be generated')
JEN_inarg.nest(MG, add_single(_getdefaults=True))
JEN_inarg.nest(MG, add_double(_getdefaults=True))
JEN_inarg.nest(MG, add_grid(_getdefaults=True))
JEN_inarg.nest(MG, add_spiral(_getdefaults=True))




#-------------------------------------------------------------------------
# The forest state record will be included automatically in the tree.
# Just assign fields to: Settings.forest_state[key] = ...

MG_JEN_forest_state.init(MG)

# NB: Using False here does not work, because it regards EVERYTHING
#        as an orphan, and deletes it.....!?
# Settings.orphans_are_roots = True




#********************************************************************************
#********************************************************************************
#***************** PART IV: Required test/demo function *************************
#********************************************************************************
#********************************************************************************


def _tdl_predefine (mqs, parent, **kwargs):
   res = True
   if parent:
      QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
      callback = dict()
      callback['0'] = dict(prompt='predefine inargs', callback=predefine_inargs)
      try:
         igui = JEN_inargGui.ArgBrowser(parent, callback=callback)
         igui.input(MG, set_open=False)
         res = igui.exec_loop()
         if res is None:
            raise RuntimeError("Cancelled by user");
      finally:
         QApplication.restoreOverrideCursor()
   return res




#**************************************************************************

def _define_forest (ns, **kwargs):

   # The MG may be passed in from _tdl_predefine():
   # In that case, override the global MG record.
   global MG
   if len(kwargs)>1: MG = kwargs
   
   # Perform some common functions, and return an empty list (cc=[]):
   cc = MG_JEN_exec.on_entry (ns, MG)

   # Start with an empty lsm:
   global lsm 
   lsm = LSM()
   display_lsm = False
   savefile = '<savefile>'

   # Optional: use an existing lsm
   print '\n** MG[input_LSM] =',MG['input_LSM'],'\n'
   if MG['input_LSM']:
      lsm.load(MG['input_LSM'],ns)
      display_lsm = True
   else:
      lsm.setNodeScope(ns)



   # Optional: add one or more test-sources to the lsm:
   print '\n** MG[test_pattern] =',MG['test_pattern'],'\n'
   if isinstance(MG['test_pattern'], str):
      display_lsm = True
      if MG['test_pattern']=='single':
         savefile = add_single(ns, lsm=lsm, _inarg=MG)
      elif MG['test_pattern']=='double':
         savefile = add_double(ns, lsm=lsm, _inarg=MG)
      elif MG['test_pattern']=='grid':
         savefile = add_grid(ns, lsm=lsm, _inarg=MG)
      elif MG['test_pattern']=='spiral':
         savefile = add_spiral(ns, lsm=lsm, _inarg=MG)
      else:
         print 'test_pattern not recognised:',MG['test_pattern']


   # Save the lsm as 'lsm_current', for continuity:
   if MG['save_as_current']:
      r = lsm.save('lsm_current.lsm')
      print '\n** lsm.save(lsm_current.lsm) ->',r,'\n'

   # Save the (possibly modified) lsm under a different name:
   if MG['saveAs']:
      if MG['saveAs']=='<automatic>':
         MG['saveAs'] = savefile              # use automaticallay generated name
      r = lsm.save(MG['saveAs'])
      print '\n** lsm.save(saveAs',MG['saveAs'],') ->',r,'\n'

   # Display the current lsm AFTER saving (so we have the new name)
   # NB: The program does NOT wait for the control to be handed back!
   if display_lsm:
      lsm.display()

   
   # Make the trees of all the lsm punits: 
   radec = []                                 # for collect_radec()
   if True:
      plist = lsm.queryLSM(count=1000)
      print '\n** plist =',type(plist),len(plist)
      bb = []
      for i in range(len(plist)):
         punit = plist[i] 
         Sixpack = punit.getSP()              # get_Sixpack()
         print '-',i,':',Sixpack.label(),

         # Display subtree:
         if i<5:
            print 'make_bookmark',
            cc.append(MG_JEN_Sixpack.make_bookmark(ns, Sixpack, radec=radec))
         else:
            print 'make_bundle',
            cc.append(MG_JEN_Sixpack.make_bundle(ns, Sixpack, radec=radec))

         # Actions depending on the type of source:
         if Sixpack.ispoint():                # point source (Sixpack object)
            print 'point-source'
            pass
         else:	                              # patch (not a Sixpack object!)
            print 'patch...'
            node = Sixpack.root()             # ONLY valid for a patch...#
            cc.append(node)                   # ....?

   # Finished: 
   MG_JEN_Sixpack.collect_radec(radec, ns=ns) # Make a radec root node (tidier)
   return MG_JEN_exec.on_exit (ns, MG, cc)










#********************************************************************************
#********************************************************************************
#*****************  PART V: Forest execution routines ***************************
#********************************************************************************
#********************************************************************************


def _test_forest (mqs, parent):
    """Execute the forest with a default domain"""
    return MG_JEN_exec.meqforest (mqs, parent)
    # return MG_JEN_exec.meqforest (mqs, parent, domain='21cm',nfreq=10, ntime=5)


def _tdl_job_nvss_3c343 (mqs, parent):
   """Create lsm(s) from nvss txt-file(s)"""
   ns = NodeScope()
   return nvss_3c343(ns)

def _tdl_job_nvss_Abell963 (mqs, parent):
   """Create lsm(s) from nvss txt-file(s)"""
   ns = NodeScope()
   return nvss_Abell963(ns)

def _tdl_job_nvss_all (mqs, parent):
   """Create lsms from all available nvss txt-file"""
   ns = NodeScope()
   return nvss_all(ns)

   
def _tdl_job_open_lsm_current (mqs, parent):
   """Open and read the file lsm_current.lsm"""
   ns = NodeScope()
   lsm1 = LSM()
   filename = 'lsm_current.lsm'
   print '\n** created lsm1:',type(lsm1)
   print '\n** before lsm1.load(',filename,', ns):\n'
   r = lsm1.load(filename, ns)
   print '\n** after lsm1.load(',filename,', ns): ->',r,'\n'
   plist = lsm1.queryLSM(count=1000)
   print '\n** lsm1.query():  -> plist =',type(plist),len(plist)
   lsm1.display()
   print '\n** after lsm1.display():\n'
   return True

   

#----------------------------------------------------------------
# Obsolete?
#----------------------------------------------------------------

if False:
   def _tdl_job_lsm_query (mqs, parent):
      """Read the 3 brightest punits from the lsm"""
      global lsm
      plist = lsm.queryLSM(count=3)
      for pu in plist:
         my_sp = pu.getSP()
         my_sp.display()

   def _tdl_job_dirdir (mqs, parent):
      """Show the contents(dir) of lsm and punit"""
      global lsm
      print '\n** dir(lsm):\n',dir(lsm)
      plist = lsm.queryLSM(count=1)
      print '\n** dir(punit):\n',dir(plist[0])

   def _tdl_job_display (mqs, parent):
      global lsm
      # set the MQS proxy of LSM
      lsm.setMQS(mqs)
      cells = MG_JEN_exec.make_cells (domain='21cm',nfreq=10, ntime=5)
      lsm.setCells(cells)
      # query the MeqTrees using these cells
      lsm.updateCells()
      # display results
      lsm.display()





#********************************************************************************
#********************************************************************************
#******************** PART VI: Standalone test routines *************************
#********************************************************************************
#********************************************************************************


if __name__ == '__main__':
   print '\n*******************\n** Local test of:',MG['script_name'],':\n'

   # Generic test:
   if 0:
       MG_JEN_exec.without_meqserver(MG['script_name'], callback=_define_forest, recurse=3)

   # Various specific tests:
   ns = NodeScope()

   if 0:
      igui = JEN_inargGui.ArgBrowser()
      igui.input(MG, set_open=False)
      igui.launch()
       

   if 0:
      lsm = lsm_343(ns)
      plist = lsm.queryLSM(count=3)
      for pu in plist:
         my_sp = pu.getSP()
         my_sp.display()

   if 0:
      lss = lsmSet()
      lss.display()
      lss.append()
      lss.append()
      lss.display()

   if 1:
      att (0, 0, None, trace=True)
      att (0, 0, 57.0, trace=True)
      att (1, 0, 57.0, trace=True)
      att (0, 1, 57.0, trace=True)
      att (1, 1, 57.0, trace=True)


   if 0:
      MG_JEN_exec.display_object (MG, 'MG', MG['script_name'])
      # MG_JEN_exec.display_subtree (rr, MG['script_name'], full=1)
   print '\n** End of local test of:',MG['script_name'],'\n*******************\n'
       
#********************************************************************************
#********************************************************************************




