# file: ../Grunt/Matrix22.py

# History:
# - 29dec2006: creation (extracted from Jones.py) 

# Description:

# The Matrix22 class encapsulates groups of 2x2 matrices,
# e.g. Jones matrices, or cohaerency matrices. 

#======================================================================================

from Timba.TDL import *
from Timba.Meq import meq

from ParmGroupManager import *
# from ParmGroup import *
from Qualifiers import *

# from Timba.Contrib.JEN.Grunt import ParmGroup
from Timba.Contrib.JEN.util import JEN_bookmarks
from Timba.Contrib.JEN import MG_JEN_dataCollect

from copy import deepcopy

#======================================================================================

class Matrix22 (object):
    """Class that represents a set of 2x2 matrices.
    It is inherited by the Jones class and the Cohsat class.  
    It also contains the named ParmGroup objects that encapsulate
    groups of MeqParm nodes (or their simulation subtrees)"""

    def __init__(self, ns, quals=[], label='M', indices=[], simulate=False):
        self._ns = ns                                # node-scope (required)
        self._label = label                          # label of the matrix 

        # Node-name qualifiers:
        self._quals = Qualifiers(quals, prepend=label)

        self._simulate = simulate                    # if True, use simulation subtrees (i.s.o. MeqParms)
        if self._simulate:
            self._quals.append('simul')

        self._matrix = None                          # the actual matrices (contract!)
        self._indices = indices                      # list of matrix 'indices' (e.g. stations)

        # Matrix22 matrix elements (contract!)
        self._matrel = dict(m11=None, m12=None, m21=None, m22=None)
        self._dcoll = None                           # visualization
        self._matrel_index = dict(m11=[0,0], m12=[0,1], m21=[1,0], m22=[1,1])
        self._matrel_style = dict(m11='circle', m12='xcross', m21='xcross', m22='circle')
        self._matrel_color = dict(m11='red', m12='magenta', m21='darkCyan', m22='blue')

        # The (solvable and simulated) MeqParms are handled in named groups:
        self._pgm = ParmGroupManager(ns, label=self.label(),quals=self.quals(),
                                     simulate=self._simulate)

        self._dummyParmGroup = ParmGroup('dummy')    # used for its printing functions...
        return None

    #-------------------------------------------------------------------

    def copy(self):
        """Return a (limited) copy of the current Matrix22 object.
        For the moment, for limited use only (no self._parmgroups)."""
        # return deepcopy(self)
        c = Matrix22(self._ns, quals=self.quals(),
                     label='copy('+self.label()+')',
                     indices=self.indices(),
                     simulate=self._simulate)
        c.matrix(new=self.matrix())
        return c

    #-------------------------------------------------------------------

    def label(self):
        """Return the Matrix22 object label""" 
        return self._label

    def quals(self, append=None, prepend=None, exclude=None):
        """Return the nodename qualifier(s), with temporary modifications"""
        return self._quals.get(append=append, prepend=prepend, exclude=exclude)

    #-------------------------------------------------------------------

    def indices(self, new=None):
        """Get/set the list of (matrix) indices"""
        if new:
            self._indices = new
        return self._indices


    def matrix(self, new=None):
        """Get/set the 2x2 matrices themselves"""
        if new:
            self._matrix = new
        return self._matrix

    #-------------------------------------------------------------------

    def matrix_element(self, key='m11', return_nodes=False):
        """Return the specified matrix element(s)"""
        if not self._matrel.has_key(key):
            return False                                # invalid key.....
        if not self._matrel[key]:                       # do only once
            quals = self.quals()
            name = self.label()+'_'+key[1:]
            for s in self.indices():
                index = self._matrel_index[key]
                node = self._ns[name](*quals)(s) << Meq.Selector(self._matrix(s),
                                                                 index=index)
            self._matrel[key] = self._ns[name](*quals)

        # Return a list of nodes, if required:
        if return_nodes:
            nodes = []
            for s in self.indices():
                nodes.append(self._matrel[key](s))
            return nodes
        
        # Otherwise, return the 'contract':
        return self._matrel[key] 

    #-------------------------------------------------------------------

    def oneliner(self):
        """Return a one-line summary of this object"""
        ss = str(type(self))
        ss += '  '+str(self.label())
        ss += '  n='+str(len(self.indices()))
        ss += '  quals='+str(self.quals())
        # if self._simulate: ss += ' (simulate)'
        return ss

    def display_specific(self, full=False):
        """Print the specific part of the summary of this object"""
        # NB: This function is called in .display().
        #     It should be re-implemented in a derived class.
        return True

    def display(self, txt=None, full=False):
        """Print a summary of this object"""
        print ' '
        print '** '+self.oneliner()
        if txt: print ' * (txt='+str(txt)+')'
        self.display_specific(full=full)
        print '** Generic (class Matrix22):'
        print ' * Available indices ('+str(len(self.indices()))+'): '+str(self.indices())
        #...............................................................
        print ' * Available 2x2 matrices ('+str(len(self.indices()))+'): '
        if self._matrix:
            for s in self.indices():
                print '  - '+str(s)+': '+str(self.matrix()(s))
            print ' * The first two matrices:'
            for i in range(len(self.indices())):
                if i<2:
                    node = self.matrix()(self.indices()[i])
                    self._dummyParmGroup.display_subtree(node, txt=str(i), recurse=2)
        #...............................................................
        ntot = len(self._pgm._parmgroup) + len(self._pgm._simparmgroup)
        print ' * Available NodeGroup objects ('+str(ntot)+'): '
        for key in self._pgm._parmgroup.keys():
            print '  - '+str(self._pgm._parmgroup[key].oneliner())
        for key in self._pgm._simparmgroup.keys():
            print '  - (sim) '+str(self._pgm._simparmgroup[key].oneliner())
        #...............................................................
        print ' * Extracted matrix elements: '
        for key in self._matrel.keys():
            print '  - '+str(key)+': '+str(self._matrel[key])
        #...............................................................
        print ' * Visualization subtree: '
        if self._dcoll:
            self._dummyParmGroup.display_subtree(self._dcoll, txt=':',
                                                 show_initrec=False, recurse=1)
        print '   - matrel_index: '+str(self._matrel_index)
        print '   - matrel_color: '+str(self._matrel_color)
        print '   - matrel_style: '+str(self._matrel_style)
        #...............................................................
        print '**\n'
        return True




    #=====================================================================================
    # Math operations: 
    #=====================================================================================


    def binop(self, binop=None, other=None):
        """Do an (item-by-item) binary operation (e.g. Subtract)
        between itself and another Matrix22 object."""
        quals = self.quals()
        qother = other._quals.concat()        # -> one string, with _ between quals
        for i in self._indices:
            self._ns[binop](*quals)(qother)(i) << getattr(Meq,binop)(self._matrix(i),
                                                                     other._matrix(i))
        self._matrix = self._ns[binop](*quals)(qother)     # replace
        self.merge_parmgroups(other)
        return True


    def unop(self, unop=None):
        """Do an (item-by-item) unary operation on itself (e.g. Abs)"""
        quals = self.quals()
        for i in self._indices:
            self._ns[unop](*quals)(i) << getattr(Meq,unop)(self._matrix(i))
        self._matrix = self._ns[unop](*quals)              # replace
        return True

    #---------------------------------------------------------------------

    def bundle(self, oper='Composer'):
        """Bundle its matrices, using an operation like Composer, Add, Multiply etc"""
        quals = self.quals()
        if not self._ns.bundle(oper)(*quals).initialized():
            for i in self._indices:
                cc.append(self._matrix(i))
            self._ns.bundle(oper)(*quals) << getattr(Meq,oper)(children=cc)
        return self._ns.bundle(oper)(*quals)



    #=====================================================================
    # Visualization:
    #=====================================================================

    def visualize (self, matrel='*', bookpage='Matrix22', folder=None):
        """Visualise (a subset of) the 4 complex matrix elements of all 
        Matrix22 matrices in a single real-vs-imag plot. Different
        matrix elements (m11,m12,m21,m22) have different styles
        and colors, which are the same for all Matrix22 matrices."""
        if not self._dcoll:
            dcoll_quals = self._quals.concat()
            dcolls = []
            keys = deepcopy(matrel)
            if keys=='*': keys = self._matrel.keys()              # i.e. ['m11','m12','m21','m22']
            if not isinstance(keys,(list,tuple)): keys = [keys]
            for key in keys:  
                cc = self.matrix_element(key, return_nodes=True) 
                rr = MG_JEN_dataCollect.dcoll (self._ns, cc, 
                                               scope=dcoll_quals,
                                               tag=key,
                                               color=self._matrel_color[key],
                                               style=self._matrel_style[key],
                                               size=8, pen=2,
                                               type='realvsimag', errorbars=True)
                dcolls.append(rr)
            # Make a combined plot of all the matrix elements:
            # NB: nodename -> dconc_scope_tag
            rr = MG_JEN_dataCollect.dconc(self._ns, dcolls, scope=dcoll_quals,
                                          tag=' ', bookpage=None)
            self._dcoll = rr['dcoll']
            JEN_bookmarks.create(self._dcoll, self.label(),
                                 page=bookpage, folder=folder)
        # Return the dataConcat node:
        return self._dcoll



    #==============================================================================
    # Solving:
    #==============================================================================

    def make_condeqs (self, other=None, matrel='*', replace=False):
        """Make a list of condeq nodes by comparing its matrices (or -elements)
        with the corresponding matrices of another Matrix22 object."""
        quals = self.quals()
        qother = other._quals.concat()        # -> one string, with _ between quals

        # It is possible to use only a subset of the matrix elements:
        keys = self._matrel.keys()            # i.e. ['m11','m12','m21','m22']
        mel = deepcopy(matrel)
        if mel=='*': mel = keys
        if not isinstance(mel,(list,tuple)): mel = [mel]
        index = []
        postfix = ''
        for i in range(len(keys)):
            if keys[i] in mel:
                index.append(i)
                postfix += '_'+str(i)

        # First make condeq nodes for all 4 matrix elements:
        # These are used for visualisation later (if replace=True)
        if replace or (len(index)==4):
            condeqs = []
            for i in self.indices():
                c = self._ns.condeq(*quals)(qother)(i) << Meq.Condeq(self._matrix(i),
                                                                     other._matrix(i))
                condeqs.append(c)
            if replace: self._matrix = self._ns.condeq(*quals)(qother)   # replace 

        # If a subset of the matrix elements is required, generate a new set of condeqs,
        # which contain the relevant selections.
        if len(index)<4:
            condeqs = []
            name = 'condeq'+postfix
            name1 = 'lhs'+postfix
            name2 = 'rhs'+postfix
            for i in self.indices():
                node1 = self._matrix(i)
                node2 = other._matrix(i)
                node1 = self._ns[name1].qadd(node1) << Meq.Selector(node1, index=index)
                node2 = self._ns[name2].qadd(node2) << Meq.Selector(node2, index=index)
                c = self._ns[name](*quals)(qother)(i) << Meq.Condeq(node1, node2)
                condeqs.append(c)
        # Return a list of condeq nodes:
        return condeqs

    #----------------------------------------------------------------------------------

    def make_solver (self, parmgroup='*', other=None, compare=None):
        """Make a solver that solves for the specified parmgroup, by comparing its
        matrices with the corresponding matrices of another Matrix22 object."""
        quals = self.quals()
        qother = other._quals.concat()        # -> one string, with _ between quals

        # Get the list of solvable MeqParm nodes:
        # ONLY from the other Matrix22 object, NOT from this one.....(?)
        # keys = other.pgm().solvable_groups()
        if not other._pgm._parmgroup.has_key(parmgroup):
            print '** parmgroup (',parmgroup,') not recognised in:',other._pgm._parmgroup.keys()
            return False
        pg = other._pgm._parmgroup[parmgroup]
        solvable = pg.nodelist()

        # Get the names of the (subset of) matrix elements to be used:
        # (e.g. for GJones, we only use ['m11','m22'], etc)
        matrel = self._matrel.keys()          # i.e. ['m11','m12','m21','m22']
        if True:
            matrel = pg.rider('matrel')
            if matrel=='*': matrel = self._matrel.keys()
        # matrel = ['m11','m22']

        # Make a list of condeq nodes:
        condeq_copy = self.copy()
        condeqs = condeq_copy.make_condeqs (other, matrel=matrel, replace=True)

        # Create the solver
        cc = []
        solver = self._ns.solver(*quals)(qother) << Meq.Solver(children=condeqs,
                                                         solvable=pg.nodelist())
        cc.append(solver)
        JEN_bookmarks.create(solver, page='solver')

        # Visualize the condeqs and the solvable MeqParms:
        cc.append(condeq_copy.visualize(matrel=matrel))

        # Return the ReqSeq node that bundles solving and visualisation: 
        reqseq = self._ns.reqseq_solver(*quals)(qother) << Meq.ReqSeq(children=cc)
        return reqseq
        
    

    #=====================================================================
    # Test module:
    #=====================================================================

    def test (self):
        """Helper function to make some test-matrices"""
        quals = self.quals()
        name = 'matrix22'
        keys = self._matrel.keys()
        index = 0
        indices = []
        for key in keys:
            index += 1
            indices.append(index)
            self._pgm.define_parmgroup(key, descr='matrix element: '+key,
                                       default=index/10.0,
                                       # stddev=0.01,
                                       tags=['test'])
            mm = dict(m11=0.0, m12=0.0, m21=0.0, m22=0.0)
            mm[key] = self._pgm.create_parmgroup_entry(key, index)
            mm[key] = self._ns << Meq.Polar(1.0,mm[key])
            mat = self._ns[name](*quals)(index) << Meq.Matrix22(mm['m11'],mm['m12'],
                                                                mm['m21'],mm['m22'])
        # Store the matrices and the list if indices:
        self.indices(new=indices)
        self.matrix(new=self._ns[name](*quals))

        # Make some secondary (composite) ParmGroups:
        self._pgm.define_gogs()
        return True







     
