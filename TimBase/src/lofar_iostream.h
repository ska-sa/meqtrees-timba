//  lofar_iostream.h:
//
//  Copyright (C) 2002-2007
//  ASTRON (Netherlands Foundation for Research in Astronomy)
//  and The MeqTree Foundation
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

#ifndef COMMON_IOSTREAM_H
#define COMMON_IOSTREAM_H

#include <TimBase/lofar_iosfwd.h>
#include <iostream>

namespace LOFAR
{
  using std::istream;
  using std::ostream;
  using std::iostream;
  using std::cin;
  using std::cout;
  using std::cerr;
  using std::endl;
  using std::ends;
  using std::flush;
}

#ifdef MAKE_LOFAR_SYMBOLS_GLOBAL
#include <TimBase/lofar_global_symbol_warning.h>
using LOFAR::istream;
using LOFAR::ostream;
using LOFAR::iostream;
using LOFAR::cin;
using LOFAR::cout;
using LOFAR::cerr;
using LOFAR::endl;
using LOFAR::ends;
using LOFAR::flush;
#endif

#endif
