//#  Node.cc: base MeqNode class
//#
//#  Copyright (C) 2002-2003
//#  ASTRON (Netherlands Foundation for Research in Astronomy)
//#  P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
//#
//#  This program is free software; you can redistribute it and/or modify
//#  it under the terms of the GNU General Public License as published by
//#  the Free Software Foundation; either version 2 of the License, or
//#  (at your option) any later version.
//#
//#  This program is distributed in the hope that it will be useful,
//#  but WITHOUT ANY WARRANTY; without even the implied warranty of
//#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//#  GNU General Public License for more details.
//#
//#  You should have received a copy of the GNU General Public License
//#  along with this program; if not, write to the Free Software
//#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//#
//#  $Id$

#include "Node.h"
#include "Forest.h"
#include "ResampleMachine.h"
#include "MeqVocabulary.h"
#include <DMI/BlockSet.h>
#include <DMI/Record.h>
#include <DMI/Vec.h>
#include <DMI/NumArray.h>
#include <algorithm>

namespace Meq {

InitDebugContext(Node,"MeqNode");

using Debug::ssprintf;


//##ModelId=3F5F43E000A0
Node::Node (int nchildren,const HIID *labels,int nmandatory)
    : control_status_(CS_ACTIVE),
      check_nchildren_(nchildren),
      check_nmandatory_(nmandatory),
      depend_mask_(0),
      symdep_masks_(defaultSymdepMasks()),
      node_groups_(1,FAll),
      auto_resample_(RESAMPLE_NONE),
      disable_auto_resample_(false),
      propagate_child_fails_(true)
{
  Assert(nchildren>=0 || !labels);
  Assert(nchildren<0 || nchildren>=nmandatory);
  if( labels )   // copy labels
  {
    child_labels_.resize(nchildren);
    for( int i=0; i<nchildren; i++ )
      child_labels_[i] = labels[i];
    check_nmandatory_ = 0;
  }
  breakpoints_ = breakpoints_ss_ = 0;
  // else child_labels_ stays empty to indicate no labels -- this is checked below
}

//##ModelId=3F5F44A401BC
Node::~Node()
{
}

void Node::setDependMask (int mask)
{
  depend_mask_ = mask;
  if( staterec_.valid() )
    staterec_()[FDependMask] = mask;
  cdebug(3)<<ssprintf("new depend mask is %x\n",depend_mask_);
}

void Node::setKnownSymDeps (const HIID deps[],int ndeps)
{
  known_symdeps_ .assign(deps,deps+ndeps);
  if( staterec_.valid() )
    staterec_()[FKnownSymDeps].replace() = known_symdeps_;
}

void Node::setActiveSymDeps (const HIID deps[],int ndeps)
{
  cdebug(2)<<"setting "<<ndeps<<" active symdeps\n";
  active_symdeps_.assign(deps,deps+ndeps);
  if( known_symdeps_.empty() )
  {
    known_symdeps_ = active_symdeps_;
    if( staterec_.valid() )
      staterec_()[FKnownSymDeps].replace() = known_symdeps_;
  }
  if( staterec_.valid() )
    staterec_()[FActiveSymDeps].replace() = active_symdeps_;
  resetDependMasks();
}

void Node::setGenSymDeps (const HIID symdeps[],const int depmasks[],int ndeps,const HIID &group)
{
  cdebug(2)<<"setting "<<ndeps<<" generated symdeps\n";
  gen_symdep_fullmask_ = 0;
  for( int i=0; i<ndeps; i++ )
  {
    gen_symdep_fullmask_ |= 
        gen_symdep_masks_[symdeps[i]] = depmasks[i];
  }
  gen_symdep_group_ = group;
}

int Node::getGenSymDepMask (const HIID &symdep) const
{
  std::map<HIID,int>::const_iterator iter = gen_symdep_masks_.find(symdep);
  return iter == gen_symdep_masks_.end() ? 0 : iter->second;
}


int Node::computeDependMask (const std::vector<HIID> &symdeps) 
{
  int mask = 0;
  for( uint i=0; i<symdeps.size(); i++ )
  {
    const HIID &id = symdeps[i];
//    cdebug(3)<<"adding symdep "<<id<<ssprintf(": mask %x\n",symdep_masks_[id]);
    mask |= symdep_masks_[id];
  }
  return mask;
}

void Node::resetDependMasks ()
{ 
  setDependMask(computeDependMask(active_symdeps_)); 
}

//##ModelId=400E531402D1
void Node::setStateImpl (DMI::Record::Ref &rec,bool initializing)
{
  // if not initializing, check for immutable fields
  if( !initializing )
  {
    protectStateField(rec,FClass);
    protectStateField(rec,FChildren);
    protectStateField(rec,FChildrenNames);
    protectStateField(rec,FNodeIndex);
    protectStateField(rec,FResolveParentId);
  }
  // apply changes to mutable bits of control state
  int cs0 = control_status_;
  int new_cs;
  if( rec[FControlStatus].get(new_cs) )
    control_status_ = (control_status_&~CS_WRITABLE_MASK)|(new_cs&CS_WRITABLE_MASK);
  // set breakpoints
  if( rec[FBreakpoint].get(breakpoints_) )
    control_status_ = breakpoints_ ? control_status_|CS_BREAKPOINT : control_status_&~CS_BREAKPOINT;
  if( rec[FBreakpointSingleShot].get(breakpoints_ss_) )
    control_status_ = breakpoints_ss_ ? control_status_|CS_BREAKPOINT_SS : control_status_&~CS_BREAKPOINT_SS;
  // set/clear cached result
  //   the cache_result field must be either a Result object,
  //   or a boolean false to clear the cache. Else throw exception.
  DMI::Record::Hook hcache(rec,FCacheResult);
  TypeId type = hcache.type();
  if( type == TpMeqResult ) // a result
  {
    cache_result_ <<= hcache.as_wp<Result>();
    control_status_ |= CS_CACHED;
  }
  else if( type == Tpbool && !hcache.as<bool>() ) // a bool false
  {
    cache_result_.detach();
    control_status_ &= ~CS_CACHED;
  }
  else if( type != 0 ) // anything else (if type=0, then field is missing)
  {
    NodeThrow(FailWithCleanup,"illegal state."+FCacheResult.toString()+" field");
  }
  
  // apply any changes to control status
  if( cs0 != control_status_ )
  {
    rec[FControlStatus] = control_status_;
    forest_->newControlStatus(*this,cs0,control_status_); 
  }
  
  // set the name
  rec[FName].get(myname_,initializing);
  // set the caching policy
  //      TBD
  
  // get known symdeps
  rec[FKnownSymDeps].get_vector(known_symdeps_,initializing && !known_symdeps_.empty());
  // get symdep masks, if specified
  DMI::Record::Hook hdepmasks(rec,FSymDepMasks);
  if( hdepmasks.exists() )
  {
    symdep_masks_.clear();
    if( hdepmasks.type() == TpDMIRecord )
    {
      cdebug(2)<<"new symdep_masks set via state\n";
      const DMI::Record &maskrec = hdepmasks.as<DMI::Record>();
      for( uint i=0; i<known_symdeps_.size(); i++ )
      {
        const HIID &id = known_symdeps_[i];
        symdep_masks_[id] = maskrec[id].as<int>(0);
      }
      resetDependMasks();
    }
    else // not a record, clear everything
    {
      cdebug(2)<<"symdep_masks cleared via state\n";
      resetDependMasks();
    }
  }
  // recompute depmask if active sysdeps change
  if( rec[FActiveSymDeps].get_vector(active_symdeps_,initializing && !known_symdeps_.empty()) )
  {
    cdebug(2)<<"active_symdeps set via state\n";
    resetDependMasks();
  }
  // get generated symdeps, if any are specified
  DMI::Record::Hook genhook(rec,FGenSymDep);
  if( genhook.exists() )
  {
    try 
    {
      const DMI::Record &deps = genhook.as<DMI::Record>();
      std::map<HIID,int>::iterator iter = gen_symdep_masks_.begin();
      gen_symdep_fullmask_ = 0;
      for( ; iter != gen_symdep_masks_.end(); iter++ )
        gen_symdep_fullmask_ |= iter->second = deps[iter->first].as<int>();
    } 
    catch( std::exception & )
    {
      NodeThrow(FailWithCleanup,
          "incorrect or incomplete "+FGenSymDep.toString()+" state field");
    }
  }
  // else place them into data record
  else if( initializing && !gen_symdep_masks_.empty() )
  {
    DMI::Record &deps = genhook <<= new DMI::Record;
    std::map<HIID,int>::const_iterator iter = gen_symdep_masks_.begin();
    for( ; iter != gen_symdep_masks_.end(); iter++ )
      deps[iter->first] = iter->second;
  }
  // get generated symdep group, if specified
  rec[FGenSymDepGroup].get(gen_symdep_group_,initializing && !gen_symdep_masks_.empty());
  
  // now set the dependency mask if specified; this will override
  // possible modifications made above
  rec[FDependMask].get(depend_mask_,initializing);
  
  // set node groups, but always implicitly insert "All" at start
  std::vector<HIID> ngr;
  if( rec[FNodeGroups].get_vector(ngr) )
  {
    node_groups_.resize(ngr.size()+1);
    node_groups_.front() = FAll;
    for( uint i=0; i<ngr.size(); i++ )
      node_groups_[i+1] = ngr[i];
  }
  
  // set cache request ID
  rec[FCacheRequestId].get(cache_reqid_);
  // set cache resultcode
  rec[FCacheResultCode].get(cache_retcode_);
  // set auto-resample mode
  int ars = auto_resample_;
  if( rec[FAutoResample].get(ars,initializing) )
  {
    if( disable_auto_resample_ && ars != RESAMPLE_NONE )
    {
      NodeThrow(FailWithCleanup,"can't use auto-resampling with this node");
    }
    auto_resample_ = ars;
  }
}

//##ModelId=3F5F445A00AC
void Node::setState (DMI::Record::Ref &rec)
{
  // lock records until we're through
  Thread::Mutex::Lock lock(rec->mutex()),lock2(state().mutex());
  // when initializing, we're called with our own state record, which
  // makes the rules somewhat different:
  bool initializing = ( rec == staterec_ );
  cdebug(2)<<"setState(init="<<initializing<<"): "<<rec.sdebug(10)<<endl;
  string fail;
  // setStateImpl() is allowed to throw exceptions if something goes wrong.
  // This may leave the node with an inconsistency between the state record
  // and internal state. To recover from this, we can call setStateImpl() with
  // the current state record to reset the node state.
  // If the exception occurs before any change of state, then no cleanup is 
  // needed. Implementations may throw a FailWithoutCleanup exception to
  // indicate this.
  try
  {
    setStateImpl(rec,initializing);
  }
  catch( FailWithoutCleanup &exc )
  {
    throw; // No cleanup required, just re-throw
  }
  catch( std::exception &exc )
  {
    fail = string("setState() failed: ") + exc.what();
  }
  catch( ... )
  {
    fail = "setState() failed with unknown exception";
  }
  // has setStateImpl() failed?
  if( fail.length() )
  {
    // reset the state by reinitializing with the state record (this is
    // obviously pointless if we were initializing to begin with). Note
    // that an exception from this call indicates that the node is well 
    // & truly fscked (a good node should always be reinitializable), so
    // we might as well re-throw itm, letting the caller deal with it.
    if( !initializing )
      setStateImpl(staterec_,true);
    Throw(fail); // rethrow the fail
  }
  else // success
  {
    // success: merge record into state record
    if( !initializing )
      wstate().merge(rec,true);
  }
}

//##ModelId=400E53120082
void Node::setNodeIndex (int nodeindex)
{
  wstate()[FNodeIndex] = node_index_ = nodeindex;
}

//##ModelId=3F85710E011F
Node & Node::getChild (int i)
{
  FailWhen(!children_[i].valid(),"unresolved child");
  return children_[i].dewr();
}

const Node & Node::getChild (int i) const
{
  FailWhen(!children_[i].valid(),"unresolved child");
  return children_[i].deref();
}

//##ModelId=3F85710E011F
Node & Node::getStepChild (int i)
{
  FailWhen(!stepchildren_[i].valid(),"unresolved child");
  return stepchildren_[i].dewr();
}

const Node & Node::getStepChild (int i) const
{
  FailWhen(!stepchildren_[i].valid(),"unresolved child");
  return stepchildren_[i].deref();
}

//##ModelId=3F85710E028E
Node & Node::getChild (const HIID &id)
{
  ChildrenMap::const_iterator iter = child_map_.find(id);
  FailWhen(iter==child_map_.end(),"unknown child "+id.toString());
  return getChild(iter->second);
}

//##ModelId=3F98D9D20201
inline int Node::getChildNumber (const HIID &id)
{
  ChildrenMap::const_iterator iter = child_map_.find(id);
  return iter == child_map_.end() ? -1 : iter->second;
}

const DMI::Record & Node::syncState()
{ 
  DMI::Record & st = wstate();
  if( current_request_.valid() )
    st.replace(FRequest,current_request_);
  else
    st.remove(FRequest);
  if( cache_result_.valid() )
    st.replace(FCacheResult,cache_result_);
  else
    st.remove(FCacheResult);
  st[FCacheResultCode] = cache_retcode_;
  st[FCacheRequestId]  = cache_reqid_;
  st[FRequestId]       = current_reqid_;
  st[FControlStatus]   = control_status_; 
  st[FBreakpointSingleShot] = breakpoints_ss_;
  st[FBreakpoint] = breakpoints_;
  return st; 
}

//##ModelId=3F9919B10014
void Node::setCurrentRequest (const Request &req)
{
  current_request_.attach(req);
  current_reqid_ = req.id();
}

//##ModelId=400E531300C8
void Node::clearCache (bool recursive,bool quiet)
{
  cache_result_.detach();
  cache_retcode_ = 0;
  cache_reqid_.clear();
//  wstate()[FCacheResult].replace() = false;
//  wstate()[FCacheResultCode].replace() = cache_retcode_ = 0;
  clearRCRCache();
  if( quiet )
    control_status_ &= ~CS_CACHED;
  else
    setControlStatus(control_status_ & ~CS_CACHED);
  if( recursive )
  {
    for( int i=0; i<numChildren(); i++ )
      getChild(i).clearCache(true,quiet);
  }
}

// static FILE *flog = fopen("cache.log","w");

//##ModelId=400E531A021A
bool Node::getCachedResult (int &retcode,Result::Ref &ref,const Request &req)
{
  // no cache -- return false
  if( !cache_result_.valid() )
    return false;
  // Check that cached result is applicable:
  // (1) An empty reqid never matches, hence it can be used to 
  //     always force a recalculation.
  // (2) A cached RES_VOLATILE code requires an exact ID match
  //     (i.e. volatile results recomputed for any different request)
  // (3) Otherwise, do a masked compare using the cached result code
  cdebug(4)<<"checking cache: request "<<cache_reqid_<<", code "<<ssprintf("0x%x",cache_retcode_)<<endl;
//   fprintf(flog,"%s: cache contains %s, code %x, request is %s\n",
//           name().c_str(),
//           cache_reqid_.toString().c_str(),cache_retcode_,req.id().toString().c_str());
  if( !req.id().empty() && !cache_reqid_.empty() && 
      !req.hasCacheOverride() &&
      (cache_retcode_&RES_VOLATILE 
        ? req.id() == cache_reqid_
        : maskedCompare(req.id(),cache_reqid_,cache_retcode_) ) )
  {
    cdebug(4)<<"cache hit"<<endl;
//     fprintf(flog,"%s: reusing cache, cache cells are %x, req cells are %x\n",
//         name().c_str(),
//         (ref->hasCells() ? int(&(ref->cells())) : 0),
//         (req.hasCells() ? int(&(req.cells())) : 0));
    // UGLY KLUDGE ALERT:
    // make sure cells of request match result, and adjust cache accordingly
    if( req.hasCells() )
    {
      if( !cache_result_->hasCells() || &(cache_result_->cells()) != &(req.cells()) )
      {
//         fprintf(flog,"%s: inserting req cells %x\n",
//             name().c_str(),int(&(req.cells())));
        cache_result_().setCells(req.cells());
        cache_reqid_ = req.id();
      }
    }
    ref = cache_result_;
    retcode = cache_retcode_;
    return true;
  }
  cdebug(4)<<"cache miss"<<endl;
//  fprintf(flog,"%s: cache missed\n",name().c_str());
  // no match -- clear cache and return 
  clearCache(false);
  return false; 
}

// stores result in cache as per current policy, returns retcode
//##ModelId=400E531C0200
int Node::cacheResult (const Result::Ref &ref,int retcode)
{
  // clear the updated flag from cached results
  retcode &= ~RES_UPDATED;
  // for now, always cache, since we don't implement any other policy
  // NB: perhaps fails should be marked separately?
  cache_result_ = ref;
  cache_retcode_ = retcode;
  cache_reqid_ = current_reqid_;
  cdebug(3)<<"caching result "<<cache_reqid_<<" with code "<<ssprintf("0x%x",retcode)<<endl;
  // control status set directly (not via setControlStatus call) because
  // caller (execute(), presumably) is going to update status anyway
  control_status_ |= CS_CACHED;
  // sync state and publish to all result subscribers
  // NB***: if we don't cache the result, we have to publish it regardless
  // this is to be implemented later, with caching policies
  if( result_event_gen_.active() )
  {
    syncState();
    result_event_gen_.generateEvent(staterec_.copy());  
  }
  return retcode;
}

bool Node::checkRCRCache (Result::Ref &ref,int ich,const Cells &cells)
{
  if( ich<0 || ich>=int(rcr_cache_.size()) || !rcr_cache_[ich].valid() )
    return false;
  // check if resolution of cached result matches the request
  if( cells.compare(rcr_cache_[ich]->cells()) )
  {
    rcr_cache_[ich].detach();
    return false;
  }
  // match, return true
  ref.copy(rcr_cache_[ich]);
  return true;
}

void Node::clearRCRCache (int ich)
{
  if( ich<0 ) // clear all
  {
    for( int i=0; i<numChildren(); i++ )
      rcr_cache_[i].detach();
  }
  else
    rcr_cache_[ich].detach();
}

void Node::cacheRCR (int ich,const Result::Ref::Copy &res)
{
  if( ich >= int(rcr_cache_.size()) )
    rcr_cache_.resize(ich+1);
  rcr_cache_[ich].copy(res);
  // at this point we can perhaps tell the child to release cache, if there's
  // no change expected. Still have to think this through
}

void Node::addResultSubscriber (const EventSlot &slot)
{
  result_event_gen_.addSlot(slot);
  setControlStatus(control_status_ | CS_PUBLISHING);
  cdebug(2)<<"added result subscription "<<slot.evId().id()<<":"<<slot.recepient()<<endl;
}

void Node::removeResultSubscriber (const EventRecepient *recepient)
{
  result_event_gen_.removeSlot(recepient);
  if( !result_event_gen_.active() )
    setControlStatus(control_status_ & ~CS_PUBLISHING);
  cdebug(2)<<"removing all subscriptions for "<<recepient<<endl;
}

void Node::removeResultSubscriber (const EventSlot &slot)
{
  result_event_gen_.removeSlot(slot);
  if( !result_event_gen_.active() )
    setControlStatus(control_status_ & ~CS_PUBLISHING);
  cdebug(2)<<"removing result subscriber "<<slot.evId().id()<<":"<<slot.recepient()<<endl;
}

void Node::resampleChildren (Cells::Ref rescells,std::vector<Result::Ref> &childres)
{
  if( auto_resample_ == RESAMPLE_NONE )
    return;
  const Cells *pcells = 0;
  rescells.detach();
  std::vector<Thread::Mutex::Lock> child_reslock(numChildren());
  lockMutexes(child_reslock,childres);
//  rescells <<= pcells = &( childres[0]->cells() );
  bool need_resampling = false;
  for( uint ich=0; ich<childres.size(); ich++ )
  {
    const Result &chres = *childres[ich];
    if( chres.hasCells() )
    {
      const Cells &cc = childres[ich]->cells();
      if( !pcells ) // first cells? Init pcells with it
        rescells <<= pcells = &cc;
      else
      {
        // check if resolution matches
        int res = pcells->compare(cc);
        if( res<0 )       // result<0: domains differ, fail
        {
          res = pcells->compare(cc); // again, for debugging
          NodeThrow1("domains of child results do not match");
        }
        else if( res>0 )  // result>0: domains same, resolutions differ
        {
          // fail if auto-resampling is disabled
          if( auto_resample_ == RESAMPLE_FAIL )
          {
            NodeThrow1("resolutions of child results do not match and auto-resampling is disabled");
          }
          else 
          // generate new output Cells by upsampling or integrating
          // the special Cells constructor will do the right thing for us, according
          // to the auto_resample_ setting
          {
            cdebug(3)<<"child result "<<ich<<" has different resolution\n";
            rescells <<= pcells = new Cells(*pcells,cc,auto_resample_);
            need_resampling = true;
          }
        }
      }
    }
    else if( chres.numVellSets() ) // result not empty
      NodeThrow1(Debug::ssprintf("result of child %d does not have a Cells attached",ich));
  }
  // resample child results if required
  if( need_resampling )
  {
    Throw("resampling currently disabled");
//     cdebug(3)<<"resampling child results to "<<*pcells<<endl;
//     ResampleMachine resample(*pcells);
//     for( uint ich=0; ich<childres.size(); ich++ )
//     {
//       if( childres[ich]->hasCells() )
//       {
//         resample.setInputRes(childres[ich]->cells());
//         if( resample.isIdentical() ) // child at correct resolution already
//         {
//           cdebug(3)<<"child "<<ich<<": already at this resolution\n";
//           // clear resample cache for this child
//           clearRCRCache(ich);
//         }
//         else
//         {
//           // check if resampled-child cache already contains the resampled result
//           if( !checkRCRCache(childres[ich],ich,*pcells) )
//           {
//             cdebug(3)<<"child "<<ich<<": resampling\n";
//             // privatize child result for writing
//             Result &chres = childres[ich].privatize(DMI::WRITE)(); 
//             chres.setCells(pcells);
//             // resample and cache the child result 
//             for( int ivs=0; ivs<chres.numVellSets(); ivs++ )
//             {
//               VellSet::Ref ref;
//               resample.apply(ref,chres.vellSetRef(ivs),chres.isIntegrated());
//               chres.setVellSet(ivs,ref);
//             }
//             cacheRCR(ich,childres[ich]);
//           }
//           else
//           {
//             cdebug(3)<<"child "<<ich<<": already cached at this resolution, reusing\n";
//           }
//         }
//       }
//     }
  }
  else if( rescells.valid() ) // no resampling needed and cells were present, clear cache of all resampled children
    clearRCRCache();
}

int Node::pollStepChildren (const Request &req)
{
  int retcode = 0;
  for( int i=0; i<numStepChildren(); i++ )
  {
    Result::Ref dum;
    int childcode = getStepChild(i).execute(dum,req);
    cdebug(4)<<"    child "<<i<<" returns code "<<ssprintf("0x%x",childcode)<<endl;
    retcode |= childcode;
  }
  return retcode;
}

//##ModelId=400E531702FD
int Node::pollChildren (std::vector<Result::Ref> &child_results,
                        Result::Ref &resref,
                        const Request &req)
{
//   // in verbose mode, child results will also be stuck into the state record
//   DMI::Vec *chres = 0;
//   if( forest().verbosity()>1 )
//     wstate()[FChildResults] <<= chres = new DMI::Vec(TpMeqResult,numChildren());
//   
  setExecState(CS_ES_POLLING);
  bool cache_result = false;
  int retcode = 0;
  cdebug(3)<<"  calling execute() on "<<numChildren()<<" child nodes"<<endl;
  std::vector<const Result *> child_fails; // RES_FAILs from children are kept track of separately
  child_fails.reserve(numChildren());
  int nfails = 0;
  for( int i=0; i<numChildren(); i++ )
  {
    int childcode = getChild(i).execute(child_results[i],req);
    cdebug(4)<<"    child "<<i<<" returns code "<<ssprintf("0x%x",childcode)<<endl;
    retcode |= childcode;
    if( !(childcode&RES_WAIT) )
    {
      const Result *pchildres = child_results[i].deref_p();
//       // cache it in verbose mode
//       if( chres )
//         chres[i] <<= pchildres;
      if( childcode&RES_FAIL )
      {
        child_fails.push_back(pchildres);
        nfails += pchildres->numFails();
      }
    }
    // if child is updated, clear resampled result cache
    if( childcode&RES_UPDATED )
      clearRCRCache(i);
  }
  // now poll stepchildren (their results are always ignored)
  pollStepChildren(req);
  // if any child has completely failed, return a Result containing all of the fails 
  if( !child_fails.empty() )
  {
    if( propagate_child_fails_ )
    {
      cdebug(3)<<"  got RES_FAIL from children ("<<nfails<<"), returning fail-result"<<endl;
      Result &result = resref <<= new Result(nfails,req);
      int ires = 0;
      for( uint i=0; i<child_fails.size(); i++ )
      {
        const Result &childres = *(child_fails[i]);
        for( int j=0; j<childres.numVellSets(); j++ )
        {
          const VellSet &vs = childres.vellSet(j);
          if( vs.isFail() )
            result.setVellSet(ires++,&vs);
        }
      }
    }
    else
    {
      cdebug(3)<<"  ignoring RES_FAIL from children since fail propagation is off"<<endl;
      retcode &= ~RES_FAIL;
    }
  }
  cdebug(3)<<"  cumulative result code is "<<ssprintf("0x%x",retcode)<<endl;
  return retcode;
} 

int Node::resolve (DMI::Record::Ref &depmasks,int rpid)
{
  // if node already resolved with this parent ID, do nothing
  if( node_resolve_id_ == rpid )
  {
    cdebug(4)<<"node already resolved for rpid "<<rpid<<endl;
    return 0;
  }
  cdebug(3)<<"resolving node, rpid="<<rpid<<endl;
  wstate()[FResolveParentId] = node_resolve_id_ = rpid;
  // resolve children
  resolveChildren(false);
  // process depmasks 
  if( !known_symdeps_.empty() )
  {
    cdebug(3)<<"checking for "<<known_symdeps_.size()<<" known symdeps\n";
    const DMI::Record &rec = *depmasks;
    bool changed = false;
    for( uint i=0; i<node_groups_.size(); i++ )
    {
      DMI::Record::Hook hgroup(rec,node_groups_[i]);
      if( hgroup.exists() )
      {
        cdebug(4)<<"found symdeps for group "<<node_groups_[i]<<endl;
        const DMI::Record &grouprec = hgroup.as<DMI::Record>();
        for( uint i=0; i<known_symdeps_.size(); i++ )
        {
          const HIID &id = known_symdeps_[i];
          int mask;
          if( grouprec[id].get(mask) )
          {
            // add to its mask, if the symdep is present in the record.
            symdep_masks_[id] |= mask;
            cdebug(4)<<"symdep_mask["<<id<<"]="<<ssprintf("%x\n",symdep_masks_[id]);
            changed = true;
          }
        }
      }
    }
    // recompute stuff if anything has changed
    if( changed )
    {
      cdebug(3)<<"recomputing depmasks\n"<<endl;
      // recompute the active depend mask
      resetDependMasks();
      // reset subrecord in state rec
      DMI::Record &known = wstate()[FSymDepMasks].replace() <<= new DMI::Record;
      for( uint i=0; i<known_symdeps_.size(); i++ )
        known[known_symdeps_[i]] = symdep_masks_[known_symdeps_[i]];
    }
  }
  // add our own generated symdeps, if any. This COWs the record
  if( !gen_symdep_masks_.empty() )
  {
    rpid = nodeIndex(); // change the rpid
    const HIID &group = gen_symdep_group_.empty() ? FAll : gen_symdep_group_;
    cdebug(3)<<"inserting generated symdeps for group "<<group<<endl;
    DMI::Record &grouprec = Rider::getOrInit(depmasks(),group);
    std::map<HIID,int>::const_iterator iter = gen_symdep_masks_.begin();
    for( ; iter != gen_symdep_masks_.end(); iter++ )
    {
      DMI::Record::Hook hook(grouprec,iter->first);
      if( hook.exists() )
        hook.as_wr<int>() |=  iter->second;
      else
        hook = iter->second;
    }
  }
  // pass recursively onto children
  for( int i=0; i<numChildren(); i++ )
    children_[i]().resolve(depmasks,rpid);
  for( int i=0; i<numStepChildren(); i++ )
    stepchildren_[i]().resolve(depmasks,rpid);
  return 0;
}

// process Node-specific commands
int Node::processCommands (const DMI::Record &rec,Request::Ref &reqref)
{
  bool generate_symdeps = false;
  // process the Resolve.Children command: call resolve children
  // non-recursively (since the request + command is going up 
  // recursively anyway)
  if( rec[FResolveChildren].as<bool>(false) )
  {
    cdebug(4)<<"processCommands("<<FResolveChildren<<")\n";
    resolveChildren(false);
  }
  // process the "State" command: change node state
  ObjRef stateref = rec[FState].ref(true);
  if( stateref.valid() )
  {
    cdebug(4)<<"processCommands("<<FState<<"): calling setState()"<<endl;
    setState(stateref.ref_cast<DMI::Record>());
  }
  // process the "Clear.Dep.Mask" command: flush known symdep masks and
  // set our mask to 0
  if( rec[FClearDepMask].as<bool>(false) )
  {
    cdebug(2)<<"processCommands("<<FClearDepMask<<"): clearing symdep_masks"<<endl;
    symdep_masks_.clear();
    wstate()[FSymDepMasks].remove();
    setDependMask(0);
  }
  // process the "Add.Dep.Mask" command, if we track any symdeps
  DMI::Record::Hook hdep(rec,FAddDepMask);
  if( hdep.exists() )
  {
    if( !known_symdeps_.empty() && hdep.type() == TpDMIRecord )
    {
      cdebug(2)<<"processCommands("<<FAddDepMask<<"): checking for masks\n";
      const DMI::Record &deprec = hdep.as<DMI::Record>();
      // reinit the sysdep_masks field in the state record as we go along
      DMI::Record &known = wstate()[FSymDepMasks].replace() <<= new DMI::Record;
      for( uint i=0; i<known_symdeps_.size(); i++ )
      {
        const HIID &id = known_symdeps_[i];
        // add to its mask, if the symdep is present in the record.
        known[id] = symdep_masks_[id] |= deprec[id].as<int>(0);
        cdebug(3)<<"symdep_mask["<<id<<"]="<<ssprintf("%x\n",symdep_masks_[id]);
      } 
      // recompute the active depend mask
      resetDependMasks();
    }
  }
  // Init.Dep.Mask command: add our own symdeps to the request rider
  // (by inserting Add.Dep.Mask commands)
  if( rec[FInitDepMask].as<bool>(false) && !gen_symdep_masks_.empty() )
  {
    const HIID &group = gen_symdep_group_.empty() ? FAll : gen_symdep_group_;
    DMI::Record &cmdrec = Rider::getCmdRec_All(reqref,group);
    DMI::Record &deprec = Rider::getOrInit(cmdrec,FAddDepMask);
    std::map<HIID,int>::const_iterator iter = gen_symdep_masks_.begin();
    for( ; iter != gen_symdep_masks_.end(); iter++ )
    {
      DMI::Record::Hook hook(deprec,iter->first);
      if( hook.exists() )
        hook.as_wr<int>() |=  iter->second;
      else
        hook = iter->second;
    }
  }
//  // should never cache a processCommand() result
// or should we? I think we should (if only to ignore the same command
// coming from multiple parents)
  return RES_VOLATILE;
}

//##ModelId=3F6726C4039D
int Node::execute (Result::Ref &ref,const Request &req0)
{
  if( control_status_&CS_STOP_BREAKPOINT || getExecState() != CS_ES_IDLE )
  {
    Throw("can't re-enter Node::execute(). Are you trying to reexecute a node "
          "that is stopped at a breakpoint, or its parent?");
  }
  
  cdebug(3)<<"execute, request ID "<<req0.id()<<": "<<req0.sdebug(DebugLevel-1,"    ")<<endl;
  FailWhen(node_resolve_id_<0,"execute() called before resolve()");
  // this indicates the current stage (for exception handler)
  string stage;
  try
  {
    if( forest().debugLevel()>1 )
      wstate()[FNewRequest].replace() <<= req0;
    setExecState(CS_ES_REQUEST);
    int retcode = 0;
    // check the cache, return on match (method will clear on mismatch)
    stage = "checking cache";
    if( getCachedResult(retcode,ref,req0) )
    {
        cdebug(3)<<"  cache hit, returning cached code "<<ssprintf("0x%x",retcode)<<" and result:"<<endl<<
                   "    "<<ref->sdebug(DebugLevel-1,"    ")<<endl;
        setExecState(CS_ES_IDLE,control_status_|CS_RETCACHE);
        return retcode;
    }
    // clear out the RETCACHE flag and the result state, since we
    // have no result for now
    control_status_ &= ~(CS_RETCACHE|CS_RES_MASK);
    // do we have a new request? Empty request id treated as always new
    bool newreq = req0.id().empty() || ( req0.id() != current_reqid_ );
    // attach a ref to the request; processRequestRider() is allowed to modify
    // the request; this will result in a copy-on-write operation on this ref
    Request::Ref reqref(req0,DMI::READONLY);
    if( newreq )
    {
      // check if node is ready to go on to the new request, return WAIT if not
      stage = "calling readyForRequest()";
      if( !readyForRequest(req0) )
      {
        cdebug(3)<<"  node not ready for new request, returning RES_WAIT"<<endl;
        setExecState(CS_ES_IDLE,control_status_|CS_RES_WAIT);
        return RES_WAIT;
      }
      // set this request as current
      setCurrentRequest(req0);
      // check for request riders
      if( req0.hasRider() )
      {
        setExecState(CS_ES_COMMAND);
        stage = "processing rider";
        retcode = processRequestRider(reqref);
      }
    } // endif( newreq )
    // if node is deactivated, return an empty result at this point
    if( !getControlStatus(CS_ACTIVE) )
    {
      ref <<= new Result(0);
      cdebug(3)<<"  node deactivated, empty result. Cumulative result code is "<<ssprintf("0x%x",retcode)<<endl;
      int ret = cacheResult(ref,retcode) | RES_UPDATED;
      setExecState(CS_ES_IDLE,control_status_|CS_RES_EMPTY);
      return ret;
    }
    // in case processRequestRider modified the request, work with the new
    // request object from now on
    const Request &req = *reqref;
    // clear the retcode if the request has cells, children code + getResult() 
    // will be considered the real result
    if( req.hasCells() )
      retcode = 0;
    // Pass request on to children and accumulate their results
    std::vector<Result::Ref> child_results(numChildren());
//    std::vector<Thread::Mutex::Lock> child_reslock(numChildren());
    Cells::Ref rescells;
    if( numChildren() )
    {
      stage = "polling children";
      retcode |= pollChildren(child_results,ref,req);
//      lockMutexes(child_reslock,
//      for( int i=0; i<numChildren(); i++ )
//        if( child_results[i].valid() )
//          child_reslock[i].relock(child_results[i]->mutex());
      // a WAIT from any child is returned immediately w/o a result
      if( retcode&RES_WAIT )
      {
        setExecState(CS_ES_IDLE,control_status_|CS_RES_WAIT);
        return retcode;
      }
      // if failed, then cache & return the fail
      if( retcode&RES_FAIL )
      {
        int ret = cacheResult(ref,retcode) | RES_UPDATED;
        setExecState(CS_ES_IDLE,control_status_|CS_RES_FAIL);
        return ret;
      }
      // if request has cells, then resample children (will do nothing if disabled)
      if( req.hasCells() )
        resampleChildren(rescells,child_results);
    }
    // does request have a Cells object? Compute our Result then
    if( req.hasCells() )
    {
      setExecState(CS_ES_EVALUATING);
      stage = "getting result";
      cdebug(3)<<"  calling getResult(): cells are "<<req.cells();
      int code = getResult(ref,child_results,req,newreq);
      // default dependency mask added to return code
      retcode |= code | getDependMask();
      cdebug(3)<<"  getResult() returns code "<<ssprintf("0x%x",code)<<
          ", cumulative "<<ssprintf("0x%x",retcode)<<endl;
      // a WAIT is returned immediately with no valid result expected
      if( code&RES_WAIT )
      {
        setExecState(CS_ES_IDLE,control_status_|CS_RES_WAIT);
        return retcode;
      }
      // else we must have a valid Result object now, even if it's a fail.
      // (in case of RES_FAIL, getResult() should have put a fail in there)
      if( !ref.valid() )
      {
        NodeThrow1("must return a valid Result or else RES_WAIT");
      }
      // Make sure the Cells are in the Result object
      if( !(code&RES_FAIL) && ref->numVellSets() && !ref->hasCells() )
        ref().setCells(req.cells());
    }
    else // no cells, ensure an empty result
    {
      ref <<= new Result(0);
      cdebug(3)<<"  empty result. Cumulative result code is "<<ssprintf("0x%x",retcode)<<endl;
      int ret = cacheResult(ref,retcode) | RES_UPDATED;
      setExecState(CS_ES_IDLE,control_status_|CS_RES_EMPTY);
      return ret;
    }
    // OK, at this point we have a valid Result to return
    if( DebugLevel>=3 ) // print it out
    {
      cdebug(3)<<"  cumulative result code is "<<ssprintf("0x%x",retcode)<<endl;
      cdebug(3)<<"  result is "<<ref.sdebug(DebugLevel-1,"    ")<<endl;
      if( DebugLevel>3 && ref.valid() )
      {
        ref->show(Debug::getDebugStream());
      }
    }
    // cache & return accumulated return code
    int ret = cacheResult(ref,retcode) | RES_UPDATED;
    int st = ret&RES_FAIL ? CS_RES_FAIL : CS_RES_OK;
    setExecState(CS_ES_IDLE,control_status_|st);
    return ret;
  }
  // catch any exceptions, return a single fail result
  catch( std::exception &exc )
  {
    ref <<= new Result(1);
    VellSet & res = ref().setNewVellSet(0);
    MakeFailVellSet(res,string("exception in execute() while "+stage+": ")+exc.what());
    int ret = cacheResult(ref,RES_FAIL) | RES_UPDATED;
    setExecState(CS_ES_IDLE,
        (control_status_&~(CS_RETCACHE|CS_RES_MASK))|CS_RES_FAIL);
    return ret;
  }
}

void Node::setBreakpoint (int bpmask,bool oneshot)
{
  if( oneshot )
  {
    breakpoints_ss_ |= bpmask;
    setControlStatus(breakpoints_ss_ ? control_status_|CS_BREAKPOINT_SS : control_status_&~CS_BREAKPOINT_SS);
  }
  else
  {
    breakpoints_ |= bpmask;
    setControlStatus(breakpoints_ ? control_status_|CS_BREAKPOINT : control_status_&~CS_BREAKPOINT);
  }
}

void Node::clearBreakpoint (int bpmask,bool oneshot)
{
  if( oneshot )
  {
    breakpoints_ss_ &= ~bpmask;
    setControlStatus(breakpoints_ss_ ? control_status_|CS_BREAKPOINT_SS : control_status_&~CS_BREAKPOINT_SS); 
  }
  else
  {
    breakpoints_ &= ~bpmask;
    setControlStatus(breakpoints_ ? control_status_|CS_BREAKPOINT : control_status_&~CS_BREAKPOINT);
  }
}

void Node::setControlStatus (int newst,bool sync)
{ 
  if( sync )
    wstate()[FControlStatus] = newst;
  if( control_status_ != newst )
  {
    int oldst = control_status_;
    control_status_ = newst;
    forest_->newControlStatus(*this,oldst,newst); 
  }
}

void Node::setExecState (int es,int newst,bool sync)
{
  // update exec state in new control status 
  newst = (newst&~CS_MASK_EXECSTATE) | es;
  // check breakpoints
  int bp = breakpointMask(es);
  // always check global breakpoints first (to make sure single-shots are cleared)
  bool breakpoint = forest_->checkGlobalBreakpoints(bp);
  // the local flag is true if a local breakpoint (also) occurs
  bool local = false;
  // always check and flush local single-shot breakpoints
  if( breakpoints_ss_&bp )
  {
    breakpoint = local = true;
    breakpoints_ss_ = 0;
    newst &= ~CS_BREAKPOINT_SS;
  }
  else if( breakpoints_&bp ) // finally check for persistent local breakpoints
    breakpoint = local = true;
  // finally, check persistent local breakpoints too
  if( breakpoint )
  {
    // update control status
    setControlStatus(newst|CS_STOP_BREAKPOINT,sync);
    // notify the Forest that a breakpoint has been reached
    forest_->processBreakpoint(*this,es,!local);
    // clear stop bit from control status
    setControlStatus(control_status_&~CS_STOP_BREAKPOINT,sync);
  }
  else  // no breakpoints, simply update control status
    setControlStatus(newst,sync);
}

std::string Node::getStrExecState (int state)
{
  switch( state )
  {
    case CS_ES_IDLE:        return "IDLE";
    case CS_ES_REQUEST:     return "REQUEST";         
    case CS_ES_COMMAND:     return "COMMAND";         
    case CS_ES_POLLING:     return "POLLING";         
    case CS_ES_EVALUATING:  return "EVALUATING";
    default:                return "(unknown exec state)";
  }
}

//##ModelId=3F98D9D100B9
int Node::getResult (Result::Ref &,const std::vector<Result::Ref> &,
                     const Request &,bool)
{
  NodeThrow1("getResult() not implemented");
}


// throw exceptions for unimplemented DMI functions
//##ModelId=3F5F4363030F
CountedRefTarget* Node::clone(int,int) const
{
  NodeThrow1("clone() not implemented");
}

//##ModelId=3F5F43630315
int Node::fromBlock(BlockSet&)
{
  NodeThrow1("fromBlock() not implemented");
}

//##ModelId=3F5F43630318
int Node::toBlock(BlockSet &) const
{
  NodeThrow1("toBlock() not implemented");
}

//##ModelId=3F5F48180303
string Node::sdebug (int detail, const string &prefix, const char *nm) const
{
  using Debug::append;
  using Debug::appendf;
  using Debug::ssprintf;
  
  string out;
  if( detail >= 0 ) // basic detail
  {
    string typestr = nm?nm:objectType().toString();
    append(out,typestr + ":" + name() );
  }
  if( detail >= 1 || detail == -1 )
  {
    appendf(out,"cs:%x",getControlStatus());
  }
  if( abs(detail) >= 2 )
  {
    ChildrenMap::const_iterator iter = child_map_.begin();
    for( ; iter != child_map_.end(); iter++ )
    {
      out += "\n" + prefix + "  " + iter->first.toString() + ": " 
           + ( children_[iter->second].valid() 
               ? children_[iter->second]->sdebug(abs(detail)-2)
               : "unresolved" );
    }
  }
  return out;
}

} // namespace Meq
