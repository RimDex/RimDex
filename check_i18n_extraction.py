"""
Check that all self.tr(...) calls in app/ have extractable arguments.

pyside6-lupdate cannot extract strings from:
  1. self.tr(variable_name)    -- argument is a variable/parameter
  2. self.tr(CONSTANT_NAME)     -- argument is a module/class constant
  3. self.tr(f"...{expr}...")   -- argument is an f-string
  4. self.tr(...) in a non-QObject class (no QObject anywhere in the MRO)

Exit code 0 = clean, non-zero = issues found.
"""

import ast
import os
import sys

QOBJECT_CLASSES = {
    "QObject",
    "QWidget",
    "QDialog",
    "QMainWindow",
    "QFrame",
    "QMenu",
    "QLabel",
    "QPushButton",
    "QCheckBox",
    "QComboBox",
    "QLineEdit",
    "QTextEdit",
    "QListWidget",
    "QTableWidget",
    "QTreeWidget",
    "QTabWidget",
    "QGroupBox",
    "QRadioButton",
    "QProgressBar",
    "QSlider",
    "QSpinBox",
    "QDoubleSpinBox",
    "QDateEdit",
    "QTimeEdit",
    "QDateTimeEdit",
    "QDial",
    "QScrollBar",
    "QToolBox",
    "QToolButton",
    "QMenuBar",
    "QStatusBar",
    "QToolBar",
    "QSplitter",
    "QDockWidget",
    "QListView",
    "QTableView",
    "QTreeView",
    "QColumnView",
    "QHeaderView",
    "QGraphicsView",
    "QGraphicsWidget",
    "QQuickWidget",
    "QWebEngineView",
    "QMessageBox",
    "QAbstractItemView",
    "QStyledItemDelegate",
    "QItemDelegate",
    "QSyntaxHighlighter",
    "QTextBrowser",
    "QListWidgetItem",
    "QThread",
    # Mixins designed for QObject subclass composition (BaseModsPanel → QWidget)
    "UIBaseMixin",
    "TableMixin",
    "ModRowsMixin",
    "SelectionMixin",
    "ButtonsMixin",
    "ColumnsMixin",
}


def _collect_qobject_subclasses(root: str) -> set[str]:
    known: set[str] = set(QOBJECT_CLASSES)
    changed = True
    while changed:
        changed = False
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(dirpath, fn)
                try:
                    with open(path, encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.ClassDef):
                        continue
                    if node.name in known:
                        continue
                    for base in node.bases:
                        name = None
                        if isinstance(base, ast.Name):
                            name = base.id
                        elif isinstance(base, ast.Attribute):
                            name = base.attr
                        if name in known:
                            known.add(node.name)
                            changed = True
                            break
    return known - QOBJECT_CLASSES


def _check_file(path: str, known_qobject: set[str]) -> list[tuple[int, str, str]]:
    issues: list[tuple[int, str, str]] = []
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except SyntaxError as e:
        print(f"  [SKIP] {path}: syntax error ({e})")
        return issues

    # Build set of non-QObject classes defined in this file
    classes_in_file: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes_in_file.add(node.name)
    non_qobject = classes_in_file - known_qobject
    if not non_qobject:
        return issues

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name not in non_qobject:
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "tr"
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
            ):
                continue
            if not child.args:
                continue
            arg = child.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                issues.append(
                    (
                        node.lineno,
                        node.name,
                        f"non-QObject class uses self.tr(...): {arg.value[:60]}",
                    )
                )
            elif isinstance(arg, ast.JoinedStr):
                issues.append(
                    (
                        node.lineno,
                        node.name,
                        "f-string passed to self.tr(...)",
                    )
                )
            else:
                issues.append(
                    (
                        node.lineno,
                        node.name,
                        f"non-literal passed to self.tr(...): {type(arg).__name__}",
                    )
                )
    return issues


def main() -> int:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(root_dir, "app")

    if not os.path.isdir(app_dir):
        print("Error: app/ directory not found")
        return 1

    print("Building QObject class hierarchy...")
    known_qobject = _collect_qobject_subclasses(app_dir) | QOBJECT_CLASSES

    all_issues: list[tuple[str, int, str, str]] = []

    for dirpath, _, filenames in os.walk(app_dir):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root_dir)
            for lineno, cls, msg in _check_file(path, known_qobject):
                all_issues.append((rel, lineno, cls, msg))

    if not all_issues:
        print("No i18n extraction issues found.")
        return 0

    print(f"\n{len(all_issues)} i18n extraction issue(s) found:\n")
    for rel, lineno, cls, msg in sorted(all_issues):
        print(f"  {rel}:{lineno}  [{cls}] {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
