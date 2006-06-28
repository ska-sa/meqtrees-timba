from Timba.TDL import *
from Timba.Meq import meq
from Utils import *
import Jones

class Direction (Parameterization):
  """A Direction represents a direction on the sky.
  name may be None, this usually identifies the phase centre.
  If constant=True, MeqConstants are used for the direction components, 
  else MeqParms.
  """;
  def __init__(self,ns,name,ra,dec,
               constant=False,
               create_nodes=True,
               parm_options=record(node_groups='Parm'),
               quals=[],kwquals={}):
    Parameterization.__init__(self,ns,name,parm_options=parm_options,
                              quals=quals,kwquals=kwquals);
    self._constant = constant;
    if constant:
      self._ra = self._const_node('ra',ra);
      self._dec = self._const_node('dec',dec);
    else:
      self._create_polc('ra',ra);
      self._create_polc('dec',dec);
    
  def radec (self):
    """Returns ra-dec two-pack for this direction""";
    radec = self.ns.radec;
    if not radec.initialized():
      if self._constant:
        radec << Meq.Composer(self._ra,self._dec);
      else:
        radec << Meq.Composer(self._parm("ra"),self._parm("dec"));
    return radec;
    
  def lmn (self,radec0):
    """Returns LMN three-pack for this component, given an reference
    direction radec0.
    Qualifiers from radec0 are added in.""";
    # create coordinate nodes, add in qualifiers of radec0 since
    # we may have different LMN sets for different directions
    lmn = self.ns.lmn.qadd(radec0);
    if not lmn.initialized():
      lmn << Meq.LMN(radec_0=radec0,radec=self.radec());
    return lmn;
    
  def n (self,radec0):
    """Returns 'n' coordinate for this source and relative to radec0
    Qualifiers from radec0 are added in.""";
    lmn = self.lmn(radec0);
    n = self.ns.n.qadd(radec0);
    if not n.initialized():
      n << Meq.Selector(lmn,index=2);
    return n;
    
  def lmn_1 (self,radec0):
    """Returns LMN-1 three-pack for this component, given an reference
    direction radec0.
    Qualifiers from radec0 are added in.""";
    lmn_1 = self.ns.lmn_minus1.qadd(radec0);
    if not lmn_1.initialized():
      lmn_1 << Meq.Paster(self.lmn(radec0),self.n(radec0)-1,index=2);
    return lmn_1;
    
  def KJones (self,array,radec0):
    """makes and returns a series of Kjones (phase shift) nodes
    for this direction, given a reference direction radec0.
    Return value is an under-qualified node, which should be 
    qualified with a station.
    """;
    Kj = self.ns.K.qadd(radec0);
    stations = array.stations();
    if not Kj(stations[0]).initialized():
      # use L,M,(N-1) for lmn. NB: this could be made an option in the future
      lmn_1 = self.lmn_1(radec0);
      uvw = array.uvw(radec0);
      for sta in stations:
        Kj(sta) << Meq.VisPhaseShift(lmn=lmn_1,uvw=uvw(sta));
    return Kj;

  def make_phase_shift (self,vis,vis0,array,radec0):
    """phase-shifts visibilities given by vis0(sta1,sta2) from dir0 to the
    given direction. Shifted visibilities are created as vis(sta1,sta2).
    """;
    # if direction is the same, use an Identity transform
    if self.radec() is radec0: 
      for sta1,sta2 in array.ifrs():
        vis(sta1,sta2) << Meq.Identity(vis0(sta1,sta2));
    # else apply KJones
    else:
      Kj = self.KJones(array,radec0);
      Jones.apply_corruption(vis,vis0,Kj,array.ifrs());
