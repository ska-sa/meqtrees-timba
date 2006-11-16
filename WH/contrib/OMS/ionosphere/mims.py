from Timba.TDL import *
import math

import iono_geometry

TDLCompileOption('polc_deg_time',"Polc degree, in time",[0,1,2,3,4,5]);

TDLCompileMenu('MIM options',
  TDLOption('mim_polc_degree',"Polc degree in X/Y",[1,2,3,4,5,6,7])
);
  

def center_tecs_only (ns,source_list,array,observation):
  """Creates MIM to solve for one TEC per station independently.
  Returns tuple of (node,parm_names), where node should be qualified
  with source name and antenna to get a TEC, and parm_names is a list of 
  solvable parms""";

  polc_shape = [polc_deg_time+1,1];
  src0 = source_list[0];
  tecs = ns.tec;
  parmlist = [];
  for p in array.stations():
    tecs(p) << Meq.Parm(10.,shape=polc_shape,node_groups='Parm',
                   constrain=[8.,12.],user_previous=True,table_name='iono.mep');
    parmlist.append(tecs(p).name);
    
  tecfunc = lambda srcname,p: tecs(p);
  
  return tecfunc,parmlist;

  
def per_direction_tecs (ns,source_list,array,observation):
  """Creates MIM to solve for one TEC per source, per station.
  Returns tuple of (node,parm_names), where node should be qualified
  with source name and antenna to get a TEC, and parm_names is a list of 
  solvable parms""";
  polc_shape = [polc_deg_time+1,1];
  tecs = ns.tec;
  parmlist = [];
  for src in source_list:
    name = src.direction.name;
    for p in array.stations():
      tec = tecs(name,p) << Meq.Parm(10.,shape=polc_shape,node_groups='Parm',
                     constrain=[8.,12.],user_previous=True,table_name='iono.mep');
      parmlist.append(tec.name);
    
  return tecs,parmlist;


def mim_poly (ns,source_list,array,observation,poly_deg=3,tec0=10.):
  """Creates simple 3rd-order polynomial MIM over the array.
  Returns tuple of (node,parm_names), where node should be qualified
  with source name and antenna to get a TEC, and parm_names is a list of 
  solvable parms""";

  polc_shape = [polc_deg_time+1,1];
  # compute piercing points and zenith angle cosines
  pxy = iono_geometry.compute_piercings(ns,source_list,array,observation);
  za_cos = iono_geometry.compute_za_cosines(ns,source_list,array,observation);
  # make MIM parms
  parmlist = [];
  mc = ns.mim_coeff;
  degs = range(mim_polc_degree+1);
  polc_degs = [ (dx,dy) for dx in degs for dy in degs \
                if dx+dy <= mim_polc_degree ];
  for degx,degy in polc_degs:
    if not degx and not degy:
      mc(degx,degy) << tec0;
    else:
      mc(degx,degy) << Meq.Parm(0.,shape=polc_shape,node_groups='Parm',
                                user_previous=True,table_name='iono.mep',
                                tags=("mim","solvable"));
    parmlist.append(mc(degx,degy).name);
  # make TEC subtrees
  tecs = ns.tec;
  for src in source_list:
    name = src.direction.name;
    for p in array.stations():
      # normalized piercing point: divide by 1000km
      npx = ns.npx(name,p) << (ns.px(name,p) << Meq.Selector(pxy(name,p),index=0))*1e-6;
      npy = ns.npy(name,p) << (ns.py(name,p) << Meq.Selector(pxy(name,p),index=1))*1e-6;
      for degx,degy in polc_degs:
        npxypow = ns.npxypow(name,p,degx,degy) << Meq.Pow(npx,degx)*Meq.Pow(npy,degy);
        ns.vtecs(name,p,degx,degy) << mc(degx,degy)*npxypow;
      ns.vtec(name,p) << Meq.Add(*[ns.vtecs(name,p,dx,dy) for dx,dy in polc_degs]);
      tecs(name,p) << Meq.Divide(ns.vtec(name,p),za_cos(name,p),tags=["mim"]);

  return tecs,parmlist;  
