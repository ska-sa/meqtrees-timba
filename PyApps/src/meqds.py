#!/usr/bin/python

# MEQ Data Services

from dmitypes import *
import weakref
import types
import new
import sets
import re
import time

_dbg = verbosity(3,name='meqds');
_dprint = _dbg.dprint;
_dprintf = _dbg.dprintf;


class _meqnode_nodeclass(record):
  pass;

_NodeClassDict = { 'meqnode':_meqnode_nodeclass };

# this function returns (creating as needed) the "Node class" class object
# for a given classname
def NodeClass (nodeclass=None):
  global _NodeClassDict;
  if nodeclass is None:
    return _meqnode_nodeclass;
  elif not isinstance(nodeclass,str):
    nodeclass = getattr(nodeclass,'classname',None) or getattr(nodeclass,'class');
  nodeclass = nodeclass.lower();
  cls = _NodeClassDict.get(nodeclass,None);
  if cls is None:
    cls = _NodeClassDict[nodeclass] = new.classobj(nodeclass,(_meqnode_nodeclass,),{});
  return cls;

# this class defines and manages a node list
class NodeList (object):
  NodeAttrs = ('name','class','children');
  RequestRecord = srecord(dict.fromkeys(NodeAttrs,True),nodeindex=True);
  
  class Node (object):
    def __init__ (self,ni):
      self.nodeindex = ni;
      self.name = None;
      self.classname = None;
      self.children = [];
      self.parents  = [];

  # init node list
  def __init__ (self,meqnl=None):
    if meqnl:
      self.load_meqlist(meqnl);
  
  # initialize from a MEQ-produced nodelist
  def load (self,meqnl):
    if not self.is_valid_meqnodelist(meqnl):
      raise ValueError,"not a valid meqnodelist";
    # check that all list fields are correct
    num = len(meqnl.nodeindex);
    # form sequence of iterators
    iter_name     = iter(meqnl.name);
    iter_class    = iter(meqnl['class']);
    iter_children = iter(meqnl.children);
    self._nimap = {};
    self._namemap = {};
    self._classmap = {};
    # iterate over all nodes in list
    # (0,) is a special case of an empty list (see bug in DMI/DataField.cc)
    if meqnl.nodeindex != (0,):
      for ni in meqnl.nodeindex:
        # insert node into list (or use old one: may have been inserted below)
        node = self._nimap.setdefault(ni,self.Node(ni));
        node.name      = iter_name.next();
        node.classname = iter_class.next();
        children  = iter_children.next();
        if isinstance(children,dict):
          node.children = tuple(children.iteritems());
        else:
          node.children = tuple(enumerate(children));
        # for all children, init node entry in list (if necessary), and
        # add to parent list
        for (i,ch_ni) in node.children:
          self._nimap.setdefault(ch_ni,self.Node(ch_ni)).parents.append(ni);
        # add to name map
        self._namemap[node.name] = node;
        # add to class map
        self._classmap.setdefault(node.classname,[]).append(node);
      # compose list of root (i.e. parentless) nodes
    self._rootnodes = [ node for node in self._nimap.itervalues() if not node.parents ];
    
#  __init__ = busyCursorMethod(__init__);
  # return list of root nodes
  def rootnodes (self):
    return self._rootnodes;
  # return map of classes
  def classes (self):
    return self._classmap;
  def iteritems (self):
    return self._nimap.iteritems();
  def iternodes (self):
    return self._nimap.itervalues();
  # mapping methods
  def __len__ (self):
    return len(self._nimap);
  # helper method: selects name or nodeindex map depending on key type
  def _map_ (self,key):
    if isinstance(key,str):     return self._namemap;
    elif isinstance(key,int):   return self._nimap;
    else:                       raise TypeError,"invalid node key "+str(key);
  def __getitem__ (self,key):
    return self._map_(key).__getitem__(key);
  def __contains__ (self,key):
    return self._map_(key).__contains__(key);
  def __setitem__ (self,key,node):
    if __debug__:
      if isinstance(key,string):  assert value.name == key;
      elif isinstance(key,int):   assert value.nodeindex == key;
      else:                       raise TypeError,"invalid node key "+str(key);
    self._nimap[node.nodeindex] = self._namemap[node.name] = node;
  def __iter__(self):
    return iter(self._nimap);

  # return True if this is a valid meqNodeList (i.e. node list object from meq kernel)
  def is_valid_meqnodelist (nodelist):
    for f in ('nodeindex',) + NodeList.NodeAttrs:
      if f not in nodelist:
        return False;
    return True;
  is_valid_meqnodelist = staticmethod(is_valid_meqnodelist);

