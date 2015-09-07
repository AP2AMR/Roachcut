#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtCore,QtGui
from roachcut_core import *

app = QtGui.QApplication(sys.argv)
settings = QtCore.QSettings("linuxac.org","TuxCut")
translator = QtCore.QTranslator()

lang = settings.value("Language","English")
print lang

roach = RoachCut()
sys.exit(app.exec_())
