#!/usr/bin/env python

######################################################################
############# Dialog to change user options on plotting the LSM
######################################################################

from qt import *
from Timba.Meq import meq
import sys

class OptionsDialog(QDialog):
    def __init__(self,parent = None,name = "Change Options",modal = 1,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)
        self.setName("Change Options")
        self.setSizeGripEnabled(1)

        LayoutWidget = QVBoxLayout(self,11,6,"OuterLayout")
        self.tabWidget = QTabWidget(self,"tabWidget")

        # remember what has changed
        self.axes_changed=0
        self.turn_gridon=-1
        self.turn_legendon=-1
        self.display_source_type=-1
        self.coord_radians=-1
        self.plot_z_type=-1 # 0:brightness, 1,2,3,4,=IQUV

        self.cell_has_changed=0
################# Tab 1
        self.axisTab=QWidget(self.tabWidget,"axisTab")

        axistabLayout=QVBoxLayout(self.axisTab,11,6,"axistabLayout")

        layoutH=QHBoxLayout(None,0,6,"layoutH")
        axistabLayout.addLayout(layoutH)
        ################
        self.markerBG=QButtonGroup(self.axisTab,"markerBG")
        self.markerBG.setColumnLayout(0,Qt.Vertical)
        self.markerBG.layout().setSpacing(6)
        self.markerBG.layout().setMargin(6)
        bgLayout=QVBoxLayout(self.markerBG.layout())
        bgLayout.setAlignment(Qt.AlignCenter)

        layoutbgV=QVBoxLayout(None,0,6,"layoutbgV")
        self.marker_rad=QRadioButton(self.markerBG,"radian")
        layoutbgV.addWidget(self.marker_rad)
        self.marker_deg=QRadioButton(self.markerBG,"degrees")
        layoutbgV.addWidget(self.marker_deg)
        bgLayout.addLayout(layoutbgV)

        layoutH.addWidget(self.markerBG)

        if self.parentWidget().cview.default_coords=='rad':
         self.marker_rad.setChecked(1)
        else:
         self.marker_deg.setChecked(1)
        self.connect(self.markerBG, SIGNAL("clicked(int)"), self.markerBGradioClick)

        ###############
        self.gridBG=QButtonGroup(self.axisTab,"gridBG")
        self.gridBG.setColumnLayout(0,Qt.Vertical)
        self.gridBG.layout().setSpacing(6)
        self.gridBG.layout().setMargin(6)
        bgLayout=QVBoxLayout(self.gridBG.layout())
        bgLayout.setAlignment(Qt.AlignCenter)

        layoutbgV=QVBoxLayout(None,0,6,"layoutbgV")
        self.grid_ON=QRadioButton(self.gridBG,"gridon")
        layoutbgV.addWidget(self.grid_ON)
        self.grid_OFF=QRadioButton(self.gridBG,"gridoff")
        layoutbgV.addWidget(self.grid_OFF)
        bgLayout.addLayout(layoutbgV)


        layoutH.addWidget(self.gridBG)
        if(self.parentWidget().cview.grid_on==1):
         self.grid_ON.setChecked(1)
        else:
         self.grid_OFF.setChecked(1)

        self.connect(self.gridBG, SIGNAL("clicked(int)"), self.gridBGradioClick)
        #################
        self.xticksBG=QGroupBox(self.axisTab,"xticksBG")
        self.xticksBG.setColumnLayout(0,Qt.Vertical)
        self.xticksBG.layout().setSpacing(6)
        self.xticksBG.layout().setMargin(11)
        xticksLayout= QHBoxLayout(self.xticksBG.layout())
        xticksLayout.setAlignment(Qt.AlignCenter)

        self.textLabel_xspace = QLabel(self.xticksBG,"textLabel_xspace")
        xticksLayout.addWidget(self.textLabel_xspace)

        self.lineEdit_xspace = QLineEdit(self.xticksBG,"lineEdit_xspace")
        tempstr='%9.7f'%((self.parentWidget().cview.x_max-self.parentWidget().cview.x_min)/self.parentWidget().cview.xdivs)
        self.lineEdit_xspace.setText(tempstr)
        self.lineEdit_xspace.setReadOnly(1)
        xticksLayout.addWidget(self.lineEdit_xspace)
        spacer = QSpacerItem(31,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        xticksLayout.addItem(spacer)
        self.connect( self.lineEdit_xspace, SIGNAL("textChanged(const QString &)"), self.lineEditXspace)

        self.textLabel_xticks = QLabel(self.xticksBG,"textLabel_xticks")
        xticksLayout.addWidget(self.textLabel_xticks)

        self.lineEdit_xticks = QLineEdit(self.xticksBG,"lineEdit_xticks")
        self.lineEdit_xticks.setText(str(self.parentWidget().cview.xdivs))
        xticksLayout.addWidget(self.lineEdit_xticks)
        self.connect( self.lineEdit_xticks, SIGNAL("textChanged(const QString &)"), self.lineEditXticks )

        axistabLayout.addWidget(self.xticksBG)
        ################################### 
        self.yticksBG=QGroupBox(self.axisTab,"yticksBG")
        self.yticksBG.setColumnLayout(0,Qt.Vertical)
        self.yticksBG.layout().setSpacing(6)
        self.yticksBG.layout().setMargin(11)
        yticksLayout= QHBoxLayout(self.yticksBG.layout())
        yticksLayout.setAlignment(Qt.AlignCenter)

        self.textLabel_yspace = QLabel(self.yticksBG,"textLabel_yspace")
        yticksLayout.addWidget(self.textLabel_yspace)

        self.lineEdit_yspace = QLineEdit(self.yticksBG,"lineEdit_yspace")
        tempstr='%9.7f'%((self.parentWidget().cview.y_max-self.parentWidget().cview.y_min)/self.parentWidget().cview.ydivs)
        self.lineEdit_yspace.setText(tempstr)
        self.lineEdit_yspace.setReadOnly(1)
        yticksLayout.addWidget(self.lineEdit_yspace)
        self.connect( self.lineEdit_yspace, SIGNAL("textChanged(const QString &)"), self.lineEditYspace)
        spacer = QSpacerItem(31,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        yticksLayout.addItem(spacer)

        self.textLabel_yticks = QLabel(self.yticksBG,"textLabel_yticks")
        yticksLayout.addWidget(self.textLabel_yticks)

        self.lineEdit_yticks = QLineEdit(self.yticksBG,"lineEdit_yticks")
        self.lineEdit_yticks.setText(str(self.parentWidget().cview.ydivs))
        self.connect( self.lineEdit_yticks, SIGNAL("textChanged(const QString &)"), self.lineEditYticks)
        yticksLayout.addWidget(self.lineEdit_yticks)

        axistabLayout.addWidget(self.yticksBG)
        ################################### 
        self.fontBG= QGroupBox(self.axisTab,"fontBG")
        self.fontBG.setColumnLayout(0,Qt.Vertical)
        self.fontBG.layout().setSpacing(6)
        self.fontBG.layout().setMargin(11)
        fontBGLayout = QVBoxLayout(self.fontBG.layout())
        fontBGLayout.setAlignment(Qt.AlignCenter)

        self.fontButton= QPushButton(self.fontBG,"fontToolButton")
        fontBGLayout.addWidget(self.fontButton)
 
        self.connect( self.fontButton, SIGNAL("clicked()"), self.parentWidget().cview.chooseFont)

        axistabLayout.addWidget(self.fontBG)
        ####################################
        self.tabWidget.insertTab(self.axisTab,QString.fromLatin1(""))

################### Tab 2
        self.displayTab=QWidget(self.tabWidget,"displayTab")
        displaytabLayout=QVBoxLayout(self.displayTab,11,6,"displaytabLayout")
  
        ######## Group 1
        self.sourceBG=QButtonGroup(self.displayTab,"sourceBG")
        self.sourceBG.setColumnLayout(0,Qt.Vertical)
        self.sourceBG.layout().setSpacing(6)
        self.sourceBG.layout().setMargin(6)
        bgLayout=QVBoxLayout(self.sourceBG.layout())
        bgLayout.setAlignment(Qt.AlignCenter)

        layoutbgV=QVBoxLayout(None,0,6,"layoutbgV")
        self.source_point=QRadioButton(self.sourceBG,"points")
        layoutbgV.addWidget(self.source_point)
        self.source_cross=QRadioButton(self.sourceBG,"crosses")
        layoutbgV.addWidget(self.source_cross)
        self.source_ext=QRadioButton(self.sourceBG,"extended")
        layoutbgV.addWidget(self.source_ext)
        bgLayout.addLayout(layoutbgV)
        displaytabLayout.addWidget(self.sourceBG)

        if self.parentWidget().cview.display_point_sources=='cross':
         self.source_cross.setChecked(1)
        elif self.parentWidget().cview.display_point_sources=='point':
         self.source_point.setChecked(1)
        else:
         self.source_ext.setChecked(1)

        self.connect(self.sourceBG, SIGNAL("clicked(int)"), self.sourceBGradioClick)
        ######## Group 2
        self.legendBG=QButtonGroup(self.displayTab,"legendBG")
        self.legendBG.setColumnLayout(0,Qt.Vertical)
        self.legendBG.layout().setSpacing(6)
        self.legendBG.layout().setMargin(6)
        bgLayout=QVBoxLayout(self.legendBG.layout())
        bgLayout.setAlignment(Qt.AlignCenter)

        layoutbgV=QVBoxLayout(None,0,6,"layoutbgV")
        self.legend_ON=QRadioButton(self.legendBG,"legendON")
        layoutbgV.addWidget(self.legend_ON)
        self.legend_OFF=QRadioButton(self.legendBG,"legendOFF")
        layoutbgV.addWidget(self.legend_OFF)
        bgLayout.addLayout(layoutbgV)
        displaytabLayout.addWidget(self.legendBG)

       
        if self.parentWidget().cview.legend_on==0:
         self.legend_OFF.setChecked(1)
        else:
         self.legend_ON.setChecked(1)
        self.connect(self.legendBG, SIGNAL("clicked(int)"), self.legendBGradioClick)
        ###############################



        self.tabWidget.insertTab(self.displayTab,QString.fromLatin1(""))
################### Tab 3
        self.zTab=QWidget(self.tabWidget,"zTab")
        displaytabLayout=QVBoxLayout(self.zTab,11,6,"ztabLayout")
  
        ######## Group 1
        self.plotBG=QButtonGroup(self.zTab,"sourceBG")
        self.plotBG.setColumnLayout(0,Qt.Vertical)
        self.plotBG.layout().setSpacing(6)
        self.plotBG.layout().setMargin(6)
        bgLayout=QVBoxLayout(self.plotBG.layout())
        bgLayout.setAlignment(Qt.AlignCenter)

        layoutbgV=QVBoxLayout(None,0,6,"layoutbgV")
        self.z_A=QRadioButton(self.plotBG,"zA")
        layoutbgV.addWidget(self.z_A)
        self.z_I=QRadioButton(self.plotBG,"zI")
        layoutbgV.addWidget(self.z_I)
        self.z_Q=QRadioButton(self.plotBG,"zQ")
        layoutbgV.addWidget(self.z_Q)
        self.z_U=QRadioButton(self.plotBG,"zU")
        layoutbgV.addWidget(self.z_U)
        self.z_V=QRadioButton(self.plotBG,"zV")
        layoutbgV.addWidget(self.z_V)
        bgLayout.addLayout(layoutbgV)
        displaytabLayout.addWidget(self.plotBG)

        if self.parentWidget().cview.default_mode=='A':
         self.z_A.setChecked(1)
        elif self.parentWidget().cview.default_mode=='I':
         self.z_I.setChecked(1)
        elif self.parentWidget().cview.default_mode=='Q':
         self.z_Q.setChecked(1)
        elif self.parentWidget().cview.default_mode=='U':
         self.z_U.setChecked(1)
        elif self.parentWidget().cview.default_mode=='V':
         self.z_V.setChecked(1)


        self.connect(self.plotBG, SIGNAL("clicked(int)"), self.plotBGradioClick)
        ######## Group 2
        self.scaleBG=QButtonGroup(self.zTab,"scaleBG")
        self.scaleBG.setColumnLayout(0,Qt.Vertical)
        self.scaleBG.layout().setSpacing(6)
        self.scaleBG.layout().setMargin(6)
        bgLayout=QVBoxLayout(self.scaleBG.layout())
        bgLayout.setAlignment(Qt.AlignCenter)

        layoutbgV=QVBoxLayout(None,0,6,"layoutbgV")
        self.scale_lin=QRadioButton(self.scaleBG,"linear")
        layoutbgV.addWidget(self.scale_lin)
        self.scale_log=QRadioButton(self.scaleBG,"log")
        layoutbgV.addWidget(self.scale_log)
        bgLayout.addLayout(layoutbgV)
        displaytabLayout.addWidget(self.scaleBG)

       
        self.scale_lin.setChecked(1)
        self.connect(self.scaleBG, SIGNAL("clicked(int)"), self.scaleBGradioClick)
        ###############################



        self.tabWidget.insertTab(self.zTab,QString.fromLatin1(""))
################### Tab 4
        self.cellTab=QWidget(self.tabWidget,"cellTab")
        celltabLayout=QVBoxLayout(self.cellTab,11,6,"celltabLayout")

        # get range from LSM
        self.rng=self.parentWidget().lsm.getCellsRange()
        print "got ",self.rng

        ################# Box 1
        self.FrangeBG=QGroupBox(self.cellTab,"FrangeBG")
        self.FrangeBG.setColumnLayout(0,Qt.Vertical)
        self.FrangeBG.layout().setSpacing(6)
        self.FrangeBG.layout().setMargin(11)
        FLayout= QHBoxLayout(self.FrangeBG.layout())
        FLayout.setAlignment(Qt.AlignCenter)

        self.textLabel_f0= QLabel(self.FrangeBG,"textLabel_f0")
        FLayout.addWidget(self.textLabel_f0)

        self.lineEdit_f0= QLineEdit(self.FrangeBG,"lineEdit_f0")
        if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['f0']
        else:
         tmpstr='0'
        self.lineEdit_f0.setText(tmpstr)

        FLayout.addWidget(self.lineEdit_f0)
        spacer = QSpacerItem(31,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        FLayout.addItem(spacer)
        self.connect( self.lineEdit_f0, SIGNAL("textChanged(const QString &)"), self.lineEditF0)

        self.textLabel_f1= QLabel(self.FrangeBG,"textLabel_f1")
        FLayout.addWidget(self.textLabel_f1)

        self.lineEdit_f1= QLineEdit(self.FrangeBG,"lineEdit_f1")
        if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['f1']
        else:
         tmpstr='0'
        self.lineEdit_f1.setText(tmpstr)


        FLayout.addWidget(self.lineEdit_f1)
        spacer = QSpacerItem(31,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        FLayout.addItem(spacer)
        self.connect( self.lineEdit_f1, SIGNAL("textChanged(const QString &)"), self.lineEditF1)


        self.textLabel_fsep= QLabel(self.FrangeBG,"textLabel_fsep")
        FLayout.addWidget(self.textLabel_fsep)

        self.lineEdit_fsep= QLineEdit(self.FrangeBG,"lineEdit_fsep")
        if len(self.rng)>0:
         tmpstr='%d'%self.rng['fstep']
        else:
         tmpstr='0'
        self.lineEdit_fsep.setText(tmpstr)


        FLayout.addWidget(self.lineEdit_fsep)
        self.connect( self.lineEdit_fsep, SIGNAL("textChanged(const QString &)"), self.lineEditFsep)



        celltabLayout.addWidget(self.FrangeBG)
 
        ################# Box 2
        self.TrangeBG=QGroupBox(self.cellTab,"TrangeBG")
        self.TrangeBG.setColumnLayout(0,Qt.Vertical)
        self.TrangeBG.layout().setSpacing(6)
        self.TrangeBG.layout().setMargin(11)
        TLayout= QHBoxLayout(self.TrangeBG.layout())
        TLayout.setAlignment(Qt.AlignCenter)

        self.textLabel_t0= QLabel(self.TrangeBG,"textLabel_t0")
        TLayout.addWidget(self.textLabel_t0)

        self.lineEdit_t0= QLineEdit(self.TrangeBG,"lineEdit_t0")
        if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['t0']
        else:
         tmpstr='0'
        self.lineEdit_t0.setText(tmpstr)


        TLayout.addWidget(self.lineEdit_t0)
        spacer = QSpacerItem(31,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        TLayout.addItem(spacer)
        self.connect( self.lineEdit_t0, SIGNAL("textChanged(const QString &)"), self.lineEditT0)

        self.textLabel_t1= QLabel(self.TrangeBG,"textLabel_t1")
        TLayout.addWidget(self.textLabel_t1)

        self.lineEdit_t1= QLineEdit(self.TrangeBG,"lineEdit_t1")
        if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['t1']
        else:
         tmpstr='0'
        self.lineEdit_t1.setText(tmpstr)


        TLayout.addWidget(self.lineEdit_t1)
        spacer = QSpacerItem(31,31,QSizePolicy.Expanding,QSizePolicy.Minimum)
        TLayout.addItem(spacer)
        self.connect( self.lineEdit_t1, SIGNAL("textChanged(const QString &)"), self.lineEditT1)


        self.textLabel_tsep= QLabel(self.TrangeBG,"textLabel_tsep")
        TLayout.addWidget(self.textLabel_tsep)

        self.lineEdit_tsep= QLineEdit(self.TrangeBG,"lineEdit_tsep")
        if len(self.rng)>0:
         tmpstr='%d'%self.rng['tstep']
        else:
         tmpstr='0'
        self.lineEdit_tsep.setText(tmpstr)


        TLayout.addWidget(self.lineEdit_tsep)
        self.connect( self.lineEdit_tsep, SIGNAL("textChanged(const QString &)"), self.lineEditTsep)



        celltabLayout.addWidget(self.TrangeBG)
 

        self.tabWidget.insertTab(self.cellTab,QString.fromLatin1(""))

############## end of Tabs
        LayoutWidget.addWidget(self.tabWidget)

############## Button Bar
        buttonLayout=QHBoxLayout(None,0,6,"buttonLayout")
        self.buttonHelp = QPushButton(self,"buttonHelp")
        self.buttonHelp.setAutoDefault(1)
        buttonLayout.addWidget(self.buttonHelp)

        Horizontal_Spacing = QSpacerItem(246,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        buttonLayout.addItem(Horizontal_Spacing)

        self.buttonOk = QPushButton(self,"buttonOk")
        self.buttonOk.setAutoDefault(1)
        self.buttonOk.setDefault(1)
        buttonLayout.addWidget(self.buttonOk)

        self.buttonCancel = QPushButton(self,"buttonCancel")
        self.buttonCancel.setAutoDefault(1)
        buttonLayout.addWidget(self.buttonCancel)
######### End of button Bar
        LayoutWidget.addLayout(buttonLayout)

        self.languageChange()

        self.resize(QSize(528,381).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.buttonHelp,SIGNAL("clicked()"),self.help)
        self.connect(self.buttonOk,SIGNAL("clicked()"),self.accept)
        self.connect(self.buttonCancel,SIGNAL("clicked()"),self.reject)


    def languageChange(self):
        self.setCaption(self.__tr("Change Options"))
        self.tabWidget.changeTab(self.axisTab,self.__tr("Axes"))
        self.markerBG.setTitle(self.__tr("Markers"))
        self.marker_rad.setText(self.__tr("Radians"))
        self.marker_deg.setText(self.__tr("Degrees"))
        self.gridBG.setTitle(self.__tr("Grid"))
        self.grid_ON.setText(self.__tr("On"))
        self.grid_OFF.setText(self.__tr("Off"))
        self.xticksBG.setTitle(self.__tr("X Ticks"))
        self.textLabel_xspace.setText(self.__tr("Spacing"))
        self.textLabel_xticks.setText(self.__tr("Count"))
        self.yticksBG.setTitle(self.__tr("Y Ticks"))
        self.textLabel_yspace.setText(self.__tr("Spacing"))
        self.textLabel_yticks.setText(self.__tr("Count"))

        QToolTip.add(self.markerBG,self.__tr("Change Coordinate display","Coords"))
        QWhatsThis.add(self.markerBG,self.__tr("Changes the Display of coordinats"))

        self.fontBG.setTitle(self.__tr("Font"))
        self.fontButton.setText(self.__tr("Choose..."))

        self.tabWidget.changeTab(self.displayTab,self.__tr("Display"))
        self.sourceBG.setTitle(self.__tr("Point Sources"))
        self.source_point.setText(self.__tr("Points"))
        self.source_cross.setText(self.__tr("Crosses"))
        self.source_ext.setText(self.__tr("Proportional Crosses"))
        self.legendBG.setTitle(self.__tr("Legend"))
        self.legend_ON.setText(self.__tr("On"))
        self.legend_OFF.setText(self.__tr("Off"))

        self.tabWidget.changeTab(self.zTab,self.__tr("Z axis"))
        self.plotBG.setTitle(self.__tr("Plot"))
        self.z_A.setText(self.__tr("Apparent Brightness"))
        self.z_I.setText(self.__tr("Stokes I"))
        self.z_Q.setText(self.__tr("Stokes Q"))
        self.z_U.setText(self.__tr("Stokes U"))
        self.z_V.setText(self.__tr("Stokes V"))
        self.scaleBG.setTitle(self.__tr("Scale"))
        self.scale_lin.setText(self.__tr("Linear"))
        self.scale_log.setText(self.__tr("Log"))

        self.tabWidget.changeTab(self.cellTab,self.__tr("Cells"))
        self.FrangeBG.setTitle(self.__tr("Frequency"))
        self.textLabel_f0.setText(self.__tr("Start"))
        self.textLabel_f1.setText(self.__tr("End"))
        self.textLabel_fsep.setText(self.__tr("Step"))
        self.TrangeBG.setTitle(self.__tr("Time"))
        self.textLabel_t0.setText(self.__tr("Start"))
        self.textLabel_t1.setText(self.__tr("End"))
        self.textLabel_tsep.setText(self.__tr("Step"))


        self.buttonHelp.setText(self.__tr("&Help"))
        self.buttonHelp.setAccel(self.__tr("F1"))
        self.buttonOk.setText(self.__tr("&OK"))
        self.buttonOk.setAccel(QString.null)
        self.buttonCancel.setText(self.__tr("&Cancel"))
        self.buttonCancel.setAccel(QString.null)


    def __tr(self,s,c = None):
        return qApp.translate("OptionsDialog",s,c)

    ####################### Callbacks
    def markerBGradioClick(self,id):
     print "marker BG button %d clicked" %id
     self.coord_radians=id


    def gridBGradioClick(self,id):
     print "grid BG button %d clicked" %id
     if id==0:
      self.turn_gridon=1
     else:
      self.turn_gridon=0

    def lineEditXspace(self,newText):
     if newText.length()>0:
      try:
       fval=float(newText.ascii())
       print "Line edit xspace text: %f" % fval
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)

    def lineEditXticks(self,newText):
     print "Line edit xticks text: " + unicode(newText)
     if newText.length()>0:
      try:
       intval=int(newText.ascii())
       print "intval =",intval
       if intval>0:
        self.lineEdit_xticks.setText(str(intval))
        tempstr='%9.7f'%((self.parentWidget().cview.x_max-self.parentWidget().cview.x_min)/intval)
        self.lineEdit_xspace.setText(tempstr)
        self.axes_changed=1
       else:
        raise TypeError
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       self.lineEdit_xticks.setText(str(self.parentWidget().cview.xdivs))

    def lineEditYspace(self,newText):
     print "Line edit yspace text: " + unicode(newText)
#     self.lineEdit_yticks.setText(newText)

    def lineEditYticks(self,newText):
     print "Line edit yticks text: " + unicode(newText)
     if newText.length()>0:
      try:
       intval=int(newText.ascii())
       print "intval =",intval
       if intval>0:
        self.lineEdit_yticks.setText(str(intval))
        tempstr='%9.7f'%((self.parentWidget().cview.y_max-self.parentWidget().cview.y_min)/intval)
        self.lineEdit_yspace.setText(tempstr)
        self.axes_changed=1
       else:
        raise TypeError
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       self.lineEdit_yticks.setText(str(self.parentWidget().cview.ydivs))



    def sourceBGradioClick(self,id):
     self.display_source_type=id
     print "source BG button %d clicked" %id

    def legendBGradioClick(self,id):
     print "legend BG button %d clicked" %id
     if id==0:
      self.turn_legendon=1
     else:
      self.turn_legendon=0




    def plotBGradioClick(self,id):
     self.plot_z_type=id
     print "plot BG button %d clicked" %id

    def scaleBGradioClick(self,id):
     print "scale BG button %d clicked" %id


    def lineEditF0(self,newText):
     print "Line edit F0 text: " + unicode(newText)
     if newText.length()>0:
      try:
       fval=float(newText.ascii())
       self.cell_has_changed=1
       print "Line edit F0 text: %f" % fval
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['f0']
       else:
         tmpstr='0'
       self.lineEdit_f0.setText(tmpstr)



    def lineEditF1(self,newText):
     print "Line edit F1 text: " + unicode(newText)
     if newText.length()>0:
      try:
       fval=float(newText.ascii())
       self.cell_has_changed=1
       print "Line edit F1 text: %f" % fval
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['f1']
       else:
         tmpstr='0'
       self.lineEdit_f1.setText(tmpstr)


    def lineEditFsep(self,newText):
     print "Line edit Fsep text: " + unicode(newText)
     if newText.length()>0:
      try:
       intval=int(newText.ascii())
       self.cell_has_changed=1
       print "Line edit Fsep text: %d" % intval
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       if len(self.rng)>0:
         tmpstr='%d'%self.rng['fstep']
       else:
         tmpstr='0'
       self.lineEdit_fsep.setText(tmpstr)


    def lineEditT0(self,newText):
     print "Line edit T0 text: " + unicode(newText)
     if newText.length()>0:
      try:
       fval=float(newText.ascii())
       self.cell_has_changed=1
       print "Line edit T0 text: %f" % fval
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['t0']
       else:
         tmpstr='0'
       self.lineEdit_t0.setText(tmpstr)


    def lineEditT1(self,newText):
     print "Line edit T1 text: " + unicode(newText)
     if newText.length()>0:
      try:
       fval=float(newText.ascii())
       self.cell_has_changed=1
       print "Line edit T1 text: %f" % fval
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       if len(self.rng)>0:
         tmpstr='%3.2e'%self.rng['t1']
       else:
         tmpstr='0'
       self.lineEdit_t1.setText(tmpstr)


    def lineEditTsep(self,newText):
     print "Line edit Tsep text: " + unicode(newText)
     if newText.length()>0:
      try:
       intval=int(newText.ascii())
       self.cell_has_changed=1
       print "Line edit Tsep text: %d" % intval
      except (TypeError,ValueError):
       print "invalid number "+unicode(newText)
       if len(self.rng)>0:
         tmpstr='%d'%self.rng['tstep']
       else:
         tmpstr='0'
       self.lineEdit_tsep.setText(tmpstr)




    def accept(self):
     print "accept options"
     if self.axes_changed==1:
      xticks=int(self.lineEdit_xticks.text().ascii())
      yticks=int(self.lineEdit_yticks.text().ascii())
      self.parentWidget().cview.updateAxes(xticks,yticks)

     if self.turn_gridon!= -1:
      print "Grid ON %d"%self.turn_gridon
      self.parentWidget().cview.grid_on=self.turn_gridon
      if self.turn_gridon==1:
       self.parentWidget().cview.axes.gridOn()
      else:
       self.parentWidget().cview.axes.gridOff()

     if self.display_source_type != -1:
      print "Source type change %d"%self.display_source_type
      if self.display_source_type==0:
        self.parentWidget().cview.showPointSources(0)
      elif self.display_source_type==1:
        self.parentWidget().cview.showPointSources(1)
      else:
        self.parentWidget().cview.showPointSources(2)

     if self.coord_radians != -1:
      print "Coordinate change %d"%self.coord_radians
      if self.coord_radians==0:
       self.parentWidget().cview.default_coords='rad'
       self.parentWidget().cview.axes.switchCoords('rad')
      else:
       self.parentWidget().cview.default_coords='deg'
       self.parentWidget().cview.axes.switchCoords('deg')

     if self.cell_has_changed==1:
      # create new cell
      newText=self.lineEdit_f0.text()
      try:
        f0=float(newText.ascii())
      except (TypeError,ValueError):
       if len(self.rng)>0:
        f0=self.rng['f0']
       else:
        f0=1.0e6
      newText=self.lineEdit_f1.text()
      try:
        f1=float(newText.ascii())
      except (TypeError,ValueError):
       if len(self.rng)>0:
        f1=self.rng['f1']
       else:
        f1=2.0e6
      newText=self.lineEdit_fsep.text()
      try:
        fsep=int(newText.ascii())
      except (TypeError,ValueError):
       if len(self.rng)>0:
        fsep=self.rng['fstep']
       else:
        fsep=2
      newText=self.lineEdit_t0.text()
      try:
        t0=float(newText.ascii())
      except (TypeError,ValueError):
       if len(self.rng)>0:
        t0=self.rng['t0']
       else:
        t0=1.0e6
      newText=self.lineEdit_t1.text()
      try:
        t1=float(newText.ascii())
      except (TypeError,ValueError):
       if len(self.rng)>0:
        t1=self.rng['t1']
       else:
        t1=2.0e6
      newText=self.lineEdit_tsep.text()
      try:
        tsep=int(newText.ascii())
      except (TypeError,ValueError):
       if len(self.rng)>0:
        tsep=self.rng['tstep']
       else:
        tsep=2
      print "New cell (%f,%f) %d, (%f,%f) %d"% (f0,f1,fsep,t0,t1,tsep)
      freqtime_domain = meq.domain(startfreq=f0, endfreq=f1, starttime=t0, endtime=t1);
      cells =meq.cells(domain=freqtime_domain, num_freq=fsep,  num_time=tsep);
      self.parentWidget().lsm.setCells(cells)
      # draw a progress dialog
      self.parentWidget().lsm.updateCells()
      self.parentWidget().cview.resetFTindices()

     if self.plot_z_type!=-1:
      #0,1,2,3,4: App. brightness, I,Q,U,V
      if self.plot_z_type==0:
       self.parentWidget().cview.updateDisplay('A')
      elif self.plot_z_type==1: 
       self.parentWidget().cview.updateDisplay('I')
      elif self.plot_z_type==2: 
       self.parentWidget().cview.updateDisplay('Q')
      elif self.plot_z_type==3: 
       self.parentWidget().cview.updateDisplay('U')
      elif self.plot_z_type==4: 
       self.parentWidget().cview.updateDisplay('V')

     if  self.turn_legendon!=-1:
      if  self.turn_legendon==1:
       self.parentWidget().cview.showLegend(1)
      else:
       self.parentWidget().cview.showLegend(0)

     self.parentWidget().canvas.update()

     QDialog.accept(self)

    def reject(self):
     print "reject options"
     QDialog.reject(self)


    def help(self):
     print "Not yet implemented"
     pass

def main(args):
  app=QApplication(args)
  win=OptionsDialog(None)
  win.show()
  app.connect(app,SIGNAL("lastWindowClosed()"),
               app,SLOT("quit()"))
  app.exec_loop()

if __name__=="__main__":
   main(sys.argv)
