# -*- coding: UTF-8 -*-
"""Table with result set."""

from collections import OrderedDict
import pandas as pd

from PyQt5.Qt import QApplication
from PyQt5.Qt import QMainWindow, QAbstractTableModel, QModelIndex
from PyQt5.Qt import Qt, QVariant
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import QTableView, QAbstractItemView

QMODEL_INDEX = QModelIndex()


########################################################################
class Row(object):
    """Row of the returned database result set."""

    # ----------------------------------------------------------------------
    def __init__(self, **kwargs):
        """Initialize Row with basic properties."""
        self.__dict__.update(kwargs)


########################################################################
class ResultTable(QMainWindow):
    """Table with result set returned by SQL query."""

    # ----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Initialize ResultTable with basic layout."""
        super(ResultTable, self).__init__(parent)
        self.view = QTableView()
        self.view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

    # ----------------------------------------------------------------------
    def draw_result(self, result, show_shapes=True):
        """Load and draw result set into the table."""
        self.table_data = ResultTableModel(result, show_shapes)
        self.view.setModel(self.table_data)
        self.setCentralWidget(self.view)
        self.view.installEventFilter(self)
        return

    # ----------------------------------------------------------------------
    def get_selected_data_as_df(self):
        """Get selected data as pandas data frame."""
        # need to read all OGR layer features that were not read yet
        if (self.table_data.number_of_fetched_layer_rows <
                self.table_data.number_layer_rows):
            (rows_fetched,
             number_of_fetched_layer_rows) = self.table_data.get_layer_rows(
                 self.table_data.number_layer_rows -
                 self.table_data.number_of_fetched_layer_rows)

            internal_rows = self.table_data.rows.copy()
            for row in rows_fetched:
                internal_rows.append(row)
            rows_to_export = internal_rows

            # reset the OGR back to where it was
            # based on number of rows at that time
            self.table_data.result.ResetReading()
            for _i in range(len(self.table_data.rows)):
                self.table_data.result.GetNextFeature()

        else:
            rows_to_export = self.table_data.rows

        df = pd.DataFrame.from_records(
            data=[row.__dict__ for row in rows_to_export],
            columns=self.table_data.headers,
            index=range(1,
                        len(rows_to_export) + 1))
        return df

    # ----------------------------------------------------------------------
    def eventFilter(self, src, evt):  # noqa: N802
        """Override built-in for filtering key press events."""
        # on Ctrl-End, load all rows and get to the last row
        if (evt.type() == QtCore.QEvent.KeyPress
                and evt.matches(QtGui.QKeySequence.MoveToEndOfDocument)):
            self.load_all_rows()

        if (evt.type() == QtCore.QEvent.KeyPress
                and evt.matches(QtGui.QKeySequence.Copy)):
            self.copy_selection()
            return True
        return super(ResultTable, self).eventFilter(src, evt)

    # ----------------------------------------------------------------------
    def load_all_rows(self):
        """Load all layer rows into the table view."""
        while len(self.table_data.rows) < self.table_data.number_layer_rows:
            self.table_data.fetchMore()
        return

    # ----------------------------------------------------------------------
    def copy_selection(self):
        """Copy selection done by user in the result grid of cells."""
        view = self.view
        table_data = self.table_data
        selection = self.view.selectedIndexes()
        headers = view.model().headers
        if len(selection) > 1:  # multiple cells are being copied
            output = ''
            headers_to_copy = list(
                OrderedDict([(table_data.headers_index_mapper[idx.column()],
                              idx.column())
                             for idx in selection][:len(headers) + 1]))

            output += '\t'.join(list(headers_to_copy)) + '\n'
            selected_rows = self.chunks(
                [str(cell.data(0)) for cell in selection], len(headers_to_copy))
            for selected_row in selected_rows:
                output += '\t'.join(selected_row)
                output += '\n'
        else:
            output = str(selection[0].data(0))

        clipboard = QApplication.clipboard()
        clipboard.setText(output)
        return

    # ----------------------------------------------------------------------
    @staticmethod
    def chunks(l, n):
        """Split list into number of chunks of given size."""
        for i in range(0, len(l), n):
            yield l[i:i + n]


