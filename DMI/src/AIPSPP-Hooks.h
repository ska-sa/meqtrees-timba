#ifndef DMI_AIPSPP_Hooks_h
#define DMI_AIPSPP_Hooks_h 1
    
#ifdef AIPSPP_HOOKS
    
#include <casa/Arrays/Array.h>
#include <casa/Arrays/Vector.h>
#include <casa/Arrays/Matrix.h>
#include <casa/BasicSL/String.h>
    
#include <DMI/DataArray.h>
#include <Common/BlitzToAips.h>


using LOFAR::copyArray;

namespace AIPSPP_Hooks 
{
  // templated helper method to create a 1D array using a copy of data
  template<class T>
  inline casa::Array<T> copyVector (TypeId tid,int n,const void *data)
  { 
    if( tid != typeIdOf(T) )
    {
      ThrowExc(NestableContainer::ConvError,"can't convert "+tid.toString()+
                  " to AIPS++ Array<"+typeIdOf(T).toString()+">");
    }
    return casa::Array<T>(casa::IPosition(1,n),static_cast<const T*>(data));
  };

  // specialization for String, with conversion from std::string
  template<>
  inline casa::Array<casa::String> copyVector (TypeId tid,int n,const void *data)
  { 
    if( tid != Tpstring )
    {
      ThrowExc(NestableContainer::ConvError,"can't convert "+tid.toString()+
                  " to AIPS++ Array<String>");
    }
    casa::String *dest0 = new casa::String[n], *dest = dest0;
    const string *src = static_cast<const string *>(data);
    for( int i=0; i<n; i++,dest++,src++ )
      *dest = *src;
    return casa::Array<casa::String>(casa::IPosition(1,n),dest0,casa::TAKE_OVER);
  };
  
};


inline casa::String NestableContainer::Hook::as_String () const
{
  return casa::String(as<string>());
}

template<class T>
casa::Array<T> NestableContainer::Hook::as_AipsArray (Type2Type<T>) const
{
  const void *targ = resolveTarget(DMI::NC_DEREFERENCE);
  // Have we resolved to a DataArray? 
  if( target.obj_tid == TpDataArray )
    return static_cast<const DataArray *>(targ)->copyAipsArray((T*)0);
  // have we resolved to a blitz array?
  else if( TypeInfo::isArray(target.obj_tid) )
  {
    casa::Array<T> out;
    switch( TypeInfo::rankOfArray(target.obj_tid) )
    {
      case 1: copyArray(out,*static_cast<const blitz::Array<T,1>*>(target.ptr)); break;
      case 2: copyArray(out,*static_cast<const blitz::Array<T,2>*>(target.ptr)); break;
      case 3: copyArray(out,*static_cast<const blitz::Array<T,3>*>(target.ptr)); break;
      case 4: copyArray(out,*static_cast<const blitz::Array<T,4>*>(target.ptr)); break;
      case 5: copyArray(out,*static_cast<const blitz::Array<T,5>*>(target.ptr)); break;
      case 6: copyArray(out,*static_cast<const blitz::Array<T,6>*>(target.ptr)); break;
      case 7: copyArray(out,*static_cast<const blitz::Array<T,7>*>(target.ptr)); break;
      case 8: copyArray(out,*static_cast<const blitz::Array<T,8>*>(target.ptr)); break;
      default: 
        ThrowExc(ConvError,"can't convert "+target.obj_tid.toString()+
                    " to AIPS++ Array<"+typeIdOf(T).toString()+">");
    }
    return out;
  }
  // have we resolved to scalar? Try the copyVector method
  return AIPSPP_Hooks::copyVector<T>(target.obj_tid,target.size,target.ptr);
}

template<class T>
casa::Vector<T> NestableContainer::Hook::as_AipsVector (Type2Type<T>) const
{
  casa::Array<T> arr = as_AipsArray();
  FailWhen( arr.ndim() != 1,"can't access array as Vector" );
  return casa::Vector<T>(arr);
}

template<class T>
casa::Matrix<T> NestableContainer::Hook::as_AipsMatrix (Type2Type<T>) const
{
  casa::Array<T> arr = as_AipsArray();
  FailWhen( arr.ndim() != 2,"can't access array as Matrix" );
  return casa::Matrix<T>(arr);
}

template<class T>
void NestableContainer::Hook::operator = (const casa::Array<T> &other) const
{
  (*this) <<= new DataArray(other,DMI::WRITE);
}

// assigning a String simply assigns a string
inline string & NestableContainer::Hook::operator = (const casa::String &other) const
{
  return operator = ( static_cast<const string &>(other) );
}

#endif

#endif
