
#% $Id$ 

#
# Copyright (C) 2002-2007
# ASTRON (Netherlands Foundation for Research in Astronomy)
# and The MeqTree Foundation
# P.O.Box 2, 7990 AA Dwingeloo, The Netherlands, seg@astron.nl
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

from qt import *
import numpy
import sys
try:
  from Qwt4 import *
except:
  from qwt import *

class QwtPlotCurveSizes(QwtPlotCurve):
    """ A QwtCurve with adjustable Symbols """

    def __init__(self,parent,title=""):
      QwtPlotCurve.__init__(self,parent,title)
      self.symbolSizes = None
      self.symbolList = None

    # __init__()

    def setData(self, xData, yData, symbolSizes=None):
      """ Override default QwtCurve setData method """
      self.symbolSizes = symbolSizes
      QwtPlotCurve.setData(self,xData,yData)
      QwtPlotCurve.curveChanged(self)

    def setSymbolList(self, symbolList):
      """ Override default QwtCurve symbols """
      self.symbolList = symbolList

    def drawSymbols(self, painter, symbol, xMap, yMap, start, to):
      if self.symbolList is None and self.symbolSizes is None:
        print 'QwtPlotCurveSizes fail: you must specify a symbol list or an array of symbol sizes'
        return
      painter.setBrush(symbol.brush());
      painter.setPen(symbol.pen())
      rect = QRect()
      for i in range(start, to+1):
        if not self.symbolList is None:
          painter.setBrush(self.symbolList[i].brush());
          painter.setPen(self.symbolList[i].pen())
# the following screenToLayout call should work but does not
#       symbol_size = QSize(self.symbolSizes[i], self.symbolSizes[i])
#       rect.setSize(QwtPainter.metricsMap().screenToLayout(symbol_size));

# so we do the following 
        if not self.symbolList is None:
          width = self.symbolList[i].size().width()
          height = self.symbolList[i].size().height()
          sizex = QwtPainter.metricsMap().screenToLayoutX(width)
          sizey = QwtPainter.metricsMap().screenToLayoutY(height)
        else:
          sizex = QwtPainter.metricsMap().screenToLayoutX(self.symbolSizes[i])
          sizey = QwtPainter.metricsMap().screenToLayoutY(self.symbolSizes[i])
        rect.setSize(QSize(sizex, sizey))

        xi = xMap.transform(self.x(i));
        yi = yMap.transform(self.y(i));
        rect.moveCenter(QPoint(xi, yi));
        if not self.symbolList is None:
          self.symbolList[i].draw(painter, rect);
        else:
          symbol.draw(painter, rect);
    # drawSymbols()

# class QwtPlotCurveSizes()

def make():
    demo = QwtPlot('symbols demo')
    curve = QwtPlotCurveSizes(parent=demo)
    curve_a = QwtPlotCurveSizes(parent=demo)
    # need to create a default symbol for the curves due to inner
    # workings of QwtCurve 
    curve.setSymbol(QwtSymbol(QwtSymbol.Ellipse,
             QBrush(Qt.black), QPen(Qt.black), QSize(5,5)))
    curve.setPen(QPen(Qt.blue, 2))
    curve_a.setSymbol(QwtSymbol(QwtSymbol.Ellipse,
             QBrush(Qt.black), QPen(Qt.black), QSize(5,5)))
    curve_a.setPen(QPen(Qt.blue, 2))

    # create some data
    x_array = numpy.zeros(20, numpy.float32)
    y_array = numpy.zeros(20, numpy.float32)
    symbol_sizes = numpy.zeros(20, numpy.int32)
    symbolList=[]
    for i in range(20):
      x_array[i] = 1.0 * i
      y_array[i] = 2.0 * i
      symbol_sizes[i] = 3 + i
      if i%2 == 0:
        symbolList.append(QwtSymbol(QwtSymbol.UTriangle,
             QBrush(Qt.black), QPen(Qt.black), QSize(3+i,3+i)))
      else:
        symbolList.append(QwtSymbol(QwtSymbol.DTriangle,
             QBrush(Qt.red), QPen(Qt.red), QSize(3+i,3+i)))
    curve.setData(x_array,y_array,symbol_sizes)
    key = demo.insertCurve(curve)
    x_array = x_array + 10
    curve_a.setData(x_array,y_array)
    curve_a.setSymbolList(symbolList)
    key1 = demo.insertCurve(curve_a)
    demo.replot()
    return demo

def main(args):
    app = QApplication(args)
    demo = make()
    demo.show()
    app.setMainWidget(demo)
    app.exec_loop()

# Admire
if __name__ == '__main__':
    main(sys.argv)
