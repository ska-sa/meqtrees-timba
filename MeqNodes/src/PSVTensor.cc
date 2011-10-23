//# PSVTensor.cc: The point source DFT component for a station
//#
//# Copyright (C) 2002-2007
//# ASTRON (Netherlands Foundation for Research in Astronomy)
//# and The MeqTree Foundation
//# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
//#
//# This program is free software; you can redistribute it and/or modify
//# it under the terms of the GNU General Public License as published by
//# the Free Software Foundation; either version 2 of the License, or
//# (at your option) any later version.
//#
//# This program is distributed in the hope that it will be useful,
//# but WITHOUT ANY WARRANTY; without even the implied warranty of
//# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//# GNU General Public License for more details.
//#
//# You should have received a copy of the GNU General Public License
//# along with this program; if not, write to the Free Software
//# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//#
//# $Id: PSVTensor.cc 8270 2011-07-06 12:17:23Z oms $

#include <MeqNodes/PSVTensor.h>
#include <DMI/AID-DMI.h>
#include <MEQ/AID-Meq.h>
#include <MeqNodes/AID-MeqNodes.h>
#include <casa/BasicSL/Constants.h>

namespace Meq {

InitDebugContext(PSVTensor,"PSVTensor");
  
  
using namespace VellsMath;

const HIID child_labels[] = { AidLMN,AidB,AidUVW,
  AidE|1,AidE|1|AidConj,
};
const int num_children = sizeof(child_labels)/sizeof(child_labels[0]);

const double _2pi_over_c = casa::C::_2pi / casa::C::c;

const HIID FNMinus = AidN|AidMinus;
const HIID FNarrowBandLimit = AidNarrow|AidBand|AidLimit;


PSVTensor::PSVTensor()
: TensorFunctionPert(-4,child_labels,3), // first 3 children mandatory, rest are optional
  narrow_band_limit_(.05),n_minus_(1),first_jones_(3)
{
  // dependence on frequency
  const HIID symdeps[] = { AidDomain,AidResolution };
  setActiveSymDeps(symdeps,2);
}

PSVTensor::~PSVTensor()
{}

//##ModelId=400E53550233
void PSVTensor::setStateImpl (DMI::Record::Ref &rec,bool initializing)
{
  TensorFunction::setStateImpl(rec,initializing);
  rec[FNarrowBandLimit].get(narrow_band_limit_,initializing);
  rec[FNMinus].get(n_minus_,initializing);
}

const LoShape shape_3vec(3),shape_2x3(2,3);

// Checks tensor dimensions of a child result to see that they are a per-source tensor
// Valid dimensions are [] (i.e. [1]), [N], [Nx1], [Nx1x1], or [Nx2x2].
void PSVTensor::checkTensorDims (int ichild,const LoShape &shape,int nsrc)
{
  int n = 0;
  FailWhen(shape.size()>3,"child '"+child_labels[ichild].toString()+"': illegal result rank (3 at most expected)");
  if( shape.size() == 0 )
    n = 1;
  else
  {
    n = shape[0];
    if( shape.size() == 2 )
    {
      FailWhen(shape[1]!=1,"child '"+child_labels[ichild].toString()+"': rank-2 result must be of shape Nx1");
    }
    else if( shape.size() == 3 )
    {
      FailWhen(!(shape[1]==1 && shape[2]==1) && !(shape[1]==2 && shape[2]==2),   // Nx1x1 or Nx2x2 result 
          "child '"+child_labels[ichild].toString()+"': rank-3 result must be of shape Nx2x2 or Nx1x1");
    }
  }
  FailWhen(n!=nsrc,"child '"+child_labels[1].toString()+"': first dimension does not match number of sources");
}

// Checks tensor dimensions of children, returns dimensions of our result (2x2)
LoShape PSVTensor::getResultDims (const vector<const LoShape *> &input_dims)
{
  const LoShape &lmn = *input_dims[0], &b = *input_dims[1], &uvw = *input_dims[2];
  // the first child (LMN) is expected to be of shape Nx3, the second (B) of Nx2x2
  FailWhen(lmn.size()!=2 || lmn[1]!=3,"child '"+child_labels[0].toString()+"': an Nx3 result expected");
  // N is num_sources_
  num_sources_ = lmn[0];
  // UVW must be a 3-vector or a 2x3 matrix (in this case smearing is enabled, and the second row contains du,dv,dw).
  FailWhen(uvw!=shape_3vec && uvw!=shape_2x3,"child '"+child_labels[2].toString()+"': an 2x3 matrix or a 3-vector expected");
  // B must be a per-source tensor
  checkTensorDims(1,b,num_sources_);
  
  // Additional children after the first_jones should come in pairs (Jones term, plus its conjugate), and be per-source tensors
  FailWhen((input_dims.size()-first_jones_)%2!=0,"a pair of children must be provided per each Jones term");
  for( uint i=first_jones_; i<input_dims.size(); i++ )
    checkTensorDims(i,*input_dims[i],num_sources_);

  // our result is a 2x2 matrix 
  return LoShape(2,2);
}

// This gets the time/frequency info from the cells, and puts these into Vells objects:
// freq_vells_ for the frequency axis,
// df_over_2_ and f_dt_over_2_ for delta-freq/2 and freq*delta-time/2 (used in smearing calculations)
void PSVTensor::computeResultCells (Cells::Ref &ref,
        const std::vector<Result::Ref> &childres,const Request &request)
{
  // use cells of request (since that's where our time/freq axis comes from) if available,
  // else fall back to parent implementation which uses the child cells
  if( request.hasCells() )
    ref.attach(request.cells());
  else
    TensorFunction::computeResultCells(ref,childres,request);
  
  const Cells & cells = *ref;
  Vells freq_approx;
  if( cells.isDefined(Axis::FREQ) )
  {
    int nfreq = cells.ncells(Axis::FREQ);
    // set up frequency vells
    freq_vells_ = Vells(0,Axis::freqVector(nfreq),false);
    memcpy(freq_vells_.realStorage(),cells.center(Axis::FREQ).data(),nfreq*sizeof(double));
    // In the narrow-band case, use a single frequency for smearing calculations
    // (to speed up things)
    const Domain &dom = cells.domain();
    double freq0 = dom.start(Axis::FREQ);
    double freq1 = dom.end(Axis::FREQ);
    double midfreq = (freq0+freq1)/2;
    // narrow-band: use effectively a single frequency
    if( ::abs(freq0-freq1)/midfreq < narrow_band_limit_ )
      freq_approx = midfreq;
    else
      freq_approx = freq_vells_;
    // set up delta-freq/2 vells
    if( cells.numSegments(Axis::FREQ)<2 )
      df_over_2_ = cells.cellSize(Axis::FREQ)(0)/2;
    else
    {
      df_over_2_ = Vells(0,Axis::freqVector(nfreq),false);
      memcpy(df_over_2_.realStorage(),cells.cellSize(Axis::FREQ).data(),nfreq*sizeof(double));
      df_over_2_ /= 2;
    }
  }
  else
    freq_vells_ = freq_approx = df_over_2_ = 0;
  // set up delta-time/2 vells
  if( cells.isDefined(Axis::TIME) )
  {
    int ntime = cells.ncells(Axis::TIME);
    if( cells.numSegments(Axis::TIME)<2 )
      f_dt_over_2_ = cells.cellSize(Axis::TIME)(0)/2;
    else
    {
      f_dt_over_2_ = Vells(0,Axis::timeVector(ntime),false);
      memcpy(f_dt_over_2_.realStorage(),cells.cellSize(Axis::TIME).data(),ntime*sizeof(double));
      f_dt_over_2_ /= 2;
    }
    f_dt_over_2_ *= freq_approx;
  }
  else
    f_dt_over_2_ = 0;
}

// helper class to implement 2x2 matrix products
class IntermediateMatrix
{
  private:
    Vells x_[4];
    const Vells * px_[4];
   