#===============================================================
# Test routine (with meqbrowser):
#===============================================================

def _define_forest(ns):

    cc = []
    simulate = True

    mat1 = Matrix22(ns, quals=[], simulate=True)
    mat1.test()
    cc.append(mat1.visualize())
    mat1.display(full=True)

    mat2 = Matrix22(ns, quals=[], simulate=False)
    mat2.test()
    cc.append(mat2.visualize())
    mat2.display(full=True)

    reqseq = mat1.make_solver('*', mat2)
    cc.append(reqseq)

    ns.result << Meq.ReqSeq(children=cc)
    return True

#---------------------------------------------------------------

def _tdl_job_execute (mqs, parent):
    """Execute the forest, starting at the named node"""
    domain = meq.domain(1.0e8,1.1e8,1,10)                            # (f1,f2,t1,t2)
    cells = meq.cells(domain, num_freq=10, num_time=11)
    request = meq.request(cells, rqtype='ev')
    result = mqs.meq('Node.Execute',record(name='result', request=request))
    return result
       


#===============================================================
# Test routine:
#===============================================================

if __name__ == '__main__':
    ns = NodeScope()

    if 1:
        m1 = Matrix22(ns, quals=['3c84','xxx'], label='HH', simulate=True)
        m1.test()
        m1.visualize()
        # m1.display_parmgroups(full=False)
        m1.display(full=True)

    if 0:
        mc = m1.copy()
        mc.display('copy', full=True)

    if 0:
        m1.unop('Cos')
        m1.display('after unop', full=True)
        
    if 1:
        m2 = Matrix22(ns, quals=['3c84','yyy'], label='TT', simulate=False)
        m2.test()
        m2.display('m2',full=True)

        if 0:
            m1.binop('Subtract',m2)
            m1.display('after binop', full=True)
        
        if 1:
            reqseq = m1.make_solver('*',m2)
            m1._dummyParmGroup.display_subtree (reqseq, txt='solver_reqseq',
                                                show_initrec=False, recurse=3)
        
        if 0:
            mc = m1.copy()
            matrel = '*'
            matrel = ['m11','m22']
            cc = mc.make_condeqs(m2, matrel=matrel, replace=True)
            print ' -> nr of condeqs:',len(cc)
            for i in range(4):
                mc._dummyParmGroup.display_subtree (cc[i], txt='condeq'+str(i), recurse=2)
            mc.visualize(matrel=matrel)
            mc.display('make_condeqs', full=True)
            # m1.display('make_condeqs', full=True)
        

    if 0:
        nn = m1.matrix_element(return_nodes=False)
        m1.display(full=True)
        print '\n** matrix_element result:'
        for s in m1.indices():
            print '--',s,':',nn(s)
        print '-- (',6,'):',nn(6)     # !!
        print
        nn = m1.matrix_element(return_nodes=True)

    if 0:
        m1.matrix_element('m11')
        m1.matrix_element('m12')
        m1.matrix_element('m21')
        m1.matrix_element('m22')
        m1.display(full=True)


#===============================================================
    
