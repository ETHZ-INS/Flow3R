# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

"""PySide6 port of the widgets/layouts/flowlayout example from Qt v6.x"""

import sys
from PySide6.QtCore import Qt, QMargins, QPoint, QRect, QSize
from PySide6.QtWidgets import QApplication, QLayout, QPushButton, QSizePolicy, QWidget, QFrame, QVBoxLayout, QSpacerItem


class Window(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        main_layout.addItem(spacer)

        frm = QFrame(self)
        flow_layout = FlowLayout(frm)
        flow_layout.addWidget(QPushButton("Short"))
        flow_layout.addWidget(QPushButton("Longer"))
        flow_layout.addWidget(QPushButton("Different text"))
        flow_layout.insertWidget(1, QPushButton("More text"))
        flow_layout.addWidget(QPushButton("Even longer button text"))

        main_layout.addWidget(frm)

        self.setWindowTitle("Flow Layout")


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0))

        self._item_list = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)
        #self.invalidate()

    def insertWidget(self, index, widget):
        self.addWidget(widget)
        self._item_list.insert(index, self._item_list.pop())

    def clear(self):
        while self.count():
            item = self.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
        item = self._item_list.pop(index) if 0 <= index < len(self._item_list) else None
        #self.invalidate()
        return item

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        m = self.contentsMargins()
        h = self._do_layout(QRect(0, 0, width, 0), True)  # no pre-subtraction
        return h + m.top() + m.bottom()

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        m = self.contentsMargins()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

#    def invalidate(self):
#        super().invalidate()
#        pw = self.parentWidget()
#        if pw is not None:
#            pw.updateGeometry()

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        # work inside margins
        rect = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())

        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            w = item.widget()
            # Use each widget's control type for style spacing
            ct = w.sizePolicy().controlType()
            style = w.style()
            layout_spacing_x = style.layoutSpacing(ct, ct, Qt.Orientation.Horizontal)
            layout_spacing_y = style.layoutSpacing(ct, ct, Qt.Orientation.Vertical)

            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y

            hint = item.sizeHint()
            next_x = x + hint.width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y += line_height + space_y
                next_x = x + hint.width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            line_height = max(line_height, hint.height())

        # total content height (inside margins)
        return (y + line_height) - rect.y()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = Window()
    main_win.show()
    sys.exit(app.exec())