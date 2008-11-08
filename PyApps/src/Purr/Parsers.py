_tdl_no_reimport = True;

import time
import os.path
from HTMLParser import HTMLParser

import Timba.utils

import Purr

_verbosity = Timba.utils.verbosity(name="purrparse");
dprint = _verbosity.dprint;
dprintf = _verbosity.dprintf;

    
def writeLogIndex (fobj,title,timestamp,entries):
  fobj.write("""<HTML><BODY>\n
    <TITLE>%s</TITLE>
    
    <H1><A CLASS="TITLE" TIMESTAMP=%d>%s</A></H1>
    
    """%(title,timestamp,title));
  for entry in entries:
    fobj.write(entry.renderIndex(os.path.join(os.path.basename(entry.pathname),"")));
  fobj.write("</BODY></HTML>\n");

class LogIndexParser (HTMLParser):
  def reset (self):
    HTMLParser.reset(self);
    self.title = "";
    self.timestamp = None;
    self.curclass = None;
    
  def end (self):
    dprintf(4,"end, title '%s', timestamp %s",self.title,self.timestamp);
    
  def handle_starttag (self,tag,attrs):
    dprint(4,"start tag",tag,attrs);
    # anchor tag -- data we look for is in here 
    if tag == "a":
      attrs = dict(attrs);
      tagclass = attrs.get('class');
      if tagclass:
        # whenever we encounter an A tag with a CLASS attribute, and the class
        # has a _handle_start_class method defined, call the handler.
        # The attributes are passed as keywords to the handler
        start_handler = getattr(self,"_handle_start_%s"%tagclass,None);
        if callable(start_handler):
          start_handler(**attrs);
        # If the class also has a _handle_end_class method defined, accumulate all text 
        # inside the tag (in self.curdata) for handling in the end handler
        if hasattr(self,"_handle_end_%s"%tagclass):
          if self.curclass:
            raise ValueError,"nested class %s inside tag of class %s"%(tagclass,self.curclass);
          self.curclass = tagclass;
          self.curdata = "";
    # paragraph tag: add newline to curdata, if accumulating
    elif tag == "p":
      if self.curclass and self.curdata:
        self.curdata += "\n";
  
  def _handle_start_TITLE (self,timestamp=0,**kw):
    if self.title is None:
      self.timestamp = int(timestamp);
    
  def _handle_end_TITLE (self,data):
    if not self.title:
      self.title = data;
  
  def handle_data (self,data):
    dprint(4,"data",data);
    data = data.rstrip();
    if data and self.curclass is not None:
      if self.curdata:
        self.curdata += " ";
      self.curdata += data;
      
  def handle_endtag (self,tag):
    dprint(4,"end tag",tag);
    # if end of A tag with CLASS attribute, pass accumulated data to data handler
    if tag == "a":
      if self.curclass:
        getattr(self,"_handle_end_%s"%self.curclass)(self.curdata)
        self.curclass = None;
    elif tag == "html":
      self.end();
    
class LogEntryIndexParser (LogIndexParser):
  def __init__ (self,dirname):
    LogIndexParser.__init__(self);
    self._dirname = dirname;
  
  def reset (self):
    LogIndexParser.reset(self);
    self.comments = None;
    self.dps = [];
    self._new_dp = None;
    
  def end (self):
    self._add_data_product();
    LogIndexParser.end(self);
    
  def _handle_start_DP (self,filename=None,src=None,policy=None,quiet=False,
                        timestamp=0,comment="",render=None,**kw):
    # dispence with previous DP tag, if any
    self._add_data_product();  
    # setup data for this tag
    self._new_dp = Purr.DataProduct(filename=filename,sourcepath=src,
                      timestamp=int(timestamp),comment=comment,
                      fullpath=os.path.join(self._dirname,filename),
                      policy=policy,render=render,quiet=quiet);
  
  def _handle_end_TITLE (self,data):
    self.title = data;
    
  def _handle_end_COMMENTS (self,data):
    self.comments = data;
    
  def _handle_end_DPCOMMENT (self,data):
    if self._new_dp:
      self._new_dp.comment = data;
      self._add_data_product();
    
  def _add_data_product (self):
    if self._new_dp:
      self.dps.append(self._new_dp);
      self._new_dp = None;
      
if __name__ == "__main__":
  parser = LogEntryParser();
  for line in file('index.html'):
    parser.feed(line);

