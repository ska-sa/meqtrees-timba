dmi_dir = $(lofar_sharedir)/../DMI

CXXFLAGS += -D_GNU_SOURCE 

# check_PROGRAMS		= 

bin_PROGRAMS   		= 

# glishwriter
# glishwriter_SOURCES		    = glishwriter.cc
# glishwriter_LDADD		      = ../src/libsolver.la -lglish -lsos -lnpd
# glishwriter_DEPENDENCIES	= ../src/libsolver.la $(LOFAR_DEPEND)

#check_PROGRAMS = tThread

#tThread_SOURCES 	= tThread.cc
#tThread_LDADD 	        = -lpython2.3
#tThread_DEPENDENCIES	= $(LOFAR_DEPEND)

TESTS				=  solver_test.sh

EXTRA_DIST			=

# script used to generate AID maps
MAPBUILDER = $(dmi_dir)/src/build_aid_maps.pl 

# All .aidlist files below this dir will be scanned
BASELISTDIR = $(lofar_sharedir)/..

# Your package's subdirectory
AID_DIR = $(top_srcdir)/test

aids:
#	$(MAPBUILDER) `find $(BASELISTDIR) -name \*.aidlist` $(AID_DIR)/*.h

include $(top_srcdir)/Makefile.common

AM_CPPFLAGS = -DMAKE_LOFAR_SYMBOLS_GLOBAL
