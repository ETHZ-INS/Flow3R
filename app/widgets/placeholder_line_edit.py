from PySide6.QtCore import Signal, Qt, QRegularExpression
from PySide6.QtGui import QFontMetrics, QSyntaxHighlighter, QTextCharFormat, QColor
from PySide6.QtWidgets import QPlainTextEdit


class VariableHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, allowed_vars = None):
        super().__init__(doc)
        self.allowed = set(allowed_vars) if allowed_vars is not None else set()
        self.regex = QRegularExpression(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")

        self.ok_fmt = QTextCharFormat()
        self.ok_fmt.setForeground(QColor("blue"))

        self.bad_fmt = QTextCharFormat()
        self.bad_fmt.setForeground(QColor("red"))
        self.bad_fmt.setFontUnderline(True)
        self.bad_fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

    def setAllowed(self, names):
        self.allowed = set(names)
        self.rehighlight()

    def highlightBlock(self, text):
        it = self.regex.globalMatch(text)
        while it.hasNext():
            m = it.next()
            name = m.captured(1)
            fmt = self.ok_fmt if name in self.allowed else self.bad_fmt
            self.setFormat(m.capturedStart(0), m.capturedLength(0), fmt)



class PlaceholderLineEdit(QPlainTextEdit):
    """A single-line text editor with syntax highlighting support."""
    returnPressed = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTabChangesFocus(True)
        # Make it look/size like a QLineEdit
        fm = QFontMetrics(self.font())
        h = fm.height() + 8
        self.setFixedHeight(h)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.returnPressed.emit()
            return
        super().keyPressEvent(e)

    def insertFromMimeData(self, source):
        # strip newlines on paste
        text = source.text().replace("\n", " ")
        self.insertPlainText(text)

    def text(self):
        return super().toPlainText()

    def setText(self, text):
        self.setPlainText(text)
