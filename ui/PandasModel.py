"""
Model used to display pandas dataframes in qt tableview widget
# useful documentation on custom models: https://www.learnpyqt.com/courses/model-views/qtableview-modelviews-numpy-pandas/

"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *

import pandas as pd

class PandasModel(QAbstractTableModel):

    def __init__(self, data, diff=None, diff_colour="blue"):
        QAbstractTableModel.__init__(self)
        self._data = data
        if type(data) == pd.MultiIndex: # This allows hierarchical tree data to be displayed in a table
            self._data = data.to_frame()
        self._diff = diff
        self._diff_colour = diff_colour

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                value = self._data.iloc[index.row(), index.column()]

                if isinstance(value, float):
                    # Render float to 2 dp
                    return "%.3f" % value

                if isinstance(value, str):
                    # Render strings with quotes
                    return '"%s"' % value

                if pd.api.types.is_string_dtype(value):
                    pass


                # return value
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

# https://gist.github.com/danieljfarrell/6e94aa6f8c3c437d901fd15b7b931afb
class CustomNode(object):
    def __init__(self, data):
        self._data = data
        if type(data) == tuple:
            self._data = list(data)
        if type(data) is str or not hasattr(data, '__getitem__'):
            self._data = [data]

        self._columncount = len(self._data)
        self._children = []
        self._parent = None
        self._row = 0

    def data(self, column):
        if column >= 0 and column < len(self._data):
            return self._data[column]

    def columnCount(self):
        return self._columncount

    def childCount(self):
        return len(self._children)

    def child(self, row):
        if row >= 0 and row < self.childCount():
            return self._children[row]

    def parent(self):
        return self._parent

    def row(self):
        return self._row

    def addChild(self, child):
        child._parent = self
        child._row = len(self._children)
        self._children.append(child)
        self._columncount = max(child.columnCount(), self._columncount)


class TreeModel(QAbstractItemModel):
    def __init__(self, data):
        QAbstractItemModel.__init__(self)
        self._root = CustomNode(None)

        self._data = data
        level_group = self._data.groupby(self._data.index.get_level_values(level=0))
        nodes = []
        for level in level_group:
            nodes.append(CustomNode(level))
            for index, row in self._data.iterrows():
                children = [""]
                if index == level[0]:
                    for child in row:
                        children.append(child)
                    nodes[-1].addChild(CustomNode(children))

        for node in nodes:
            self._root.addChild(node)

        # Add back in the column header for the index
        index_name = self._data.index.name
        if index_name:
            self._data.insert(0, index_name, self._data.index)
        else:
            self._data.insert(0, "index", self._data.index)

    def rowCount(self, index):
        if index.isValid():
            return index.internalPointer().childCount()
        return self._root.childCount()

    def addChild(self, node, _parent):
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()
        parent.addChild(node)

    def index(self, row, column, _parent=None):
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()

        if not QAbstractItemModel.hasIndex(self, row, column, _parent):
            return QModelIndex()

        child = parent.child(row)
        if child:
            return QAbstractItemModel.createIndex(self, row, column, child)
        else:
            return QModelIndex()

    def parent(self, index):
        if index.isValid():
            p = index.internalPointer().parent()
            if p:
                return QAbstractItemModel.createIndex(self, p.row(), 0, p)
        return QModelIndex()

    def columnCount(self, index):
        if index.isValid():
            return index.internalPointer().columnCount()
        return self._root.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == Qt.DisplayRole:
            return node.data(index.column())
        return None

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
