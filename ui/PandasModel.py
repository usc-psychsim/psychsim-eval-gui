"""
Model used to display pandas dataframes in qt tableview widget
# useful documentation on custom models: https://www.learnpyqt.com/courses/model-views/qtableview-modelviews-numpy-pandas/

"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *

class PandasModel(QAbstractTableModel):

    def __init__(self, data, diff=None, diff_colour="blue"):
        QAbstractTableModel.__init__(self)
        self._data = data
        self._diff = diff
        self._diff_colour = diff_colour

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
            if self._diff is not None and role == Qt.BackgroundRole:
                row = index.row()
                col = index.column()
                diff_val = self._diff.iloc[index.row(), index.column()]#.iloc[index.row()][index.column()]
                if not diff_val: # colour if the diff value is FALSE (i.e. the values aren't the same between the two dataframes)
                    return QColor(self._diff_colour)

        return None

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])