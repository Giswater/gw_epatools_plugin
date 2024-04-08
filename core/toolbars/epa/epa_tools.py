"""
Copyright © 2023 by BGEO. All rights reserved.
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""
# -*- coding: utf-8 -*-
from functools import partial

from qgis.PyQt.QtCore import QPoint
from qgis.PyQt.QtWidgets import QMenu, QAction, QActionGroup

from ....settings import dialog, gw_global_vars
from .... import global_vars
from .anl_add_demand_check import AddDemandCheck
from .anl_recursive_go2epa import RecursiveEpa


class GwEpaTools(dialog.GwAction):
    """ Button 44: Replace feature
    User select one feature. Execute SQL function: 'gw_fct_setfeaturereplace' """

    def __init__(self, icon_path, action_name, text, toolbar, action_group):

        super().__init__(icon_path, action_name, text, toolbar, action_group)
        self.iface = global_vars.iface

        self.icon_path = icon_path
        self.action_name = action_name
        self.text = text
        self.toolbar = toolbar
        self.action_group = action_group

        # Create a menu and add all the actions
        self.menu = QMenu()
        self.menu.setObjectName("GW_epa_tools")
        self._fill_action_menu()

        if toolbar is not None:
            self.action.setMenu(self.menu)
            toolbar.addAction(self.action)

    def clicked_event(self): 
        button = self.action.associatedWidgets()[1]
        menu_point = button.mapToGlobal(QPoint(0,button.height()))
        self.menu.exec(menu_point)

    def _fill_action_menu(self):
        """ Fill action menu """

        # disconnect and remove previuos signals and actions
        actions = self.menu.actions()
        for action in actions:
            action.disconnect()
            self.menu.removeAction(action)
            del action
        ag = QActionGroup(self.iface.mainWindow())

        anl_menu = self.menu.addMenu("ANALYTICS")

        new_actions = [
            (anl_menu, ('ws'), 'ADDITIONAL DEMAND CHECK'),
            (anl_menu, ('ud', 'ws'), 'EPA MULTI CALLS'),
        ]
        for menu, types, action in new_actions:
            if gw_global_vars.project_type in types:
                obj_action = QAction(f"{action}", ag)
                menu.addAction(obj_action)
                obj_action.triggered.connect(partial(self._get_selected_action, action))

        # Remove menu if it is empty
        for menu in self.menu.findChildren(QMenu):
            if not len(menu.actions()):
                menu.menuAction().setParent(None)

    def _get_selected_action(self, name):
        """ Gets selected action """

        if name == 'ADDITIONAL DEMAND CHECK':
            add_demand_check = AddDemandCheck()
            add_demand_check.clicked_event()

        elif name == 'EPA MULTI CALLS':
            recursive_epa = RecursiveEpa()
            recursive_epa.clicked_event()
