#/usr/bin/python
#
#% $Id: connect_meqtimba_dialog.py 6778 2009-02-19 14:00:37Z oms $ 
#
#
# Copyright (C) 2002-2007
# The MeqTree Foundation & 
# ASTRON (Netherlands Foundation for Research in Astronomy)
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>,
# or write to the Free Software Foundation, Inc., 
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import Timba
from Timba.GUI import meqgui
from Timba.GUI.pixmaps import pixmaps
from qt import *

MEQTREE_VERSION  = "1.0";

class AboutDialog (QDialog):
    def __init__(self,parent=None,name=None,modal=0,fl=None):
        if fl is None:
          fl = Qt.WType_TopLevel|Qt.WStyle_Customize;
          fl |= Qt.WStyle_DialogBorder|Qt.WStyle_Title;
        
        QDialog.__init__(self,parent,name,modal,fl)
        
        image0 = pixmaps.redhood_300.pm();

        # self.setSizeGripEnabled(0)
        LayoutWidget = QWidget(self,"lo_top")
        LayoutWidget.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding);
        
        lo_top = QVBoxLayout(LayoutWidget,11,6,"lo_top")

        lo_title = QHBoxLayout(None,0,6,"lo_title")

        self.title_icon = QLabel(LayoutWidget,"title_icon")
        self.title_icon.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed,self.title_icon.sizePolicy().hasHeightForWidth()))
        self.title_icon.setPixmap(image0)
        self.title_icon.setAlignment(QLabel.AlignCenter)
        lo_title.addWidget(self.title_icon)

        self.title_label = QLabel(LayoutWidget,"title_label")
        lo_title.addWidget(self.title_label)
        lo_top.addLayout(lo_title)
        
        if Timba.packages():
          lo_pkgs = QHBoxLayout(None,0,6,"lo_pkgs")
          lo_top.addLayout(lo_pkgs);
          self.pkg_label = QLabel(LayoutWidget,"pkg_label")
          self.pkg_label.setFrameStyle(QFrame.Box|QFrame.Raised);
          lo_pkgs.addWidget(self.pkg_label);
          txt = """<P>Optional packages:</P><TABLE>""";
          for pkg,path in Timba.packages().iteritems():
            txt += "<TR><TD>%s</TD><TD>%s</TD></TR>"""%(pkg,path);
          self.pkg_label.setText(txt);
        
        lo_logos = QHBoxLayout(None,0,6,"lo_logos")
        lo_top.addLayout(lo_logos);
        for logo in "astron","oxford_physics","oerc","drao":
          icon = QLabel(LayoutWidget)
          icon.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed,self.title_icon.sizePolicy().hasHeightForWidth()))
          icon.setPixmap(getattr(pixmaps,logo+"_logo").pm());
          icon.setAlignment(QLabel.AlignCenter)
          lo_logos.addWidget(icon)

        lo_mainbtn = QHBoxLayout(None,0,6,"lo_mainbtn")
        lo_mainbtn.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))
        lo_top.addLayout(lo_mainbtn);

        self.btn_ok = QPushButton(LayoutWidget,"btn_ok")
        self.btn_ok.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed,1,0,self.btn_ok.sizePolicy().hasHeightForWidth()))
        self.btn_ok.setMinimumSize(QSize(60,0))
        self.btn_ok.setAutoDefault(1)
        self.btn_ok.setDefault(1)
        lo_mainbtn.addWidget(self.btn_ok)
        lo_mainbtn.addItem(QSpacerItem(20,20,QSizePolicy.Expanding,QSizePolicy.Minimum))

        self.languageChange()
        
        LayoutWidget.adjustSize();

        #LayoutWidget.resize(QSize(489,330).expandedTo(LayoutWidget.minimumSizeHint()))
        #self.resize(QSize(489,330).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)
        
        self.connect(self.btn_ok,SIGNAL("clicked()"),self.accept)
        
    def languageChange(self):
        self.setCaption(self.__tr("About MeqTrees"))
        self.title_icon.setText(QString.null)
        self.title_label.setText(self.__tr( \
          """<h1>MeqTrees %s</h1>
          <p>(C) 2002-2009 ASTRON<br>(Netherlands Institude for Radioastronomy)<br>
          Oude Hoogeveensedijk 4<br>
          7991 PD Dwingeloo, The Netherlands<br>
          http://www.astron.nl</p>
          <p>With contributions from:<p><ul>
          <li>Dominion Radio Astrophysical Observatory (NRC-HIA)</li>
          <li>Oxford e-Research Centre<li>
          <li>Oxford Astrophysics<li>
          <li>Sarod Yatawatta, Tony Willis, Maaijke Mevius,
          Ger van Diepen, Ronald Nijboer, Filipe Abdalla, Rob Assendorp, Ilse
          van Bemmel, Ian Heywood, Hans-Rainer Kloeckner, Rense Boomsma, Michiel
          Brentjens, Joris van Zwieten, Stef Salvini, Christopher Williams, Mike Sipior,
          James Anderson, George Heald,  Jan Noordam, Oleg Smirnov
          </ul>
          """%MEQTREE_VERSION \
          ));

        self.btn_ok.setText(self.__tr("&OK"))
        self.btn_ok.setAccel(QString.null)


    def __tr(self,s,c = None):
        return qApp.translate("ConnectMeqKernel",s,c)

