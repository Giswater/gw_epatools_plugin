"""
This file is part of Giswater 3
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
import os
import sys
from functools import partial

from qgis.core import QgsApplication, QgsLayoutExporter, QgsProject
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QLabel
from qgis.PyQt.QtCore import QSettings

from ...ui.ui_manager import RecursiveEpaUi
from ...threads.recursive_epa import GwRecursiveEpa
from .... import global_vars
from ....settings import tools_qgis, tools_qt, tools_gw, dialog, tools_os, tools_log, tools_db


class RecursiveEpa(dialog.GwAction):

    def __init__(self, icon_path, action_name, text, toolbar, action_group):
        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

    def clicked_event(self):

        self.dlg_epa = RecursiveEpaUi()
        tools_gw.load_settings(self.dlg_epa)

        # Load user values
        last_path = tools_gw.get_config_parser('recursive_epa', 'folder_path', 'user', 'session', plugin=global_vars.user_folder_name)
        tools_qt.set_widget_text(self.dlg_epa, self.dlg_epa.txt_path, last_path)
        last_prefix = tools_gw.get_config_parser('recursive_epa', 'prefix', 'user', 'session', plugin=global_vars.user_folder_name)
        tools_qt.set_widget_text(self.dlg_epa, self.dlg_epa.txt_prefix, last_prefix)

        # Set signals
        self.dlg_epa.btn_close.clicked.connect(partial(self.dlg_epa.reject))
        self.dlg_epa.btn_path.clicked.connect(partial(self.get_folder_dialog, self.dlg_epa.txt_path))
        self.dlg_epa.btn_config.clicked.connect(partial(self.open_config_file))
        self.dlg_epa.btn_accept.clicked.connect(partial(self.execute_epa))
        self.dlg_epa.rejected.connect(partial(self.save_user_values, self.dlg_epa))
        self.dlg_epa.rejected.connect(partial(tools_gw.close_dialog, self.dlg_epa))

        tools_gw.open_dialog(self.dlg_epa, dlg_name='dlg_recursive_epa')


    def open_config_file(self):
        """ Opens recursive_go2epa.config file """
        file_path = f"{global_vars.plugin_dir}{os.sep}config{os.sep}recursive_go2epa.config"
        tools_os.open_file(file_path)


    def save_user_values(self, dialog):
        """ Save last user values """
        folder_path = tools_qt.get_text(dialog, dialog.txt_path)
        tools_gw.set_config_parser('recursive_epa', 'folder_path', f"{folder_path}", plugin=global_vars.user_folder_name)
        prefix = tools_qt.get_text(dialog, dialog.txt_prefix, False, False)
        tools_gw.set_config_parser('recursive_epa', 'prefix', f"{prefix}", plugin=global_vars.user_folder_name)


    def execute_epa(self):
        # Get folder path
        folder_path = tools_qt.get_text(self.dlg_epa, self.dlg_epa.txt_path)
        if folder_path is None or folder_path == 'null' or not os.path.exists(folder_path):
            self.get_folder_dialog(self.dlg_epa.txt_path)
            folder_path = tools_qt.get_text(self.dlg_epa, self.dlg_epa.txt_path)

        # Get prefix
        prefix = tools_qt.get_text(self.dlg_epa, self.dlg_epa.txt_prefix, False, False)

        setting_file = os.path.join(global_vars.plugin_dir, 'config', 'recursive_go2epa.config')
        if not os.path.exists(setting_file):
            message = f"Config file not found at: {setting_file}"
            self.iface.messageBar().pushMessage("", message, 1, 20)
            return
        settings = QSettings(setting_file, QSettings.IniFormat)
        settings.setIniCodec(sys.getfilesystemencoding())
        list1 = settings.value("list1/list")
        list2 = settings.value("list2/list")
        list3 = settings.value("list3/list")

        msg = "These are the lists that will be used. Do you want to continue?"
        inf_text = f"{list1}"
        if list2:
            inf_text += f"\n{list2}"
            if list3:
                inf_text += f"\n{list3}"
        response = tools_qt.show_question(msg, inf_text=inf_text, force_action=True)
        if response:
            self.recursive_epa = GwRecursiveEpa("Recursive Go2Epa", prefix, folder_path, settings, self.plugin_dir)
            self.recursive_epa.change_btn_accept.connect(self._enable_cancel_btn)
            self.recursive_epa.time_changed.connect(self._set_remaining_time)
            QgsApplication.taskManager().addTask(self.recursive_epa)
            QgsApplication.taskManager().triggerTask(self.recursive_epa)


    def get_folder_dialog(self, widget):
        """ Get folder dialog """

        # Check if selected folder exists. Set default value if necessary
        folder_path = tools_qt.get_text(self.dlg_epa, widget)
        if folder_path in (None, 'null') or not os.path.exists(folder_path):
            folder_path = os.path.expanduser("~")

        # Open dialog to select folder
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        message = "Select folder"
        folder_path = file_dialog.getExistingDirectory(
            parent=None, caption=tools_qt.tr(message), directory=folder_path)
        if folder_path:
            tools_qt.set_widget_text(self.dlg_epa, widget, str(folder_path))


    def _enable_cancel_btn(self, enable):
        if enable:
            self.dlg_epa.btn_accept.clicked.disconnect()
            self.dlg_epa.btn_accept.setText(f"Cancel")
            self.dlg_epa.btn_accept.clicked.connect(self.recursive_epa.stop_task)
            self.dlg_epa.btn_close.hide()
        else:
            self.dlg_epa.btn_close.show()
            self.dlg_epa.btn_accept.clicked.disconnect()
            self.dlg_epa.btn_accept.setText(f"Accept")
            self.dlg_epa.btn_accept.clicked.connect(partial(self.execute_epa))


    def _set_remaining_time(self, time):
        lbl_time = self.dlg_epa.findChild(QLabel, 'lbl_time')
        lbl_time.setText(time)

