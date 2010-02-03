'''
Created on 1 Feb 2010

@author: Mike Thomas

'''
from ui_Betty_MainWindow import Ui_Betty_MainWindow
from PyQt4.QtGui import (QMainWindow, QApplication,
                         QMessageBox, QFileDialog)
from PyQt4.QtCore import pyqtSignature, QString, SIGNAL, QFileInfo, QDate, QTime
import sys
from Model.RaceModel import RaceModel
from Model import Chance

def setCombo(combo, itemText):
    itemList = [unicode(combo.itemText(i)) for
        i in xrange(0, combo.count())]
    if itemText in itemList:
        combo.setCurrentIndex(itemList.index(itemText))
    else:
        combo.addItem(itemText)
        combo.setCurrentIndex(combo.count() - 1)

class BettyMain(QMainWindow, Ui_Betty_MainWindow):
    '''
    classdocs
    '''

    __formatExtension = "*.bty"

    def __init__(self, filename = None, parent = None):
        '''
        Constructor
        '''
        super(BettyMain, self).__init__(parent)
        self.filename = filename
        self.model = RaceModel(filename)
        self.setupUi(self)
        self.deleteButton.setEnabled(False)
        self.raceTable.setModel(self.model)
        self.connect(self.model, SIGNAL("rowsInserted(QModelIndex,int,int)"),
                     self.check_deleteButton)
        self.connect(self.model, SIGNAL("rowsRemoved(QModelIndex,int,int)"),
                     self.check_deleteButton)
        self.resizeColumns()
        self.populateInfo()

    def resizeColumns(self):
        self.raceTable.resizeColumnsToContents()

    def populateInfo(self):
        self.nameEdit.setText(self.model.racename)
        setCombo(self.courseCombo, self.model.course)
        setCombo(self.classCombo, self.model.raceclass)
        self.prizeSpinner.setValue(self.model.prize)
        if self.model.date is None:
            self.dateEdit.setDate(QDate.currentDate())
        else:
            self.dateEdit.setDate(QDate.fromString(self.model.date))
        if self.model.time is None:
            self.timeEdit.setTime(QTime(12, 0))
        else:
            self.timeEdit.setTime(QTime.fromString(self.model.time))
        miles = self.model.distance / 8
        furlongs = self.model.distance % 8
        self.milesSpinner.setValue(miles)
        self.furlongCombo.setCurrentIndex(furlongs)

    @pyqtSignature("")
    def on_addButton_clicked(self):
        row = self.model.rowCount()
        self.model.insertRows(row)
        index = self.model.index(row, 0)
        self.raceTable.setCurrentIndex(index)
        #self.raceTable.edit(index)

    @pyqtSignature("")
    def on_deleteButton_clicked(self):
        index = self.raceTable.currentIndex()
        if not index.isValid():
            return
        row = index.row()
        name = self.model.data(self.model.index(row, 0)).toString()
        if QMessageBox.question(self, "Remove Horse",
                                QString("Remove horse %1").arg(name),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
            return
        self.model.removeRows(row)
        self.resizeColumns()

    @pyqtSignature("")
    def on_decimalButton_clicked(self):
        self.model.setOddsDisplay(Chance.DecimalOddsDisplay)

    @pyqtSignature("")
    def on_betfairButton_clicked(self):
        self.model.setOddsDisplay(Chance.BetfairOddsDisplay)

    @pyqtSignature("")
    def on_fractionalButton_clicked(self):
        self.model.setOddsDisplay(Chance.FractionalOddsDisplay)

    @pyqtSignature("QString")
    def on_nameEdit_textChanged(self):
        self.model.racename = unicode(self.nameEdit.text())

    @pyqtSignature("QString")
    def on_courseCombo_activated(self):
        self.model.course = unicode(self.courseCombo.currentText())

    @pyqtSignature("QString")
    def on_courseCombo_editTextChanged(self, text):
        self.model.course = unicode(text)

    @pyqtSignature("QString")
    def on_classCombo_activated(self):
        self.model.raceclass = unicode(self.classCombo.currentText())

    @pyqtSignature("int")
    def on_milesSpinner_valueChanged(self):
        self.model.distance = self.calculateDistance()

    @pyqtSignature("QString")
    def on_furlongCombo_activated(self):
        self.model.distance = self.calculateDistance()

    def calculateDistance(self):
        return int(self.milesSpinner.value()) * 8 + self.furlongCombo.currentIndex()

    @pyqtSignature("QString")
    def on_classCombo_editTextChanged(self, text):
        self.model.raceclass = unicode(text)

    @pyqtSignature("QDate")
    def on_dateEdit_dateChanged(self, date):
        self.model.date = unicode(date.toString())

    @pyqtSignature("QTime")
    def on_timeEdit_timeChanged(self, time):
        self.model.time = unicode(time.toString())

    @pyqtSignature("int")
    def on_prizeSpinner_valueChanged(self):
        self.model.prize = int(self.prizeSpinner.value())

    @pyqtSignature("")
    def on_actionNew_triggered(self):
        self.newRace()

    @pyqtSignature("")
    def on_actionSave_triggered(self):
        self.fileSave()

    @pyqtSignature("")
    def on_actionSaveAs_triggered(self):
        self.fileSaveAs()

    @pyqtSignature("")
    def on_actionOpen_triggered(self):
        self.fileOpen()

    def okToContinue(self):
        if not self.model.dirty:
            return True
        reply = QMessageBox.question(self, "Betty - Unsaved Changes",
                                     "Save unsaved changes?",
                                     buttons = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                     defaultButton = QMessageBox.Yes)
        if reply == QMessageBox.Cancel:
            return False
        elif reply == QMessageBox.Yes:
            self.fileSave()
        return True

    def newRace(self):
        if not self.okToContinue():
            return
        self.model.newRace()
        self.populateInfo()
        self.resizeColumns()

    def fileSave(self, filename = None):
        if filename is None:
            filename = self.model.filename
        if filename is None:
            self.fileSaveAs()
        else:
            if not self.model.save(filename):
                QMessageBox.warning(self, "File Error", "Could not save %s" % filename)

    def fileSaveAs(self):
        path = QFileInfo(self.model.filename).path() if self.model.filename is not None else "."
        filename = QFileDialog.getSaveFileName(self,
                                               "Betty - Save Race As",
                                               path,
                                               "Betty files (%s)" % self.__formatExtension)
        if not filename.isEmpty():
            if not filename.contains("."):
                filename += self.__formatExtension
            self.fileSave(filename)

    def fileOpen(self, filename = None):
        if not self.okToContinue():
            return
        path = QFileInfo(filename).path() if filename is not None else "."
        filename = QFileDialog.getOpenFileName(self,
                                               "Betty - Load Race",
                                               path,
                                               "Betty files (%s)" % self.__formatExtension)
        if not filename.isEmpty():
            if self.model.load(unicode(filename)):
                self.populateInfo()
                self.resizeColumns()
            else:
                QMessageBox.warning(self, "File Error", "Could not load %s" % filename)



    def check_deleteButton(self):
        if(self.model.rowCount() > 2):
            self.deleteButton.setEnabled(True)
        else:
            self.deleteButton.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = BettyMain()
    main.show()
    app.exec_()