//  DataArray.cc: DMI Array class (using AIPS++ Arrays)
//
//  Copyright (C) 2002
//  ASTRON (Netherlands Foundation for Research in Astronomy)
//  P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
//
//  This program is free software; you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation; either version 2 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//
//  $Id$
//
//  $Log$
//  Revision 1.6  2002/05/07 11:46:00  gvd
//  The 'final' version supporting array subsets
//
//  Revision 1.5  2002/04/17 12:19:31  oms
//  Added the "Intermediate" type category (for Array_xxx) and support for it
//  in hooks.
//
//  Revision 1.4  2002/04/12 10:15:09  oms
//  Added fcomplex and dcomplex types.
//  Changes to NestableContainer::get():
//   - merged autoprivatize and must_write args into a single flags arg
//   - added NC_SCALAR and NC_POINTER flags that are passed to get()
//  Got rid of isScalar() and isContiguous(), checking is now up to get().
//
//  Revision 1.3  2002/04/12 07:47:53  oms
//  Added fcomplex and dcomplex types
//
//  Revision 1.2  2002/04/08 14:27:07  oms
//  Added isScalar(tid) to DataArray.
//  Fixed isContiguous() in DataField.
//
//  Revision 1.1  2002/04/05 13:05:46  gvd
//  First version
//


#ifndef DMI_DATAARRAY_H
#define DMI_DATAARRAY_H

#include "DMI/Common.h"
#include "DMI/DMI.h"

#pragma types #DataArray
#pragma types %Array_bool %Array_int %Array_float %Array_double
#pragma types %Array_fcomplex %Array_dcomplex

#include "DMI/NestableContainer.h"
#include "DMI/HIID.h"
#include "DMI/SmartBlock.h"

#include <aips/Arrays/Array.h>


class DataArray : public NestableContainer
{
public:
  // Create the object without an array in it.
  explicit DataArray (int flags = DMI::WRITE);

  // Create the object with an array of the given shape.
  DataArray (TypeId type, const IPosition& shape, int flags = DMI::WRITE,
	     int shm_flags = 0);

  // Copy (copy semantics).
  DataArray (const DataArray& other, int flags = 0, int depth = 0);

  ~DataArray();

  // Assignment (copy semantics).
  DataArray& operator= (const DataArray& other);

  // Return the object type (TpDataArray).
  virtual TypeId objectType() const;

  // Reconstruct the DataArray object from a BlockSet.
  virtual int fromBlock (BlockSet& set);

  // Add the DataArray object to the BlockSet.
  virtual int toBlock (BlockSet& set) const;

  // Clone the object.
  virtual CountedRefTarget* clone (int flags = 0, int depth = 0) const;

  // Privatize the object.
  virtual void privatize (int flags = 0, int depth = 0);

  // Get the 
  virtual const void* get (const HIID& id, TypeId& tid, bool& can_write,
			   TypeId check_tid = 0, int flags = 0) const;

  // Insertion is not possible (throws exception).
  virtual void* insert (const HIID& id, TypeId tid, TypeId& real_tid);

  // The size is the number of array elements.
  virtual int size() const;

  // The actual type of the array (TpArray_float, etc.).
  virtual TypeId type() const;
  
      
private:
  // The object is valid if it contains an array.
  bool valid() const 
    { return itsArray; }

  // Initialize internal shape and create array using the given shape.
  void init (const IPosition& shape);

  // Initialize shape and create array using internal shape.
  void reinit();

  // Create the actual Array object.
  // It is created from the array data part in the SmartBlock.
  void makeArray();

public:
  // Parse a HIID describing a subset and fill start,end,incr.
  // It fills in keepAxes telling if an axes should always be kept,
  // even if it is degenerated (i.e. has length 1).
  // It returns true if axes can be removed.
  bool parseHIID (const HIID& id, IPosition& st, IPosition& end,
		  IPosition& incr, IPosition& keepAxes) const;

  // Clear the object (thus remove the Array).
  void clear();

  // Clone the object.
  void cloneOther (const DataArray& other, int flags = 0, int depth = 0);

  // Accessor functions to array type and size kept in the SmartBlock.
  int headerType() const
    { return static_cast<const int*>(*itsData.deref())[0]; }
  int headerSize() const
    { return static_cast<const int*>(*itsData.deref())[1]; }
  void setHeaderType (int type)
    { static_cast<int*>(*itsData.dewr())[0] = type; }
  void setHeaderSize (int size)
    { static_cast<int*>(*itsData.dewr())[1] = size; }


  IPosition  itsShape;          // actual shape
  BlockRef   itsData;           // SmartBlock holding the data
  TypeId     itsScaType;        // scalar data type matching the array type
  int        itsElemSize;       // #bytes of an array element
  int        itsDataOffset;     // array data offset in SmartBlock
  char*      itsArrayData;      // pointer to array data in SmartBlock
  void*      itsArray;          // pointer to the Array object
  void*      itsSubArray;       // pointer to Array object holding a subarray
};


#endif
