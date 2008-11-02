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
from Parameterization import *
import Jones
import Context
from math import cos,sin,sqrt

class Direction (Parameterization):
  """A Direction represents an absolute direction on the sky, in ra,dec (radians).
  'name' may be None, this usually identifies the phase centre.
  A direction may be static, in which case it is known and fixed at compile-time.
  """;
  def __init__(self,ns,name,ra,dec,static=False,
               quals=[],kwquals={}):
    Parameterization.__init__(self,ns,name,
                              quals=quals,kwquals=kwquals);
    self._add_parm('ra',ra,tags="direction solvable");
    self._add_parm('dec',dec,tags="direction solvable");
    if static and self._is_constant('ra') and self._is_constant('dec'):
      self.static = ra,dec;
      self.static_lmn = {};
    else:
      self.static = None;
    
  def radec (self):
    """Returns ra-dec 2-vector node for this direction.
    """;
    radec = self.ns.radec;
    if not radec.initialized():
      ra = self._parm('ra');
      dec = self._parm('dec');
      radec << Meq.Composer(ra,dec);
    return radec;
    
  def radec_static (self):
    """Returns ra-dec tuple for this direction if static, None if not.
    """;
    return self.static;
    
  def lmn (self,dir0=None):
    """Returns LMN 3-vector node for this direction, given a reference
    direction dir0, or using the global phase center if not supplied.
    Qualifiers from dir0 are added in.
    All other lmn-related methods below call on this one to get
    the basic lmn 3-vector.
    """;
    dir0 = Context.get_dir0(dir0);
    lmn = self.ns.lmn(*dir0._quals,**dir0._kwquals);
    if not lmn.initialized():
      if self is dir0:
        lmn << Meq.Constant(value=Timba.array.array((0.,0.,1.)));
      else:
        lmnst = self.lmn_static(dir0);
        if lmnst:
          lmn << Meq.Constant(value=Timba.array.array(lmnst));
        else:
          lmn << Meq.LMN(radec_0=dir0.radec(),radec=self.radec());
    return lmn;
  
  def lmn_static (self,dir0=None):
    """Returns static LMN tuple, given a reference direction dir0, or using the global phase 
    center if not supplied. 
    Both this direction and the reference direction must be static, otherwise None is returned.
    """;
    dir0 = Context.get_dir0(dir0);
    if not self.static or not dir0.static:
      return None;
    ra0,dec0 = dir0.radec_static();
    # see if we have already computed this lmn
    lmn = self.static_lmn.get((ra0,dec0),None);
    if lmn is None:
      ra,dec = self.radec_static();
      l = cos(dec) * sin(ra-ra0);
      m = sin(dec) * cos(dec0) - cos(dec) * sin(dec0) * cos(ra-ra0);
      n = sqrt(1 - l*l - m*m );
      lmn = self.static_lmn[(ra0,dec0)] = l,m,n;
    return lmn;
    
  def _lmn_component (self,name,dir0,index):
    """Helper method for below, returns part of the LMN vector.""";
    lmn = self.lmn(dir0);
    comp = self.ns[name].qadd(lmn);  # use ns0: all qualifiers are in lmn already
    # if we used self.ns, we'd have duplicate qualifiers
    if not comp.initialized():
      comp << Meq.Selector(lmn,index=index,multi=True);
    return comp;

  def lm (self,dir0=None):
    """Returns an LM 2-vector node for this direction. All args are as
    per lmn().""";
    lmnst = self.lmn_static(dir0);
    if lmnst:
      lm = self.ns.lm(*dir0._quals,**dir0._kwquals);
      return lm << Meq.Constant(value=Timba.array.array(lmnst[0:2]));
    else:
      return self._lmn_component('lm',dir0,[0,1]);
  def l (self,dir0=None):
    """Returns an L node for this direction. All args are as per lmn().""";
    return self._lmn_component('l',dir0,0);
  def m (self,dir0=None):
    """Returns an M node for this direction. All args are as per lmn().""";
    return self._lmn_component('m',dir0,1);
  def n (self,dir0=None):
    """Returns an N node for this direction. All args are as per lmn().""";
    return self._lmn_component('n',dir0,2);
    
  def lmn_1 (self,dir0=None):
    """Returns L,M,N-1 3-vector node for this direction.
     All args are as per lmn().""";
    dir0 = Context.get_dir0(dir0);
    lmn_1 = self.ns.lmn_minus1(*dir0._quals,**dir0._kwquals);
    if not lmn_1.initialized():
      lmnst = self.lmn_static(dir0);
      if lmnst:
        lmn_1 << Meq.Constant(value=Timba.array.array((lmnst[0],lmnst[1],lmnst[2]-1)));
      else:
        lmn = self.lmn(dir0);
        lmn_1 << Meq.Paster(lmn,self.n(dir0)-1,index=2);
    return lmn_1;
    
  def KJones (self,array=None,dir0=None,smearing=False):
    """makes and returns a series of Kjones (phase shift) nodes
    for this direction, given a reference direction dir0, or using
    the global phase center if not supplied.
    Return value is an under-qualified node K, which should be 
    qualified with a station index.
    If 'smearing' is True, then uses an alternative implementation of K -- 
    makes a separate node K('arg'), which holds the complex argument of K. This argument node
    can be used to compute smearing factors.
    """;
    # if direction is same, K is identity for all stations
    if self is dir0:
      Kj = self.ns.K << 1;
      return lambda p: Kj;
    else:
      Kj = self.ns.K;
      if dir0:
        Kj = Kj.qadd(dir0.radec());
      if smearing:
        Kjarg = Kj('arg');
      array = Context.get_array(array);
      stations = array.stations();
      if not Kj(stations[0]).initialized():
        # use L,M,(N-1) for lmn. NB: this could be made an option in the future
        lmn_1 = self.lmn_1(dir0);
        uvw = array.uvw(dir0);
        for p in stations:
          if smearing:
            Kj(p) << Meq.Polar(1,
              Kjarg(p) << Meq.VisPhaseShiftArg(lmn=lmn_1,uvw=uvw(p)));
          else:
            Kj(p) << Meq.VisPhaseShift(lmn=lmn_1,uvw=uvw(p));
      return Kj;

  def make_phase_shift (self,vis,vis0,array=None,dir0=None,smearing=False):
    """phase-shifts visibilities given by vis0(p,q) from dir0 
    (the global phase center by default) to the given direction. 
    Shifted visibilities are created as vis(p,q).
    """;
    dir0 = Context.get_dir0(dir0);
    array = Context.get_array(array);
    # if direction is the same, use an Identity transform
    if self is dir0:
      for p,q in array.ifrs():
        vis(p,q) << Meq.Identity(vis0(p,q));
    # else apply KJones
    else:
      Kj = self.KJones(array=array,dir0=dir0,smearing=smearing);
      if smearing:
        Karg = Kj('arg');
        Ksmear = Kj('smear');
        vis1 = vis('unsmeared');
        Jones.apply_corruption(vis1,vis0,Kj,array.ifrs());
        for p,q in array.ifrs():
          sf = Ksmear(p,q) << Meq.TFSmearFactor(Karg(p),Karg(q));
          vis(p,q) << sf*vis1(p,q);
      else:
        Jones.apply_corruption(vis,vis0,Kj,array.ifrs());