########################################################################
class ResultTableModel(QAbstractTableModel):
    """Result table model."""

    # ----------------------------------------------------------------------
    def __init__(self, result, show_shapes):
        """Initialize ResultTableModel with the basic settings."""
        super(ResultTableModel, self).__init__()
        self.chunk_size = 200
        self.show_shapes = show_shapes
        self.number_of_fetched_layer_rows = 0
        self.result = result
        self.number_layer_rows = self.get_layer_number_of_rows()
        self.geom_column = self.get_geom_column()
        self.headers = self.get_layer_columns(show_shapes)
        self.rows = []
        self.headers_index_mapper = {
            idx: header
            for idx, header in enumerate(self.headers)
        }

    # ----------------------------------------------------------------------
    def get_layer_number_of_rows(self):
        """Get the number of rows in the returned OGR layer."""
        # TODO: any faster way to count features?
        # on the source tables (select * from streets is fast;
        # on views created on-the-fly is terribly slow)
        return len(self.result)

    # ----------------------------------------------------------------------
    def get_geom_column(self):
        """Get geometry column of the OGR layer."""
        return self.result.GetGeometryColumn()

    # ----------------------------------------------------------------------
    def get_layer_columns(self, show_shapes):
        """Get OGR layer columns that were requested by SQL query."""
        sql_table_columns = [field.GetName() for field in self.result.schema]
        if show_shapes:
            if self.geom_column != '':
                cols_to_add = [self.geom_column]
            else:
                cols_to_add = []
            sql_table_columns += cols_to_add
        return sql_table_columns

    # ----------------------------------------------------------------------
    def get_layer_rows(self, limit):
        """Fetch result rows from an OGR layer, push into table data object."""
        rows_fetched = []
        number_of_fetched_layer_rows = 0
        for _i in range(limit):
            feat = self.result.GetNextFeature()
            if feat:
                attributes = feat.items()
                if self.geom_column and self.show_shapes:
                    geom = feat.geometry()
                    if geom:
                        attributes[self.geom_column] = geom.ExportToWkt()
                rows_fetched.append(Row(**attributes))
            else:
                break
        number_of_fetched_layer_rows += _i + 1

        return rows_fetched, number_of_fetched_layer_rows

    # ----------------------------------------------------------------------
    def rowCount(self, index=QMODEL_INDEX):  # noqa: N802
        """Override built-in method."""
        if not self.rows:
            return 0

        if len(self.rows) <= self.number_layer_rows:
            return len(self.rows)
        else:
            return self.number_layer_rows

    # ----------------------------------------------------------------------
    def canFetchMore(self, index=QMODEL_INDEX):  # noqa: N802
        """Override built-in method."""
        if self.number_layer_rows > len(self.rows):
            return True
        else:
            return False

    # ----------------------------------------------------------------------
    def fetchMore(self, index=QMODEL_INDEX):  # noqa: N802
        """Override built-in method."""
        remainder = self.number_layer_rows - len(self.rows)
        items_to_fetch = min(remainder, self.chunk_size)

        rows_fetched, number_of_fetched_layer_rows = self.get_layer_rows(
            limit=self.chunk_size)
        self.number_of_fetched_layer_rows += number_of_fetched_layer_rows
        for row in rows_fetched:
            self.add_row(row)

        self.beginInsertRows(QModelIndex(), len(self.rows),
                             len(self.rows) + items_to_fetch - 1)
        self.endInsertRows()
        return

    # ----------------------------------------------------------------------
    def add_row(self, row):
        """Add row to the grid of cells with rows."""
        # not using  self.beginResetModel() and self.endResetModel()
        # as it will put the the current selected row to the top
        self.rows.append(row)
        return

    # ----------------------------------------------------------------------
    def columnCount(self, index=QMODEL_INDEX):  # noqa: N802
        """Override built-in method."""
        return len(self.headers)

    # ----------------------------------------------------------------------
    def data(self, index, role=Qt.DisplayRole):  # noqa: N802
        """Override built-in method."""
        col = index.column()
        row = self.rows[index.row()]
        if role == Qt.DisplayRole:
            return getattr(row, self.headers_index_mapper[col], None)

    # ----------------------------------------------------------------------
    def headerData(self, section, orientation,  # noqa: N802
                   role=Qt.DisplayRole):
        """Override built-in method."""
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            return QVariant(self.headers[section])
        return QVariant(int(section + 1))
