"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
import configparser
import os
import webbrowser

from qgis.PyQt import uic, QtCore
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMainWindow, QDialog, QDockWidget, QWhatsThis, QLineEdit


class GwDialog(QDialog):

    def __init__(self, subtag=None):
        super().__init__()
        self.setupUi(self)
        self.subtag = subtag
        # Enable event filter
        self.installEventFilter(self)


    def eventFilter(self, object, event):

        if event.type() == QtCore.QEvent.EnterWhatsThisMode and self.isActiveWindow():
            QWhatsThis.leaveWhatsThisMode()
            parser = configparser.ConfigParser()
            path = os.path.dirname(__file__) + os.sep + 'config' + os.sep + 'init.config'
            if not os.path.exists(path):
                print(f"File not found: {path}")
                webbrowser.open_new_tab('https://giswater.org/giswater-manual')
                return True

            parser.read(path)
            if self.subtag is not None:
                tag = f'{self.objectName()}_{self.subtag}'
            else:
                tag = str(self.objectName())

            try:
                web_tag = parser.get('web_tag', tag)
                webbrowser.open_new_tab(f'https://giswater.org/giswater-manual/#{web_tag}')
            except Exception:
                webbrowser.open_new_tab('https://giswater.org/giswater-manual')
            finally:
                return True

        return False



def get_ui_class(ui_file_name, subfolder='shared'):
    """ Get UI Python class from @ui_file_name """

    # Folder that contains UI files
    if subfolder in ('basic', 'edit', 'epa', 'om', 'plan', 'utilities', 'toc', 'custom'):
        ui_folder_path = os.path.dirname(__file__) + os.sep + 'toolbars' + os.sep + subfolder
    else:
        ui_folder_path = os.path.dirname(__file__) + os.sep + subfolder
    ui_file_path = os.path.abspath(os.path.join(ui_folder_path, ui_file_name))
    return uic.loadUiType(ui_file_path)[0]


# giswater_advancedtools

FORM_CLASS = get_ui_class('add_demand_check.ui', 'epa')
class AddDemandCheckUi(GwDialog, FORM_CLASS):
    pass

FORM_CLASS = get_ui_class('recursive_go2epa.ui', 'epa')
class RecursiveEpaUi(GwDialog, FORM_CLASS):
    pass