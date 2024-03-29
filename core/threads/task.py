"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from time import sleep

from qgis.PyQt.QtCore import pyqtSignal, QObject
from qgis.core import QgsTask

from ...settings import tools_qgis, tools_qt, tools_gw, tools_db, dialog, toolbox, tools_os, tools_log



class GwTask(QgsTask, QObject):
    """ This shows how to subclass QgsTask """

    fake_progress = pyqtSignal()

    def __init__(self, description, duration=0):

        QObject.__init__(self)
        super().__init__(description, QgsTask.CanCancel)
        self.exception = None
        self.duration = duration


    def run(self):

        tools_log.log_info(f"Started task {self.description()}")

        if self.duration is 0:
            if self.isCanceled():
                return False
            if self.progress() >= 100:
                return True
            return True
        else:
            wait_time = self.duration / 100
            sleep(wait_time)
            for i in range(100):
                sleep(wait_time)
                self.setProgress(i)
                if self.isCanceled():
                    return False

            return True


    def finished(self, result):

        if result:
            tools_log.log_info(f"Task {self.description()} completed")
        else:
            if self.exception is None:
                tools_log.log_info(f"Task {self.description()} not successful but without exception")
            else:
                tools_log.log_info(f"Task {self.description()} Exception: {self.exception}")
                raise self.exception


    def cancel(self):

        tools_log.log_info(f"Task {self.description()} was cancelled")
        super().cancel()