# creates a UDI from a node record or node index or node name
def node_udi (node,suffix=None):
  try: (name,index) = (node.name,node.nodeindex);
  except AttributeError,KeyError: 
    node = nodelist[node];
    (name,index) = (node.name,node.nodeindex);
  udi = "/node/%s#%d"%(name,index);
  if suffix:
    udi += "/" + suffix;
  return udi;

_patt_Udi_NodeState = re.compile("^/node/([^#/]*)(#[0-9]+)?$");
def parse_node_udi (udi):
  match = _patt_Udi_NodeState.match(udi);
  if match is None:
    return (None,None);
  (name,ni) = match.groups();
  if ni is not None:
    ni = int(ni[1:]);
  return (name,ni);
  
def set_meqserver (mqs1):
  global mqs;
  mqs = weakref.proxy(mqs1);

def reclassify_nodestate (nodestate):
  nodestate.__class__ = NodeClass(nodestate['class']);
  
def nodeindex (node):
  if isinstance(node,int):
    return node;
  elif isinstance(node,str):
    return nodelist[node].nodeindex;
  else:
    return node.nodeindex

# Adds a subscriber to node state changes
#   If weak=True, callback will be held via weakref, otherwise
#   via WeakInstanceMethod (if object method), otherwise via direct ref
#
def subscribe_node_state (node,callback,weak=False):
  ni = nodeindex(node);
  if type(callback) == types.MethodType:
    _dprint(2,"registering weak method callback");
    callback = WeakInstanceMethod(callback);
  elif not callable(callback):
    raise TypeError,"callback argument is not a callable";
  elif weak:
    callback = weakref.ref(callback);
  # add to subscriber list
  node_subscribers.setdefault(ni,sets.Set()).add(callback);

def request_node_state (node):
  ni = nodeindex(node);
  mqs1 = mqs or mqs();
  if mqs1 is None:
    raise RuntimeError,"meqserver not initialized or not running";
  mqs.meq('Node.Get.State',srecord(nodeindex=ni),wait=False);
  
def update_node_state (node,event):
  ni = nodeindex(node);
  callbacks = node_subscribers.get(ni,());
  deleted = [];
  for cb in callbacks:
    if type(cb) == weakref.ReferenceType:
      cb1 = cb();
      if cb1 is None:
        "removing dead callback";
        deleted.append(cb);
      else:
        cb1(node,event);
    elif isinstance(cb,WeakInstanceMethod):
      if cb(node,event) is WeakInstanceMethod.DeadRef:
        "removing dead callback";
        deleted.append(cb);
    else:
      cb(node,event);
  # delete any dead subscribers
  for d in deleted:
    callbacks.remove(d);

def add_node_snapshot (node,event):
  ni = nodeindex(node);
  # get list of snapshots and filter it to eliminate dead refs
  sslist = filter(lambda s:s[0]() is not None,snapshots.get(ni,[]));
  if len(sslist) and sslist[-1][0]() == node:
    node.__nochange = True;
    return;
  sslist.append((weakref.ref(node),event,time.time()));
  snapshots[ni] = sslist;
  update_node_state(node,event);
  
def get_node_snapshots (node):
  ni = nodeindex(node);
  sslist0 = snapshots.get(ni,[]);
  # filter out dead refs, reset list if it changes
  sslist = filter(lambda s:s[0]() is not None,sslist0);
  if len(sslist) != len(sslist0):
    snapshots[ni] = sslist;
  return sslist;

# create global node list
snapshots = {};
nodelist = NodeList();

node_subscribers = {};
mqs = None;