    void initScalar (const Vells *value)
    {
      px_[0] = px_[3] = value;
      px_[1] = px_[2] = &(Vells::Null());
      scalar = true;
    }
    
  public:
    bool scalar;
    
    // accesses i-th element
    const Vells & operator () (int i) const
    { return *px_[i]; }
    
    // sets i-th element
    void set (int i,const Vells &value)
    { px_[i] = &( x_[i] = value ); }
    
    // Helper function: fills four pointers to Vells with four matrix elements corresponding to
    // child ichild, perturbation ipert, source isrc.
    // If shape of child is 1 and not 2x2, only fills the first pointer.
    // Returns true if any pointer was a new value (see newval flag of TensorFunctionPert::getChildValue()),
    // for ipert==0 this is always true
    bool fillFromChild (PSVTensor &psvt,int ichild,int ipert,int isrc)
    {
      bool newval = false;
      if( psvt.numChildElements(ichild) == psvt.num_sources_ ) // child supplies Nsrc values, hence Jones matrix is scalar
        initScalar(psvt.getChildValue(newval,ichild,ipert,isrc));
      // else assume Nsrcx2x2 matrix
      else
      {
        for( int i=0; i<4; i++ )
          px_[i] = psvt.getChildValue(newval,ichild,ipert,isrc*4+i);
        scalar = false;
      }
      return newval;
    }
    
