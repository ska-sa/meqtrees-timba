# standard preamble
from Timba.TDL import *

# Timba.TDL.Settings.forest_state is a standard TDL name. 
# This is a record passed to Set.Forest.State. 
Settings.forest_state.cache_policy = 100;
Settings.forest_state.a = None;

# Make sure our solver root node is not cleaned up
Settings.orphans_are_roots = True;

def _define_forest (ns,**kwargs):
  """define_forest() is a standard TDL name. When a forest script is
  loaded by, e.g., the browser, this method is automatically called to
  define the forest. The 'ns' argument is a NodeScope object in which
  the forest is to be defined, usually this is simply the global scope.
  """;
  ns.value << Meq.Sin(Meq.Freq) + Meq.Cos(Meq.Time) + \
              Meq.Cos(Meq.Grid(axis='l')) - Meq.Sin(Meq.Grid(axis='m'));
  children = [];
  for nodeclass in ("Min","Max","Mean","Sum","Product","NElements"):
    name = nodeclass.lower();
    children.append(ns[name] << Meq[nodeclass](ns.value));
    children.append(ns[name]('t') << Meq[nodeclass](ns.value,reduction_axes=(0,)));
    children.append(ns[name]('f') << Meq[nodeclass](ns.value,reduction_axes=(1,)));
    children.append(ns[name]('tf') << Meq[nodeclass](ns.value,reduction_axes=(0,1)));
    
  ns.mux = Meq.ReqMux(*children);

def _test_forest (mqs,parent,**kwargs):
  """test_forest() is a standard TDL name. When a forest script is
  loaded by, e.g., the browser, and the "test" option is set to true,
  this method is automatically called after define_forest() to run a 
  test on the forest. The 'mqs' argument is a meqserver proxy object.
  """;
  from Timba.Meq import meq
  # run tests on the forest
  dom = meq.gen_domain(time=(0,6),freq=(0,6),l=(0,6),m=(0,6));
  cells = meq.gen_cells(dom,num_freq=20,num_time=20,num_l=20,num_m=20);
  request = meq.request(cells,rqtype='ev');
  mqs.meq('Node.Execute',record(name='mux',request=request),wait=False);

# this is the testing branch, executed when the script is run directly
# via 'python script.py'

if __name__ == '__main__':
#  from Timba.Meq import meqds 
  Timba.TDL._dbg.set_verbose(5);
  ns = NodeScope();
  _define_forest(ns);
  # resolves nodes
  ns.Resolve();
