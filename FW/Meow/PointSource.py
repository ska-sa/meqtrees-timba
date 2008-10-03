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
from SkyComponent import *
import Jones
import Context
  
STOKES = ("I","Q","U","V");

class PointSource(SkyComponent):
  def __init__(self,ns,name,direction,
               I=0.0,Q=None,U=None,V=None,
               spi=None,freq0=None,
               RM=None):
    """Creates a PointSource with the given name; associates with 
    direction. 
    'direction' is a Direction object or a (ra,dec) tuple
    'I' is I flux (constant, node, or Meow.Parm)
    Optional arguments:
      'Q','U','V' are constants, nodes, or Meow.Parms. If none of the three 
          are supplied, an unpolarized source representation is used.
      'spi' and 'freq0' are constants, nodes or Meow.Parms. If both are
          supplied, a spectral index is added, otherwise the fluxes are
          constant in frequency.
      'RM' is rotation measure (constants, nodes or Meow.Parms). If None,
          no intrinsic rotation measure is used.
    """;
    SkyComponent.__init__(self,ns,name,direction);
    self._add_parm('I',I,tags="flux");
    # check if polarized
    # NB: disable for now, as Sink can't handle scalar results
    # self._polarized = True;
    self._polarized = Q is not None or U is not None or V is not None or RM is not None;
    self._add_parm('Q',Q or 0.,tags="flux pol");
    self._add_parm('U',U or 0.,tags="flux pol");
    self._add_parm('V',V or 0.,tags="flux pol");
    # see if a spectral index is present (freq0!=0 then), create polc
    self._has_spi = spi is not None or freq0 is not None;
    if self._has_spi:
      self._add_parm('spi',spi or 0.,tags="spectrum");
      # for freq0, use placeholder node for first MS frequency,
      # unless something else is specified 
      self._add_parm('spi_fq0',freq0 or (ns.freq0 ** 0),tags="spectrum");
    # see if intrinsic rotation measure is present
    self._has_rm = RM is not None;
    if self._has_rm:
      self._add_parm("RM",RM,tags="pol");
    # flag: flux is fully defined by constants
    self._constant_flux = not self._has_rm and not \
                          [ flux for flux in STOKES if not self._is_constant(flux) ];
      
  def stokes (self,st):
    """Returns flux node for this source. 'st' must be one of 'I','Q','U','V'.
    (This is the flux after RM has been applied, but without spi).
    If flux was defined as a constant, returns constant value, not node!
    """;
    if st not in STOKES:
      raise ValueError,"st: must be one of 'I','Q','U','V'";
    if self._constant_flux:
      return self._get_constant(st);
    # rotation measure rotates Q-U with frequency. So if no RM is given,
    # or if we're just asked for an I or V node, return it as is
    if st == "I" or st == "V" or not self._has_rm:
      return self._parm(st);
    else:
      stokes = self.ns[st+'r'];
      if stokes.initialized():
        return stokes;
      q = self._parm("Q");
      u = self._parm("U");
      # squared wavelength
      freq = self.ns0.freq ** Meq.Freq;
      iwl2 = self.ns0.wavelength2 << Meq.Sqr(2.99792458e+8/freq);
      # rotation node
      farot = self.ns.farot << self._parm("RM")*iwl2;
      cosf = self.ns.cos_farot << Meq.Cos(farot);
      sinf = self.ns.sin_farot << Meq.Sin(farot);
      self.ns.Qr << cosf*q - sinf*u;
      self.ns.Ur << sinf*q + cosf*u;
      return self.ns[st+'r'];
      
  def norm_spectrum (self):
    """Returns spectrum normalized to 1 at the reference frequency.
    Flux should be multiplied by this to get the real spectrum""";
    if not self._has_spi:
      return 1;
    nsp = self.ns.norm_spectrum;
    if not nsp.initialized():
      freq = self.ns0.freq ** Meq.Freq;
      nsp << Meq.Pow(freq/self._parm('spi_fq0'),self._parm('spi'));
    return nsp;
    
  def coherency_elements (self,observation):
    """helper method: returns the four components of the coherency matrix""";
    i,q,u,v = [ self.stokes(st) for st in STOKES ];
    if observation.circular():
      if self._constant_flux:
        return i+v,complex(q,u),complex(q,-u),i-v;
      rr = self.ns.rr ** (self.stokes("I") + self.stokes("V"));
      rl = self.ns.rl ** Meq.ToComplex(self.stokes("Q"),self.stokes("U"));
      lr = self.ns.lr ** Meq.Conj(rl);
      ll = self.ns.ll ** (self.stokes("I") - self.stokes("V"));
      return rr,rl,lr,ll;
    else:
      if self._constant_flux:
        return i+q,complex(u,v),complex(u,-v),i-q;
      xx = self.ns.xx ** (self.stokes("I") + self.stokes("Q"));
      xy = self.ns.xy ** Meq.ToComplex(self.stokes("U"),self.stokes("V"));
      yx = self.ns.yx ** Meq.Conj(xy);
      yy = self.ns.yy ** (self.stokes("I") - self.stokes("Q"));
      return xx,xy,yx,yy;
    
  def coherency (self,observation=None):
    """Returns the coherency matrix for a point source.
    'observation' argument is used to select a linear or circular basis;
    if not supplied, the global context is used.""";
    observation = observation or Context.observation;
    if not observation:
      raise ValueError,"observation not specified in global Meow.Context, or in this function call";
    coh = self.ns.coherency;
    if not coh.initialized():
      # if not polarized, just return I
      if not self._polarized:
        if self._has_spi:
          if self._constant_flux:
            coh << (self.stokes("I")*0.5)*self.norm_spectrum();
          else:
            coh << Meq.Multiply(self.stokes("I"),self.norm_spectrum(),.5);
        else:
          coh << self.stokes("I")*.5;
      else:
        coh_els = self.coherency_elements(observation);
        if self._constant_flux:
          if self._has_spi:
            coh1 = self.ns.coh1 << Meq.Matrix22(*[x*.5 for x in coh_els]);
            coh << coh1*self.norm_spectrum();
          else:
            coh << Meq.Matrix22(*[x*.5 for x in coh_els]);
        else:
          coh1 = self.ns.coh1 << Meq.Matrix22(*coh_els);
          if self._has_spi:
            coh << Meq.Multiply(coh1,self.norm_spectrum(),.5);
          else:
            coh << coh1*.5;
    return coh;

  def make_visibilities (self,nodes,array=None,observation=None,smearing=False,**kw):
    observation = observation or Context.observation;
    # create lambda to return the same coherency at all baselines
    cohnode = lambda p,q: self.coherency(observation);
    # use direction's phase shift method
    self.direction.make_phase_shift(nodes,cohnode,array,observation.phase_center,smearing=smearing);
   
  def is_station_decomposable (self):
    """Check the type -- subclasses are not necessarily decomposable.""";
    return type(self) == PointSource;
  
  def sqrt_coherency (self,observation):
    # Cholesky decomposition of the coherency matrix into 
    # UU*, where U is lower-triangular
    coh = self.ns.sqrt_coh;
    if not coh.initialized():
      # if unpolarized, then matrix is scalar -- simply take the square root
      if not self._polarized:
        flux = self.stokes("I")*0.5*self.norm_spectrum();
        if isinstance(flux,(int,float,complex)):
          coh << math.sqrt(flux);
        else:
          coh << Meq.Sqrt(flux);
      else:
        # circular and linear matrices have the same form, only QUV is swapped around.
        # So the code below forms up the matrix assuming linear polarization, while
        # here for the circular case we simply swap the quv variables around
        if observation.circular():
          i,q,u,v = self.stokes("I"),self.stokes("V"),self.stokes("Q"),self.stokes("U");
        else:
          i,q,u,v = self.stokes("I"),self.stokes("Q"),self.stokes("U"),self.stokes("V");
        # form up matrix
        if self._constant_flux:
          norm = math.sqrt(.5/(i+q));
          c11 = (i+q)*norm;
          c12 = 0;
          c21 = complex(u,-v)*norm;
          c22 = math.sqrt(i**2-q**2-u**2-v**2)*norm;
          if self._has_spi:
            coh1 = self.ns.sqrt_coh1 << Meq.Matrix22(c11,c12,c21,c22);
            coh << coh1*Meq.Sqrt(self.norm_spectrum());
          else:
            coh << Meq.Matrix22(c11,c12,c21,c22);
        else:
          c11 = self.ns.sqrt_coh(1,1) << i+q;
          c12 = 0;
          c21 = self.ns.sqrt_coh(2,1) << Meq.ToComplex(u,-v);
          i2 = self.ns.I2 << Meq.Sqr(i);
          q2 = self.ns.Q2 << Meq.Sqr(q);
          u2 = self.ns.U2 << Meq.Sqr(u);
          v2 = self.ns.V2 << Meq.Sqr(v);
          c22 = self.ns.sqrt_coh(2,2) << Meq.Sqrt(
            self.ns.I2_QUV2 << self.ns.I2 - (self.ns.QUV2 << Meq.Add(q2,u2,v2)) 
          );
          # create unnormalized matrix + normalization term
          self.ns.sqrt_coh1 << Meq.Matrix22(c11,c12,c21,c22);
          norm = self.ns.sqrt_coh_norm << Meq.Sqrt(.5*self.norm_spectrum()/c11);
          # and finally form up product
          coh << norm * self.ns.sqrt_coh1;
    return coh;
  
  def sqrt_visibilities (self,array=None,observation=None,nodes=None):
    self.using_station_decomposition = True;
    observation = Context.get_observation(observation);
    array = Context.get_array(array);
    if nodes is None:
      nodes = self.ns.sqrt_visibility.qadd(observation.radec0());
    stations = array.stations();
    if nodes(stations[0]).initialized():
      return nodes;
    # create decomposition nodes
    sqrtcoh = self.sqrt_coherency(observation);
    # get K jones per station
    if self.direction is observation.phase_center:
      for p in array.stations():
        nodes(p) << Meq.Identity(sqrtcoh);
    # else apply KJones
    else:
      Kj = self.direction.KJones(array=array,dir0=observation.phase_center);
      for p in array.stations():
        nodes(p) << Meq.MatrixMultiply(Kj(p),sqrtcoh);
    return nodes;
