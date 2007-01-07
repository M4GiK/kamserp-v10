#Autogenerated by ReportLab guiedit do not edit
from reportlab.graphics.shapes import _DrawingEditorMixin
from reportlab.graphics.charts.slidebox import SlideBox
from rlextra.graphics.guiedit.datacharts import ODBCDataSource, CSVDataSource, DataAssociation, DataAwareDrawing

class SlideBoxDrawing(_DrawingEditorMixin,DataAwareDrawing):
    def __init__(self,width=400,height=200,*args,**kw):
        apply(DataAwareDrawing.__init__,(self,width,height)+args,kw)
        self._add(self,SlideBox(),name='SlideBox',validate=None,desc='The main chart')
        self.height          = 40
        self.width           = 168
        #self.dataSource = ODBCDataSource()
        self.dataSource = CSVDataSource()
        self.dataSource.filename = 'slidebox.csv'
        self.dataSource.integerColumns = ['chartId','value','numberOfBoxes']
        self.dataSource.sql  = 'SELECT chartId,numberOfBoxes,label,value FROM generic_slidebox'
        self.dataSource.associations.size = 4
        self.dataSource.associations.element00 = DataAssociation(column=0, target='chartId', assocType='scalar')
        self.dataSource.associations.element01 = DataAssociation(column=1, target='SlideBox.numberOfBoxes', assocType='scalar')
        self.dataSource.associations.element02 = DataAssociation(column=2, target='SlideBox.sourceLabelText', assocType='scalar')
        self.dataSource.associations.element03 = DataAssociation(column=3, target='SlideBox.trianglePosition', assocType='scalar')
        self.verbose         = 1
        self.formats         = ['eps', 'pdf']
        self.outDir          = './output/'
        self.fileNamePattern = 'slidebox%03d'


if __name__=="__main__": #NORUNTESTS
    SlideBoxDrawing().go()