    // fills matrix with product of matrices A and B
    void fillProduct (const IntermediateMatrix &a,const IntermediateMatrix &b)
    {
      if( a.scalar &&  b.scalar )
      {
        set(0,a(0)*b(0));
        initScalar(px_[0]);
      }
      else
      {
        if( a.scalar )
          for( int i=0; i<4; i++ )
            set(i,a(0)*b(i)); 
        else if( b.scalar )
          for( int i=0; i<4; i++ )
            set(i,b(0)*a(i)); 
        else
        {
          set(0, a(0)*b(0) + a(1)*b(2) );
          set(1, a(0)*b(1) + a(1)*b(3) );
          set(2, a(2)*b(0) + a(3)*b(2) );
          set(3, a(2)*b(1) + a(3)*b(3) );
        }
        scalar = false;
      }
    }
};

// fills tensors
void PSVTensor::evaluateTensors (Result &result,int npert,int nchildren)
{
  // if we have delta-uvws (child 2, elements 4-6), then enable smearing.
  // (Note below that the smearing term is only computed for the main values (ipert==0), as it is 
  // a lot of work computationally, and does not change appreciably with perturbation.
  const Vells *pduvw[3] = {0,0,0};
  if( numChildElements(2) == 6 )
    for( int i=0; i<3; i++ )
      pduvw[i] = getChildValue(2,0,i+3);
    
  // for each perturbation, initialize the output vells where the sum is accumulated
  std::vector<Vells*> out[4];
  for( int i=0; i<4; i++ )
  {
    out[i].resize(npert+1);
    for( int ipert=0; ipert<=npert; ipert++ )
      out[i][ipert] = &( initResultValue(result,ipert,i) );
  }
  // number of Jones pairs supplied to us as children
  int num_jones = (nchildren-first_jones_)/2;
  
  // For each source, for the main (non-perturbed) value, we store intermediate products for 
  // each pair of Jones terms. X[0] is B; X[1] is thus J1p*B*J2q^H, X[2] is J2p*X[0]*J2q^H, etc.
  // X[num_jones] is then the total source visibility, sans K term, sans smearing.
  std::vector<IntermediateMatrix> X(num_jones+1);
  std::vector<IntermediateMatrix> J(num_jones),Jt(num_jones);
  // temp value used in calculations
  IntermediateMatrix Y;
  // store values for reuse
  Vells K0sm,                         // K*smear
        K0smsh,                       // K*smear*shape
        shape0 = Vells::Unity(),      // smearing
        smear0 = Vells::Unity();      // shape
  std::vector<Vells> srcvis0(4);                   // total source visibility
 
  // each intermediate product by two jones terms gets stored in 
  
  // compute K=exp{ i*_2pi_over_c*freq*(u*l+v*m+w*n) } for every source, multiply by smearing term,
  // multiply by B matrix and all Jones matrices, then sum over all sources
  for( int isrc=0; isrc<num_sources_; isrc++ )
  {
    // loop over perturbations
    // Note that for each perturbation, typically only one component of the calculations changes, but it's a different
    // one every time. Most of the logic below (all the recmopute_xxx variables and flags) is therefore concerned with 
    // caching non-perturbed (aka "main") values (i.e. those for ipert==0), and reusing these as much as possible, so 
    // that only the bare minimum is recomputed for each perturbed product.
    for( int ipert=0; ipert<=npert; ipert++ )
    {
      bool recompute_K = !ipert;
      // collect uvw values for current perturbation
      const Vells *puvw[3];
      for( int i=0; i<3; i++ )
        puvw[i] = getChildValue(recompute_K,2,ipert,i);
      // collect lmn values for current perturbation
      const Vells *plmn[3];
      for( int i=0; i<3; i++ )
        plmn[i] = getChildValue(recompute_K,0,ipert,isrc*3+i);
      // intermediate values used in calculations
      Vells K,n,phase,shape;
      // pointer to which value to use
      Vells *pK = &K;
      bool recompute_shape = computeShapeTerm(shape,isrc,ipert,npert,nchildren) || !ipert;
      // does K need to be recomputed
      if( recompute_K )
      {
        // get the phase argument exp{ i*2*pi/c*(u*l+v*m+w*n) } -- this will be multiplied by frequency in computeExponent()
        n = *plmn[2]-n_minus_;
        phase = ((*puvw[0])*(*plmn[0]) + (*puvw[1])*(*plmn[1]) + (*puvw[2])*n)*_2pi_over_c;
        K = computeExponent(phase,resultCells());
      }
      // if computing main values (ipert==0), then cache them for reuse later in the loop
      if( !ipert )
      {
        // Compute the smear term. Note that in this way we only compute smearing for the main value and ignore 
        // perturbations, but that's OK since small pertubations to position will not change the smearing appreciably
        if( pduvw[0] )
        {
          Vells dphase = ((*pduvw[0])*(*plmn[0]) + (*pduvw[1])*(*plmn[1]) + (*pduvw[2])*n)*_2pi_over_c;
          smear0 = computeSmearingTerm(phase,dphase);
        }
        shape0 = shape;
        K0sm = K*smear0;
        K0smsh = K0sm*shape0;
        pK = &K0smsh;
      }
      // else see how much can be used from the cached main values
      else if( recompute_K )
        K *= smear0 * (recompute_shape ? shape : shape0);
      else if( recompute_shape )
        K = K0sm * shape;
      else
        pK = &K0smsh;
      // OK, *pK is now the K*smear*shape term
      
      // Accumulate Jones products by multiplying by each successive pair of Jones terms.
      // When ipert==0, we cache each intermediate product (i.e. B, J*B*J, J*J*B*Jt*Jt, etc.), so for perturbed
      // values we only recompute as much as needed.
      // First just collect pointers, so that we know many products to recompute.
      // Get pointers to Jones terms first. recompute_product will be set to the number of the _first_ Jones pair
      // that differs from the main value (so the product needs to be recomputed beginning from this stage)
      int recompute_product = num_jones+1;
      for( int i=num_jones-1; i>=0; i-- )
        if( J[i].fillFromChild(*this,first_jones_+i*2,ipert,isrc) | Jt[i].fillFromChild(*this,first_jones_+i*2+1,ipert,isrc) )
          recompute_product = i;
      // Get pointer to B term
      if( X[0].fillFromChild(*this,1,ipert,isrc) )
        recompute_product = 0;
      for( int j = recompute_product; j < num_jones; j++ )
      {
        Y.fillProduct(J[j],X[j]);
        X[j+1].fillProduct(Y,Jt[j]);
      }
      // for main value, cache the visibility contribution
      if( !ipert )
      {
        for( int i=0; i<4; i++ )
          (*out[i][0]) += srcvis0[i] = (*pK)*X[num_jones](i);
      }
      // for perturbed value: recompute contribution, if any component was recomputed
      else if( recompute_K || recompute_shape || recompute_product < num_jones )
      {
        for( int i=0; i<4; i++ )
          (*out[i][ipert]) += (*pK)*X[num_jones](i);
      }
      // else reuse cached contribution
      else
      {
        for( int i=0; i<4; i++ )
          (*out[i][ipert]) += srcvis0[i];
      }
    } // for ipert
  } // for isrc
}

// This computes the phase term, exp(-i*freq*p)
// It is mostly identical to VisPhaseShift::evaluateTensors()
// The p term is expected to be (ul+vm+wn)*2_pi/c, so need only be multiplied by frequency
// to get the actual phase
Vells PSVTensor::computeExponent (const Vells &p,const Cells &cells)
{
  // Now, if r is only variable in time, and we only have one
  // regularly-spaced frequency segment, we can use a quick algorithm
  // to compute only the exponent at freq0 and df, and then multiply
  // the rest.
  // Otherwise we fall back to the (potentially slower) full VellsMath version
  if( p.extent(Axis::TIME) == p.nelements() &&
      cells.ncells(Axis::FREQ) > 1            &&
      cells.numSegments(Axis::FREQ) == 1        )  // fast eval possible
  {
    // need to compute exp(-i*(freq0+n*dfreq)*p) for n=0...Nchan
    // decompose this into exp(-i*freq0*p)*exp(-i*dfreq*p)**n
    const double *fq = freq_vells_.realStorage();
    Vells vf0 = polar(1,p*fq[0]);
    Vells vdf = polar(1,p*(fq[1]-fq[0]));

    int ntime = p.extent(Axis::TIME);
    int nfreq = cells.ncells(Axis::FREQ);
    LoShape result_shape(ntime,nfreq);

    Vells out(numeric_zero<dcomplex>(),result_shape);
    dcomplex* resdata   = out.complexStorage();
    const dcomplex* pf0 = vf0.complexStorage();
    const dcomplex* pdf = vdf.complexStorage();

    int step = (ntime > 1 ? 1 : 0);
    for(int i = 0; i < ntime; i++)
    {
      dcomplex val0 = *pf0;
      *resdata++    = val0;
      dcomplex dval = *pdf;
      for(int j=1; j < nfreq; j++)
      {
        val0      *= dval;
        *resdata++ = val0;
      }// for j (freq)
      pf0 += step;
      pdf += step;
    }// for i (time)
    return out;
  }
  else // slower but much simpler
  {
    // create freq vells from grid
    return polar(1,p*freq_vells_);
  }
}

// This computes the time/freq smearing term, sinc(dt/2)*sinc(df/2), where
// dp is the delta-phase in time, and df is the delta-phase in frequency.
// Input argument is phase and delta-phase (which still needs to be multiplied by frequency),
// i.e. p is expected to be (ul+vm+wn)*2_pi/c, and dp is the same for delta-uvw

Vells PSVTensor::computeSmearingTerm (const Vells &p,const Vells &dp)
{
  Vells dphi = f_dt_over_2_ * dp;
  Vells dpsi = df_over_2_ * p;
  
  Vells prod1 = sin(dphi)/dphi;
  Vells prod2 = sin(dpsi)/dpsi;
  
  prod1.replaceFlaggedValues(dphi.whereEq(0.),1.);
  prod2.replaceFlaggedValues(dpsi.whereEq(0.),1.);
  
  return prod1*prod2;
}

// fill normalized visibilities -- do nothing, as they are then treated as unity
bool PSVTensor::computeShapeTerm (Vells &shape,int,int ipert,int,int)
{ 
  shape = Vells::Unity(); 
  return !ipert;
}


} // namespace Meq
