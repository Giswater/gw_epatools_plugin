"""
This file is part of Giswater 3
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
import os
import re
import subprocess
from datetime import timedelta
from time import sleep, time

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication, QgsProject, QgsTask

from .task import GwTask
from ... import global_vars
from ...settings import tools_qgis, tools_qt, tools_gw, tools_db, tools_os, tools_log, task


class GwRecursiveEpa(task.GwTask):
    time_changed = pyqtSignal(str)
    task_finished = pyqtSignal()
    change_btn_accept = pyqtSignal(bool)

    def __init__(self, description, prefix, path, settings, plugin_dir):

        super().__init__(description, QgsTask.CanCancel)
        self.prefix = prefix
        self.path = path
        self.settings = settings
        self.fid = 140
        self.plugin_dir = plugin_dir
        self.stop = False
        self.t0 = 0
        self.total_objects = 0
        self.initialize_variables()


    def initialize_variables(self):

        self.exception = None
        self.error_msg = None
        self.message = None
        self.common_msg = ""
        self.function_failed = False
        self.complet_result = None
        self.function_name = None
        self.rpt_result = None
        self.files_exported = []
        global_vars.project_type = tools_gw.get_project_type()


    def run(self):

        self.change_btn_accept.emit(True)
        steps = self.settings.value("options/steps")
        self.export_subcatch = self.settings.value("options/export_subcatch")
        query1 = self.settings.value("list1/query")
        list1 = self.settings.value("list1/list")
        if not issubclass(type(list1), list):
            list1 = [list1]
        query2 = self.settings.value("list2/query")
        list2 = self.settings.value("list2/list")
        if not issubclass(type(list2), list):
            list2 = [list2]
        query3 = self.settings.value("list3/query")
        list3 = self.settings.value("list3/list")
        if not issubclass(type(list3), list):
            list3 = [list3]

        # Calculate total number of objects in all lists
        self.total_objects = len(list1)
        if list2:
            self.total_objects *= len(list2)
        if list3:
            self.total_objects *= len(list3)

        try:
            self.t0 = time()  # Initial time
            self.cur_idx = 0
            for l1o in list1:
                query = query1.replace("$list1object", l1o)
                tools_db.execute_sql(query, is_thread=True)
                if self.stop:
                    return False
                if not query2 or not list2:
                    self.run_go2epa(steps, l1o)
                    continue
                for l2o in list2:
                    query = query2.replace("$list2object", l2o)
                    tools_db.execute_sql(query, is_thread=True)
                    if self.stop:
                        return False
                    if not query3 or not list3:
                        self.run_go2epa(steps, l1o, l2o)
                        continue
                    for l3o in list3:
                        query = query3.replace("$list3object", l3o)
                        tools_db.execute_sql(query, is_thread=True)
                        self.run_go2epa(steps, l1o, l2o, l3o)
                        if self.stop:
                            return False

        except Exception as e:
            self.exception = e
            return False

        return True

    def run_go2epa(self, steps, l1o=None, l2o=None, l3o=None):
        self.cur_idx += 1
        resultname = f"{self.prefix}"
        if l3o:
            resultname += f"-{l3o}"
        if l2o:
            resultname += f"-{l2o}"
        if l1o:
            resultname += f"-{l1o}"
        self.result_name = resultname
        self.files_exported.append(resultname)
        inpfilename = f"{self.path}{os.sep}{resultname}.inp"
        rptfilename = f"{self.path}{os.sep}{resultname}.rpt"
        self.execute_go2epa(resultname, inpfilename, rptfilename, steps)
        self._calculate_remaining_time(self.t0)
        self.t0 = time()

    def finished(self, result):

        super().finished(result)
        self.task_finished.emit()
        self.change_btn_accept.emit(False)

        self._close_file()
        if self.files_exported:
            msg = f"The process has been executed. Files generated:"
            tools_qt.show_info_box(msg, inf_text=self.files_exported)
        if self.isCanceled():
            return

        # If PostgreSQL function returned null
        if self.complet_result is None:
            msg = f"Database returned null. Check postgres function '{self.function_name}'"
            tools_log.log_warning(msg)

        if self.function_failed:
            if self.json_result is None or not self.json_result:
                tools_log.log_warning("Function failed finished")
            if self.complet_result:
                if 'status' in self.complet_result:
                    if "Failed" in self.complet_result['status']:
                        tools_gw.manage_json_exception(self.complet_result)
            if self.rpt_result:
                if 'status' in self.rpt_result:
                    if "Failed" in self.rpt_result['status']:
                        tools_gw.manage_json_exception(self.rpt_result)

        if self.error_msg:
            title = f"Task aborted - {self.description()}"
            tools_qt.show_info_box(self.error_msg, title=title)
            return

        if self.exception:
            title = f"Task aborted - {self.description()}"
            tools_qt.show_info_box(self.exception, title=title)
            raise self.exception

        # If Database exception, show dialog after task has finished
        if global_vars.session_vars['last_error']:
            tools_qt.show_exception_message(msg=global_vars.session_vars['last_error_msg'])


    def cancel(self):
        self.stop_task()
        super().cancel()


    def stop_task(self):
        self.stop = True


    def _calculate_remaining_time(self, t0):
        tf = time()  # Final time
        td = tf - t0  # Delta time
        print(f"{td} * ({self.total_objects} - {self.cur_idx})")
        print(td * (self.total_objects - self.cur_idx))
        time_remaining = td * (self.total_objects - self.cur_idx)  # Delta time * remaining pages
        self.time_changed.emit(f"{timedelta(seconds=round(time_remaining))} ({self.cur_idx}/{self.total_objects})")


    def execute_go2epa(self, resultname, inpfilename, rptfilename, steps):

        # Execute pg2epa
        status = self._exec_function_pg2epa(steps, resultname)
        if not status:
            self.function_name = 'gw_fct_pg2epa_main'
            return False

        # Export inp
        status = self._export_inp(inpfilename, rptfilename)

        # Execute epa
        if status:
            status = self._execute_epa()

        # Import rpt
        if status:
            tools_log.log_info(f"Task 'Go2Epa' execute function 'def _import_rpt'")
            self.function_name = 'gw_fct_rpt2pg_main'
            status = self._import_rpt()

        return status

    # region pg2epa
    def _exec_function_pg2epa(self, steps, resultname):

        self.json_result = None
        status = False
        self.setProgress(0)

        extras = f'"resultId":"{resultname}"'
        if global_vars.project_type == 'ud':
            extras += f', "dumpSubcatch":"{self.export_subcatch}"'

        if steps == 3:
            self.body = tools_gw.create_body(extras=(extras + f', "step": 1'))
            tools_log.log_info(f"Task 'Go2Epa' execute procedure 'gw_fct_pg2epa_main' step 1 with parameters: "
                               f"'gw_fct_pg2epa_main', '{self.body}', 'log_sql=True', 'aux_conn={self.aux_conn}', 'is_thread=True'")

            json_result = tools_gw.execute_procedure('gw_fct_pg2epa_main', self.body, log_sql=True,
                                                     aux_conn=self.aux_conn, is_thread=True)
            if self.isCanceled():
                return False
            if json_result is not None:
                self.body = tools_gw.create_body(extras=(extras + f', "step": 2'))
                tools_log.log_info(f"Task 'Go2Epa' execute procedure 'gw_fct_pg2epa_main' step 2 with parameters: "
                                   f"'gw_fct_pg2epa_main', '{self.body}', 'log_sql=True', 'aux_conn={self.aux_conn}', 'is_thread=True'")
                json_result = tools_gw.execute_procedure('gw_fct_pg2epa_main', self.body, log_sql=True,
                                                         aux_conn=self.aux_conn, is_thread=True)
                if self.isCanceled():
                    return False
                if json_result is not None:
                    self.body = tools_gw.create_body(extras=(extras + f', "step": 3'))
                    tools_log.log_info(f"Task 'Go2Epa' execute procedure 'gw_fct_pg2epa_main' step 3 with parameters: "
                                       f"'gw_fct_pg2epa_main', '{self.body}', 'log_sql=True', 'aux_conn={self.aux_conn}', 'is_thread=True'")
                    json_result = tools_gw.execute_procedure('gw_fct_pg2epa_main', self.body, log_sql=True,
                                                             aux_conn=self.aux_conn, is_thread=True)
                    if self.isCanceled():
                        return False
        else:
            extras += f', "step": 0'
            self.body = tools_gw.create_body(extras=extras)
            json_result = tools_gw.execute_procedure('gw_fct_pg2epa_main', self.body, log_sql=True,
                                                     aux_conn=self.aux_conn, is_thread=True)
            if self.isCanceled():
                return False

        # Manage json result
        self.json_result = json_result
        self.complet_result = json_result
        if json_result is None or not json_result:
            self.function_failed = True
        elif 'status' in json_result:
            if json_result['status'] == 'Failed':
                tools_log.log_warning(json_result)
                self.function_failed = True
            else:
                status = True
        if self.isCanceled():
            return False

        return status
    # endregion

    # region export inp
    def _export_inp(self, inpfilename, rptfilename):

        if self.isCanceled():
            return False

        tools_log.log_info(f"Export INP file into PostgreSQL")

        # Get values from complet_result['body']['file'] and insert into INP file
        if 'file' not in self.complet_result['body']:
            return False

        self.file_inp = inpfilename
        self.file_rpt = rptfilename
        if self.file_inp == "null":
            message = "You have to set this parameter"
            self.error_msg = f"{message}: INP file"
            return False

        self._fill_inp_file(self.file_inp, self.complet_result['body']['file'])
        self.message = self.complet_result['message']['text']
        self.common_msg += "Export INP finished. "

        return True


    def _fill_inp_file(self, folder_path=None, all_rows=None):

        tools_log.log_info(f"Write inp file........: {folder_path}")

        # Generate generic INP file
        file_inp = open(folder_path, "w")
        read = True
        for row in all_rows:
            # Use regexp to check which targets to read (everyone except GULLY)
            if bool(re.match('\[(.*?)\]', row['text'])) and \
                    ('GULLY' in row['text'] or 'LINK' in row['text'] or
                     'GRATE' in row['text'] or 'LXSECTIONS' in row['text']):
                read = False
            elif bool(re.match('\[(.*?)\]', row['text'])):
                read = True
            if 'text' in row and row['text'] is not None and read:
                line = row['text'].rstrip() + "\n"
                file_inp.write(line)

        self._close_file(file_inp)

        networkmode = tools_gw.get_config_value('inp_options_networkmode')
        if global_vars.project_type == 'ud' and networkmode and networkmode[0] == "2":

            # Replace extension .inp
            aditional_path = folder_path.replace('.inp', f'.gul')
            aditional_file = open(aditional_path, "w")
            read = True
            save_file = False
            for row in all_rows:
                # Use regexp to check which targets to read (only TITLE and aditional target)
                if bool(re.match('\[(.*?)\]', row['text'])) and \
                        ('TITLE' in row['text'] or 'GULLY' in row['text'] or 'LINK' in row['text'] or
                         'GRATE' in row['text'] or 'LXSECTIONS' in row['text']):
                    read = True
                    if 'GULLY' in row['text'] or 'LINK' in row['text'] or \
                       'GRATE' in row['text'] or 'LXSECTIONS' in row['text']:
                        save_file = True
                elif bool(re.match('\[(.*?)\]', row['text'])):
                    read = False
                if 'text' in row and row['text'] is not None and read:
                    line = row['text'].rstrip() + "\n"
                    aditional_file.write(line)

            self._close_file(aditional_file)

            if save_file is False:
                os.remove(aditional_path)


    def _close_file(self, file=None):

        if file is None:
            file = self.file_rpt

        try:
            if file:
                file.close()
                del file
        except Exception:
            pass
    # endregion

    # region execute epa
    def _execute_epa(self):

        if self.isCanceled():
            return False

        tools_log.log_info(f"Execute EPA software")

        if self.file_rpt == "null":
            message = "You have to set this parameter"
            self.error_msg = f"{message}: RPT file"
            return False

        msg = "INP file not found"
        if self.file_inp is not None:
            if not os.path.exists(self.file_inp):
                self.error_msg = f"{msg}: {self.file_inp}"
                return False
        else:
            self.error_msg = f"{msg}: {self.file_inp}"
            return False

        # Set file to execute
        opener = None
        if global_vars.project_type in 'ws':
            opener = f"{self.plugin_dir}{os.sep}resources{os.sep}epa{os.sep}epanet{os.sep}epanet.exe"
        elif global_vars.project_type in 'ud':
            opener = f"{self.plugin_dir}{os.sep}resources{os.sep}epa{os.sep}swmm{os.sep}swmm5.exe"

        if opener is None:
            return False

        if not os.path.exists(opener):
            self.error_msg = f"File not found: {opener}"
            return False

        subprocess.call([opener, self.file_inp, self.file_rpt], shell=False)
        self.common_msg += "EPA model finished. "

        return True
    # endregion

    # region import rpt
    def _import_rpt(self):
        """ Import result file """

        tools_log.log_info(f"Import rpt file........: {self.file_rpt}")

        self.rpt_result = None
        self.json_rpt = None
        status = False
        try:
            # Call import function
            status = self._read_rpt_file(self.file_rpt)
            if not status:
                return False
            tools_log.log_info(f"Task 'Go2Epa' execute function 'def _exec_import_function'")
            status = self._exec_import_function()
        except Exception as e:
            self.error_msg = str(e)
        finally:
            return status


    def _read_rpt_file(self, file_path=None):

        self.file_rpt = open(file_path, "r+")
        full_file = self.file_rpt.readlines()
        progress = 0

        # Create dict with sources
        sql = f"SELECT tablename, target FROM config_fprocess WHERE fid = {self.fid};"
        rows = tools_db.get_rows(sql)
        sources = {}
        for row in rows:
            json_elem = row[1].replace('{', '').replace('}', '')
            item = json_elem.split(',')
            for i in item:
                sources[i.strip()] = row[0].strip()

        # While we don't find a match with the target, target and col40 must be null
        target = "null"
        col40 = "null"
        json_rpt = ""
        # noinspection PyUnusedLocal
        row_count = sum(1 for rows in full_file)

        for line_number, row in enumerate(full_file):

            if self.isCanceled():
                return False

            progress += 1
            if '**' in row or '--' in row:
                continue

            row = row.rstrip()
            dirty_list = row.split(' ')

            # Clean unused items
            for x in range(len(dirty_list) - 1, -1, -1):
                if dirty_list[x] == '':
                    dirty_list.pop(x)

            sp_n = []
            if len(dirty_list) > 0:
                for x in range(0, len(dirty_list)):
                    if bool(re.search('[0-9][-]\d{1,2}[.]]*', str(dirty_list[x]))):
                        last_index = 0
                        for i, c in enumerate(dirty_list[x]):
                            if "-" == c:
                                json_elem = dirty_list[x][last_index:i]
                                last_index = i
                                sp_n.append(json_elem)

                        # noinspection PyUnboundLocalVariable
                        json_elem = dirty_list[x][last_index:i]
                        sp_n.append(json_elem)

                    elif bool(re.search('(\d\..*\.\d)', str(dirty_list[x]))):
                        if 'Version' not in dirty_list and 'VERSION' not in dirty_list:
                            error_near = f"Error near line {line_number+1} -> {dirty_list}"
                            tools_log.log_info(error_near)
                            message = (f"The rpt file is not valid to import. "
                                       f"Because columns on rpt file are overlaped, it seems you need to improve your simulation. "
                                       f"Please ckeck and fix it before continue. \n"
                                       f"{error_near}")
                            self.error_msg = message
                            return False
                    elif bool(re.search('>50', str(dirty_list[x]))):
                        error_near = f"Error near line {line_number+1} -> {dirty_list}"
                        tools_log.log_info(error_near)
                        message = (f"The rpt file is not valid to import. "
                                   f"Because velocity has not numeric value (>50), it seems you need to improve your simulation. "
                                   f"Please ckeck and fix it before continue. \n"
                                   f"{error_near}")
                        self.error_msg = message
                        return False
                    else:
                        sp_n.append(dirty_list[x])

            # Find strings into dict and set target column
            for k, v in sources.items():
                try:
                    if k in (f'{sp_n[0]} {sp_n[1]}', f'{sp_n[0]}'):
                        target = "'" + v + "'"
                        _time = re.compile('^([012]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$')
                        if _time.search(sp_n[3]):
                            col40 = "'" + sp_n[3] + "'"
                except IndexError:
                    pass
                except Exception as e:
                    tools_log.log_info(type(e).__name__)

            if len(sp_n) > 0:
                json_elem = f'"target": "{target}", "col40": "{col40}", '
                for x in range(0, len(sp_n)):
                    json_elem += f'"col{x + 1}":'
                    if "''" not in sp_n[x]:
                        value = '"' + sp_n[x].strip().replace("\n", "") + '", '
                        value = value.replace("''", "null")
                    else:
                        value = 'null, '
                    json_elem += value

                json_elem = '{' + str(json_elem[:-2]) + '}, '
                json_rpt += json_elem

            # Update progress bar
            if progress % 1000 == 0:
                self.setProgress((line_number * 100) / row_count)

        # Manage JSON
        json_rpt = '[' + str(json_rpt[:-2]) + ']'
        self.json_rpt = json_rpt

        self._close_file()

        return True


    def _exec_import_function(self):
        """ Call function gw_fct_rpt2pg_main """

        extras = f'"resultId":"{self.result_name}"'
        if self.json_rpt:
            extras += f', "file": {self.json_rpt}'
        self.body = tools_gw.create_body(extras=extras)
        self.json_result = tools_gw.execute_procedure('gw_fct_rpt2pg_main', self.body,
                                                      aux_conn=self.aux_conn, is_thread=True)
        self.rpt_result = self.json_result
        if self.json_result is None or not self.json_result:
            self.function_failed = True
            return False

        if 'status' in self.json_result and self.json_result['status'] == 'Failed':
            tools_log.log_warning(self.json_result)
            self.function_failed = True
            return False

        # final message
        self.common_msg += "Import RPT file finished."

        return True

    # endregion
