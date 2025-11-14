""""
physiboss_intra.py - parameters for the Cell Types -> Intracellular -> MaBoSS
Authors:
Vincent Noël (vincent.noel@curie.fr)
Randy Heiland (heiland@iu.edu)
Dr. Paul Macklin (macklinp@iu.edu)
- also rf. Credits.md
"""

import sys
import os
import csv
import logging

import xml.etree.ElementTree as ET  # https://docs.python.org/2/library/xml.etree.elementtree.html
from pathlib import Path
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QFrame,QApplication,QWidget,QTabWidget,QLineEdit, QGroupBox,QHBoxLayout,QVBoxLayout,QRadioButton,QLabel,QCheckBox,QComboBox,QScrollArea,QGridLayout,QPushButton,QFileDialog,QTableWidget,QTableWidgetItem,QHeaderView
from PyQt5.QtWidgets import QMessageBox, QCompleter, QSizePolicy
from PyQt5.QtCore import QSortFilterProxyModel, Qt, QRect
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont, QIcon
from PyQt5.QtGui import QPixmap
from PyQt5 import QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

# from multivariate_rules import Window_plot_rules
from studio_classes import ExtendedCombo, QCheckBox_custom, QComboBox_custom
from studio_functions import show_studio_warning_window
from xml_constants import *
# from cell_def_tab import CellDefException

class PhysiBoSSCellDefException(Exception):
    pass

# Overloading the QLineEdit widget to let us map it to its variable name. Ugh.
class MyQLineEdit(QLineEdit):
    vname = None
    wrow = 0
    wcol = 0
    prev = None

#----------------------------------------------------------------------
class PhysiBoSS_CellDef(QWidget):
    def __init__(self, nanohub_flag, microenv_tab, celldef_tab):
        super().__init__()

        print("\n---------- creating PhysiBoSS_CellDef(QWidget)")
        self.nanohub_flag = nanohub_flag
        self.homedir = '.'  # reset in studio.py
        self.absolute_data_dir = None   # updated in studio.py

        self.microenv_tab = microenv_tab
        self.celldef_tab = celldef_tab

        self.celltype_name = None
        
        self.physiboss_boolean_frame = QFrame()
        self.physiboss_signals = []
        self.physiboss_behaviours = []


        # self.studio_flag = studio_flag
        self.studio_flag = None
        self.vis_tab = None

        self.xml_root = None


        # -------  PhysiBoSS Boolean  -------

        # self.boolean_frame = QFrame()
        
        ly = QVBoxLayout()
        self.physiboss_boolean_frame.setLayout(ly)

        bnd_hbox = QHBoxLayout()

        bnd_label = QLabel("MaBoSS BND file")
        bnd_hbox.addWidget(bnd_label)

        self.physiboss_bnd_file = QLineEdit()
        self.physiboss_bnd_file.textChanged.connect(self.physiboss_bnd_filename_changed)
        bnd_hbox.addWidget(self.physiboss_bnd_file)


        bnd_button = QPushButton("Choose BND file")
        bnd_button.clicked.connect(self.choose_bnd_file)

        bnd_hbox.addWidget(bnd_button)
        ly.addLayout(bnd_hbox)

        cfg_hbox = QHBoxLayout()

        cfg_label = QLabel("MaBoSS CFG file")
        cfg_hbox.addWidget(cfg_label)

        self.physiboss_cfg_file = QLineEdit()
        self.physiboss_cfg_file.textChanged.connect(self.physiboss_cfg_filename_changed)
        cfg_hbox.addWidget(self.physiboss_cfg_file)

        cfg_button = QPushButton("Choose CFG file")
        cfg_button.clicked.connect(self.choose_cfg_file)

        cfg_hbox.addWidget(cfg_button)
        ly.addLayout(cfg_hbox)

        time_step_hbox = QHBoxLayout()

        time_step_label = QLabel("Time step")
        time_step_hbox.addWidget(time_step_label)

        self.physiboss_time_step = QLineEdit()
        self.physiboss_time_step.textChanged.connect(self.physiboss_time_step_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_time_step.setValidator(QtGui.QDoubleValidator())

        time_step_hbox.addWidget(self.physiboss_time_step)

        ly.addLayout(time_step_hbox)

        scaling_hbox = QHBoxLayout()

        scaling_label = QLabel("Scaling")
        scaling_hbox.addWidget(scaling_label)

        self.physiboss_scaling = QLineEdit()
        self.physiboss_scaling.textChanged.connect(self.physiboss_scaling_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_scaling.setValidator(QtGui.QDoubleValidator())

        scaling_hbox.addWidget(self.physiboss_scaling)

        ly.addLayout(scaling_hbox)

        time_stochasticity_hbox = QHBoxLayout()

        time_stochasticity_label = QLabel("Time stochasticity")
        time_stochasticity_hbox.addWidget(time_stochasticity_label)

        self.physiboss_time_stochasticity = QLineEdit()
        self.physiboss_time_stochasticity.textChanged.connect(self.physiboss_time_stochasticity_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_time_stochasticity.setValidator(QtGui.QDoubleValidator())

        time_stochasticity_hbox.addWidget(self.physiboss_time_stochasticity)

        ly.addLayout(time_stochasticity_hbox)

        starttime_hbox = QHBoxLayout()

        starttime_label = QLabel("Start time")
        starttime_hbox.addWidget(starttime_label)

        self.physiboss_starttime = QLineEdit()
        self.physiboss_starttime.textChanged.connect(self.physiboss_starttime_changed)
        # Commenting it because for french, we need to use a comma, which then get written in the XML and might cause problems
        # self.physiboss_scaling.setValidator(QtGui.QDoubleValidator())

        starttime_hbox.addWidget(self.physiboss_starttime)

        ly.addLayout(starttime_hbox)


        initial_states_groupbox = QGroupBox("Initial states")
        self.physiboss_initial_states_layout = QVBoxLayout()
        initial_states_labels = QHBoxLayout()

        initial_states_node_label = QLabel("Node")
        initial_states_value_label = QLabel("Value")
        initial_states_labels.addWidget(initial_states_node_label)
        initial_states_labels.addWidget(initial_states_value_label)
        self.physiboss_initial_states_layout.addLayout(initial_states_labels)

        self.physiboss_initial_states = []
        initial_states_groupbox.setLayout(self.physiboss_initial_states_layout)

        ly.addWidget(initial_states_groupbox)
        
        initial_states_addbutton = QPushButton("Add new initial value")
        initial_states_addbutton.setStyleSheet("QPushButton { color: black }")
        initial_states_addbutton.clicked.connect(self.physiboss_clicked_add_initial_value)
        ly.addWidget(initial_states_addbutton)

        
        mutants_groupbox = QGroupBox("Mutants")
        self.physiboss_mutants_layout = QVBoxLayout()
        mutants_labels = QHBoxLayout()

        mutants_node_label = QLabel("Node")
        mutants_value_label = QLabel("Value")
        mutants_labels.addWidget(mutants_node_label)
        mutants_labels.addWidget(mutants_value_label)
        self.physiboss_mutants_layout.addLayout(mutants_labels)
        mutants_groupbox.setLayout(self.physiboss_mutants_layout)
        
        self.physiboss_mutants = []
        ly.addWidget(mutants_groupbox)
 
        mutants_addbutton = QPushButton("Add new mutant")
        mutants_addbutton.setStyleSheet("QPushButton { color: black }")
        mutants_addbutton.clicked.connect(self.physiboss_clicked_add_mutant)
        ly.addWidget(mutants_addbutton)

        parameters_groupbox = QGroupBox("Parameters")

        self.physiboss_parameters_layout = QVBoxLayout()
        parameters_labels = QHBoxLayout()

        parameters_node_label = QLabel("Name")
        parameters_value_label = QLabel("Value")
        parameters_labels.addWidget(parameters_node_label)
        parameters_labels.addWidget(parameters_value_label)
        self.physiboss_parameters_layout.addLayout(parameters_labels)
        parameters_groupbox.setLayout(self.physiboss_parameters_layout)

        self.physiboss_parameters = []
        ly.addWidget(parameters_groupbox)

        parameters_addbutton = QPushButton("Add new parameter")
        parameters_addbutton.setStyleSheet("QPushButton { color: black }")
        parameters_addbutton.clicked.connect(self.physiboss_clicked_add_parameter)
        ly.addWidget(parameters_addbutton)

        inputs_groupbox = QGroupBox("Inputs")

        self.physiboss_inputs_layout = QVBoxLayout()
        self.physiboss_inputs_layout.setAlignment(Qt.AlignTop)
        inputs_labels = QHBoxLayout()

        inputs_signal_label = QLabel("Signal")
        inputs_node_label = QLabel("Node")
        inputs_action_label = QLabel("Action")
        inputs_threshold_label = QLabel("Thr")
        inputs_inact_threshold_label = QLabel("Inact. Thr")
        inputs_smoothing_label = QLabel("Smoothing")


        inputs_labels.addWidget(inputs_signal_label)
        inputs_signal_label.setMinimumWidth(240)
        inputs_labels.setStretch(0, 1)
        inputs_labels.addWidget(inputs_action_label)
        inputs_action_label.setMinimumWidth(50)
        inputs_labels.setStretch(1, 1)
        inputs_labels.addWidget(inputs_node_label)
        inputs_node_label.setMinimumWidth(50)
        inputs_labels.setStretch(2, 1)
        inputs_labels.addWidget(inputs_threshold_label)
        inputs_threshold_label.setFixedWidth(70)
        inputs_labels.addWidget(inputs_inact_threshold_label)
        inputs_inact_threshold_label.setFixedWidth(70)
        inputs_labels.addWidget(inputs_smoothing_label)
        inputs_smoothing_label.setFixedWidth(70)
        inputs_labels.addSpacing(35)

        self.physiboss_inputs_layout.addLayout(inputs_labels)
        inputs_groupbox.setLayout(self.physiboss_inputs_layout)

        self.physiboss_inputs = []
        ly.addWidget(inputs_groupbox)

        inputs_addbutton = QPushButton("Add new input")
        inputs_addbutton.setStyleSheet("QPushButton { color: black }")
        inputs_addbutton.clicked.connect(self.physiboss_clicked_add_input)
        ly.addWidget(inputs_addbutton)

        outputs_groupbox = QGroupBox("Outputs")

        self.physiboss_outputs_layout = QVBoxLayout()
        outputs_labels = QHBoxLayout()

        outputs_signal_label = QLabel("Behavior")
        outputs_node_label = QLabel("Node")
        outputs_action_label = QLabel("Action")
        outputs_value_label = QLabel("Value")
        outputs_basal_value_label = QLabel("Base value")
        outputs_smoothing_label = QLabel("Smoothing")

        outputs_labels.addWidget(outputs_node_label)
        outputs_node_label.setMinimumWidth(50)
        outputs_labels.setStretch(0, 1)
        outputs_labels.addWidget(outputs_action_label)
        outputs_action_label.setMinimumWidth(40)
        outputs_labels.setStretch(1, 1)
        outputs_labels.addWidget(outputs_signal_label)
        outputs_signal_label.setMinimumWidth(250)
        outputs_labels.setStretch(2, 1)
        outputs_labels.addWidget(outputs_value_label)
        outputs_value_label.setFixedWidth(70)
        outputs_labels.addWidget(outputs_basal_value_label)
        outputs_basal_value_label.setFixedWidth(70)
        outputs_labels.addWidget(outputs_smoothing_label)
        outputs_labels.addSpacing(40)

        self.physiboss_outputs_layout.addLayout(outputs_labels)
        outputs_groupbox.setLayout(self.physiboss_outputs_layout)

        self.physiboss_outputs = []
        ly.addWidget(outputs_groupbox)

        outputs_addbutton = QPushButton("Add new output")
        outputs_addbutton.setStyleSheet("QPushButton { color: black }")
        outputs_addbutton.clicked.connect(self.physiboss_clicked_add_output)
        ly.addWidget(outputs_addbutton)


        inheritance_groupbox = QGroupBox("Inheritance")

        self.physiboss_inheritance_layout = QVBoxLayout()

        self.physiboss_global_inheritance = QHBoxLayout()

        self.physiboss_global_inheritance_checkbox = QCheckBox_custom('Global inheritance')
        self.physiboss_global_inheritance_flag = False
        self.physiboss_global_inheritance_checkbox.setEnabled(True)
        self.physiboss_global_inheritance_checkbox.setChecked(self.physiboss_global_inheritance_flag)
        self.physiboss_global_inheritance_checkbox.clicked.connect(self.physiboss_global_inheritance_checkbox_cb)
        self.physiboss_global_inheritance.addWidget(self.physiboss_global_inheritance_checkbox)
        self.physiboss_inheritance_layout.addLayout(self.physiboss_global_inheritance)
        
        
        inheritance_labels = QHBoxLayout()
        inheritance_node_label = QLabel("Node")
        inheritance_node_label.setFixedWidth(200)
        inheritance_value_label = QLabel("Value")
        inheritance_value_label.setFixedWidth(150)
        inheritance_labels.addWidget(inheritance_node_label)
        inheritance_labels.addWidget(inheritance_value_label)
        inheritance_labels.addStretch(1)

        self.physiboss_inheritance_layout.addLayout(inheritance_labels)
        inheritance_groupbox.setLayout(self.physiboss_inheritance_layout)
        self.physiboss_node_specific_inheritance = []

        ly.addWidget(inheritance_groupbox)

        inheritance_addbutton = QPushButton("Add node-specific inheritance")
        inheritance_addbutton.clicked.connect(self.physiboss_clicked_add_node_inheritance)
        ly.addWidget(inheritance_addbutton)

        self.layout = QVBoxLayout(self)  # leave this!
        print("\n---------- at 6")
        self.layout.addWidget(self.physiboss_boolean_frame )
        print("\n---------- end of SBML_ODEs")

    def choose_bnd_file(self):
        file , check = QFileDialog.getOpenFileName(None, "Please select a MaBoSS BND file",
                                               "", "MaBoSS BND Files (*.bnd)")
        if check:
            self.physiboss_bnd_file.setText(os.path.relpath(file, os.getcwd()))
            
    def choose_cfg_file(self):
        file , check = QFileDialog.getOpenFileName(None, "Please select a MaBoSS CFG file",
                                               "", "MaBoSS CFG Files (*.cfg)")
        if check:
            self.physiboss_cfg_file.setText(os.path.relpath(file, os.getcwd()))

    def physiboss_bnd_filename_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['bnd_filename'] = text
            self.physiboss_update_list_nodes()
    
    def physiboss_cfg_filename_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['cfg_filename'] = text
            self.physiboss_update_list_parameters()

    def physiboss_update_list_signals(self):

        if self.celldef_tab.current_cell_def == None:
            return
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:

            self.physiboss_signals = []
            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_signals.append(substrate)

            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_signals.append("intracellular " + substrate)
        
            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_signals.append(substrate + " gradient")
        
            self.physiboss_signals += ["pressure", "volume"]

            for celltype in self.celldef_tab.celltypes_list:
                self.physiboss_signals.append("contact with " + celltype)

            for custom_data in self.celldef_tab.master_custom_var_d.keys():
                self.physiboss_signals.append("custom:" + custom_data)

            self.physiboss_signals += ["contact with live cell", "contact with dead cell", "contact with basement membrane", "damage", "dead", "attacking", "total attack time", "time", "damage delivered"]

            for i, (name, _, _, _, _, _, _, _) in enumerate(self.physiboss_inputs):
                name.currentIndexChanged.disconnect()
                name.clear()
                for signal in self.physiboss_signals:
                    name.addItem(signal)
            
                if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"] is not None
                    and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"] in self.physiboss_signals
                ):
                    name.setCurrentIndex(self.physiboss_signals.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"]))
                else:
                    name.setCurrentIndex(-1)
        
                name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_signal_changed(i, index))

    def physiboss_update_list_behaviours(self):

        if self.celldef_tab.current_cell_def == None:
            return
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:

            self.physiboss_behaviours = []
            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_behaviours.append(substrate + " secretion")

            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_behaviours.append(substrate + " secretion target")
        
            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_behaviours.append(substrate + " uptake")

            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_behaviours.append("chemotactic response to " + substrate)

            for substrate in self.celldef_tab.substrate_list:
                self.physiboss_behaviours.append(substrate + " export")

            for custom_data in self.celldef_tab.master_custom_var_d.keys():
                self.physiboss_behaviours.append("custom:" + custom_data)
        
            self.physiboss_behaviours += [
                "cycle entry", "exit from cycle phase 0", "exit from cycle phase 1", "exit from cycle phase 2", "exit from cycle phase 3", "exit from cycle phase 4", "exit from cycle phase 5",
                "apoptosis", "necrosis", "migration speed", "migration bias", "migration persistence time", "chemotactic response to oxygen", 
                "cell-cell adhesion", "cell-cell adhesion elastic constant"
            ]

            for celltype in self.celldef_tab.celltypes_list:
                self.physiboss_behaviours.append("adhesive affinity to " + celltype)

            self.physiboss_behaviours += ["relative maximum adhesion distance", "cell-cell repulsion", "cell-BM adhesion", "cell-BM repulsion", "phagocytose apoptotic cell", "phagocytose necrotic cell", "phagocytose other dead cell"]

            for celltype in self.celldef_tab.celltypes_list:
                self.physiboss_behaviours.append("phagocytose " + celltype)

            for celltype in self.celldef_tab.celltypes_list:
                self.physiboss_behaviours.append("attack " + celltype)

            for celltype in self.celldef_tab.celltypes_list:
                self.physiboss_behaviours.append("fuse " + celltype)

            for celltype in self.celldef_tab.celltypes_list:
                self.physiboss_behaviours.append("transform to " + celltype)


            for i, (name, _, _, _, _, _, _, _) in enumerate(self.physiboss_outputs):
                name.currentIndexChanged.disconnect()
                name.clear()
                for behaviour in self.physiboss_behaviours:
                    name.addItem(behaviour)

                if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"] is not None
                    and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"] in self.physiboss_behaviours
                ):
                    name.setCurrentIndex(self.physiboss_behaviours.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"]))
                else:
                    name.setCurrentIndex(-1)

                name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_behaviour_changed(i, index))

    def physiboss_update_list_nodes(self):

        t_intracellular = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]
        
        if t_intracellular is not None:

            # Here I started by looking at both the bnd and the cfg
            if (
                t_intracellular is not None 
                and "bnd_filename" in t_intracellular.keys() 
                and t_intracellular['bnd_filename'] is not None 
                and len(t_intracellular['bnd_filename']) > 0
                and os.path.exists(os.path.join(os.getcwd(), t_intracellular["bnd_filename"])) 
                ):
                list_nodes = []
                with open(os.path.join(os.getcwd(), t_intracellular["bnd_filename"]), 'r') as bnd_file:
                    list_nodes = sorted([node.split(" ")[1].strip() for node in bnd_file.readlines() if node.strip().lower().startswith("node")])
            
                if len(list_nodes) > 0:
                    self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"] = list_nodes

                for i, (node, _, _, _) in enumerate(self.physiboss_initial_states):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_initial_value_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]["node"] = ""
                        node.setCurrentIndex(-1)

                for i, (node, _, _, _) in enumerate(self.physiboss_mutants):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_mutants_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] = ""
                        node.setCurrentIndex(-1)


                for i, (_, node, _, _, _, _, _, _) in enumerate(self.physiboss_inputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] = ""
                        node.setCurrentIndex(-1)
        
                for i, (_, node, _, _, _, _, _, _) in enumerate(self.physiboss_outputs):
                    node.currentIndexChanged.disconnect()
                    node.clear()
                    for name in list_nodes:
                        node.addItem(name)
                    node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] in list_nodes
                    ):
                        node.setCurrentIndex(list_nodes.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] not in list_nodes:
                        node.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] = list_nodes[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] = ""
                        node.setCurrentIndex(-1)
          
    def physiboss_update_list_parameters(self):
        
        t_intracellular = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]        
        if t_intracellular is not None:
            # Here I started by looking at both the bnd and the cfg
            if (
                t_intracellular is not None 
                and "cfg_filename" in t_intracellular.keys() 
                and t_intracellular['cfg_filename'] is not None \
                and len(t_intracellular['cfg_filename']) > 0
                and os.path.exists(os.path.join(os.getcwd(), t_intracellular["cfg_filename"])) 
                # and t_intracellular["cfg_filename"] and and os.path.exists(t_intracellular["cfg_filename"])
                ):
                list_parameters = []
                # list_internal_nodes = []
                with open(os.path.join(os.getcwd(), t_intracellular["cfg_filename"]), 'r') as cfg_file:
                    for line in cfg_file.readlines():
                        if line.strip().startswith("$"):
                            list_parameters.append(line.split("=")[0].strip())
                            
                        # elif ".is_internal" in line:
                        #     tokens = line.split("=")
                        #     value = tokens[1].strip()[:-1].lower() in ["1", "true"]
                        #     node = tokens[0].strip().replace(".is_internal", "")
                        #     if value:
                        #         list_internal_nodes.append(node)
                list_parameters = sorted(list_parameters)
                # list_output_nodes = list(set(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]).difference(set(list_internal_nodes)))
                if len(list_parameters) > 0:
                    self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"] = list_parameters
                
                for i, (param, _, _, _) in enumerate(self.physiboss_parameters):
                    param.currentIndexChanged.disconnect()
                    param.clear()
                    for name in list_parameters:
                        param.addItem(name)
                    param.currentIndexChanged.connect(lambda index, i=i: self.physiboss_parameters_node_changed(i, index))

                    if (self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] is not None
                        and self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] in list_parameters
                    ):
                        param.setCurrentIndex(list_parameters.index(self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"]))
                    elif self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] == "" or self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] not in list_parameters:
                        param.setCurrentIndex(0)
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] = list_parameters[0]
                    else:
                        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] = ""
                        param.setCurrentIndex(-1)

    def physiboss_time_step_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['time_step'] = text
    
    def physiboss_scaling_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['scaling'] = text
    
    def physiboss_time_stochasticity_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['time_stochasticity'] = text
    
    def physiboss_starttime_changed(self, text):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]['start_time'] = text
    
    def physiboss_clicked_add_initial_value(self):
        self.physiboss_add_initial_values()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"].append({
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'value': "1.0"
        })

    def physiboss_add_initial_values(self):

        initial_states_editor = QHBoxLayout()
        initial_states_dropdown = QComboBox_custom()
        initial_states_dropdown.setFixedWidth(150)
        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                initial_states_dropdown.addItem(node)
        initial_states_value = QLineEdit("1.0")
        initial_states_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        initial_states_remove.setStyleSheet("QPushButton { color: black }")

        id = len(self.physiboss_initial_states)
        initial_states_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_initial_value_node_changed(id, index))
        initial_states_value.textChanged.connect(lambda text, id=id: self.physiboss_initial_value_value_changed(id, text))
        initial_states_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_initial_values(id))

        initial_states_editor.addWidget(initial_states_dropdown)
        initial_states_editor.addWidget(initial_states_value)
        initial_states_editor.addWidget(initial_states_remove)

        self.physiboss_initial_states_layout.addLayout(initial_states_editor)
        self.physiboss_initial_states.append((initial_states_dropdown, initial_states_value, initial_states_remove, initial_states_editor))

    def physiboss_clicked_remove_initial_values(self, i):
        self.physiboss_remove_initial_values(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]

    def physiboss_remove_initial_values(self, id):
        self.physiboss_initial_states[id][0].currentIndexChanged.disconnect()
        self.physiboss_initial_states[id][0].deleteLater()
        self.physiboss_initial_states[id][1].textChanged.disconnect()
        self.physiboss_initial_states[id][1].deleteLater()
        self.physiboss_initial_states[id][2].clicked.disconnect()
        self.physiboss_initial_states[id][2].deleteLater()
        self.physiboss_initial_states[id][3].deleteLater()
        del self.physiboss_initial_states[id]
        
        # Here we should remap the clicked method to have the proper id
        for i, initial_state in enumerate(self.physiboss_initial_states):
            node, value, button, _ = initial_state
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_initial_value_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_initial_value_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_initial_values(i))

    def physiboss_clear_initial_values(self):
        for i, _ in reversed(list(enumerate(self.physiboss_initial_states))):
            self.physiboss_remove_initial_values(i)
    
    def physiboss_initial_value_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]['node'] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]

    def physiboss_initial_value_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"][i]['value'] = text
    
    def physiboss_clicked_add_mutant(self):
        self.physiboss_add_mutant()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"].append({
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'value': "0",
        })

    def physiboss_add_mutant(self):

        mutants_editor = QHBoxLayout()        
        
        mutants_node_dropdown = QComboBox_custom()
        mutants_node_dropdown.setFixedWidth(150)
        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                mutants_node_dropdown.addItem(node)
        
        mutants_value = QLineEdit("0")
        mutants_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        id = len(self.physiboss_mutants)
        mutants_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_mutants_node_changed(id, index))
        mutants_value.textChanged.connect(lambda text, id=id: self.physiboss_mutants_value_changed(id, text))
        mutants_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_mutant(id))

        mutants_editor.addWidget(mutants_node_dropdown)
        mutants_editor.addWidget(mutants_value)
        mutants_editor.addWidget(mutants_remove)
        self.physiboss_mutants_layout.addLayout(mutants_editor)
        self.physiboss_mutants.append((mutants_node_dropdown, mutants_value, mutants_remove, mutants_editor))

    def physiboss_clicked_remove_mutant(self, i):
        self.physiboss_remove_mutant(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]

    def physiboss_remove_mutant(self, id):
        self.physiboss_mutants[id][0].currentIndexChanged.disconnect()
        self.physiboss_mutants[id][0].deleteLater()
        self.physiboss_mutants[id][1].textChanged.disconnect()
        self.physiboss_mutants[id][1].deleteLater()
        self.physiboss_mutants[id][2].clicked.disconnect()
        self.physiboss_mutants[id][2].deleteLater()
        self.physiboss_mutants[id][3].deleteLater()
        del self.physiboss_mutants[id]
      
        # Here we should remap the clicked method to have the proper id
        for i, mutant in enumerate(self.physiboss_mutants):
            name, value, button, _ = mutant
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_mutants_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_mutants_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_mutant(i))

    def physiboss_clear_mutants(self):
        for i, _ in reversed(list(enumerate(self.physiboss_mutants))):
            self.physiboss_remove_mutant(i)
    
    def physiboss_mutants_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]

    def physiboss_mutants_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"][i]["value"] = text

    def physiboss_clicked_add_parameter(self):
        self.physiboss_add_parameter()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"].append({
            'name': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'value': "1.0"
        })

    def physiboss_add_parameter(self):

        parameters_editor = QHBoxLayout()
        parameters_dropdown = QComboBox_custom()
        parameters_dropdown.setFixedWidth(150)
        if "list_parameters" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for parameter in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"]:
                parameters_dropdown.addItem(parameter)
        parameters_value = QLineEdit("1.0")
        parameters_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
       
        id = len(self.physiboss_parameters)
        parameters_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_parameters_node_changed(id, index))
        parameters_value.textChanged.connect(lambda text, id=id: self.physiboss_parameters_value_changed(id, text))
        parameters_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_parameter(id))

        parameters_editor.addWidget(parameters_dropdown)
        parameters_editor.addWidget(parameters_value)
        parameters_editor.addWidget(parameters_remove)
        self.physiboss_parameters_layout.addLayout(parameters_editor)
        self.physiboss_parameters.append((parameters_dropdown, parameters_value, parameters_remove, parameters_editor))

    def physiboss_clicked_remove_parameter(self, i):
        self.physiboss_remove_parameter(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]

    def physiboss_remove_parameter(self, id):
        self.physiboss_parameters[id][0].currentIndexChanged.disconnect()
        self.physiboss_parameters[id][0].deleteLater()
        self.physiboss_parameters[id][1].textChanged.disconnect()
        self.physiboss_parameters[id][1].deleteLater()
        self.physiboss_parameters[id][2].clicked.disconnect()
        self.physiboss_parameters[id][2].deleteLater()
        self.physiboss_parameters[id][3].deleteLater()
        del self.physiboss_parameters[id]

        # Here we should remap the clicked method to have the proper id
        for i, parameter in enumerate(self.physiboss_parameters):
            name, value, button, _ = parameter
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_parameters_node_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_parameters_value_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_parameter(i))
        
    def physiboss_clear_parameters(self):
        for i, _ in reversed(list(enumerate(self.physiboss_parameters))):
            self.physiboss_remove_parameter(i)

    def physiboss_parameters_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["name"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_parameters"][index]

    def physiboss_parameters_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"][i]["value"] = text
    
    def physiboss_clicked_add_input(self):
        self.physiboss_add_input()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"].append({
            'name': self.physiboss_signals[0],
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'action': 'activation',
            'threshold': "1.0",
            'inact_threshold': "1.0",
            'smoothing': "0"
        })

    def physiboss_add_input(self):

        inputs_editor = QHBoxLayout()

        inputs_signal_dropdown = QComboBox_custom()

        for signal in self.physiboss_signals:
            inputs_signal_dropdown.addItem(signal)
        
        inputs_node_dropdown = QComboBox_custom()

        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                inputs_node_dropdown.addItem(node)
        
        inputs_action = QComboBox_custom()

        inputs_action.addItem("activation")
        inputs_action.addItem("inhibition")

        inputs_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)

        id = len(self.physiboss_inputs)
        inputs_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_inputs_node_changed(id, index))
        inputs_signal_dropdown.currentIndexChanged.connect(lambda text, id=id: self.physiboss_inputs_signal_changed(id, text))
        inputs_action.currentIndexChanged.connect(lambda index, id=id: self.physiboss_inputs_action_changed(id, index))
        inputs_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_input(id))

        inputs_editor.addWidget(inputs_signal_dropdown)
        inputs_editor.setStretch(0, 1)
        inputs_editor.addWidget(inputs_action)
        inputs_editor.setStretch(1, 1)
        inputs_editor.addWidget(inputs_node_dropdown)
        inputs_editor.setStretch(2, 1)
        
        inputs_threshold = QLineEdit("1.0")
        inputs_inact_threshold = QLineEdit("1.0")
        inputs_smoothing = QLineEdit("0")
        inputs_threshold.textChanged.connect(lambda text, id=id: self.physiboss_inputs_threshold_changed(id, text))
        inputs_inact_threshold.textChanged.connect(lambda text, id=id: self.physiboss_inputs_inact_threshold_changed(id, text))
        inputs_smoothing.textChanged.connect(lambda text, id=id: self.physiboss_inputs_smoothing_changed(id, text))
        
        inputs_editor.addWidget(inputs_threshold)
        inputs_threshold.setFixedWidth(70)
        inputs_editor.addWidget(inputs_inact_threshold)
        inputs_inact_threshold.setFixedWidth(70)
        inputs_editor.addWidget(inputs_smoothing)
        inputs_smoothing.setFixedWidth(70)


        inputs_remove.setFixedWidth(30)
        inputs_editor.addWidget(inputs_remove)


        self.physiboss_inputs_layout.addLayout(inputs_editor)
        self.physiboss_inputs.append((inputs_signal_dropdown, inputs_node_dropdown, inputs_action, inputs_threshold, inputs_inact_threshold, inputs_smoothing, inputs_remove, inputs_editor))#, inputs_editor_2))
    
    def physiboss_inputs_signal_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["name"] = self.physiboss_signals[index]
        
    def physiboss_inputs_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]
        
    def physiboss_inputs_action_changed(self, i, index):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["action"] = "activation" if index == 0 else "inhibition"

    def physiboss_inputs_threshold_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["threshold"] = text

    def physiboss_inputs_inact_threshold_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["inact_threshold"] = text

    def physiboss_inputs_smoothing_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]["smoothing"] = text

    def physiboss_clicked_remove_input(self, i):
        self.physiboss_remove_input(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"][i]

    def physiboss_remove_input(self, id):
        self.physiboss_inputs[id][0].currentIndexChanged.disconnect()
        self.physiboss_inputs[id][0].deleteLater()
        self.physiboss_inputs[id][1].currentIndexChanged.disconnect()
        self.physiboss_inputs[id][1].deleteLater()
        self.physiboss_inputs[id][2].currentIndexChanged.disconnect()
        self.physiboss_inputs[id][2].deleteLater()
        self.physiboss_inputs[id][3].textChanged.disconnect()
        self.physiboss_inputs[id][3].deleteLater()
        self.physiboss_inputs[id][4].textChanged.disconnect()
        self.physiboss_inputs[id][4].deleteLater()
        self.physiboss_inputs[id][5].textChanged.disconnect()
        self.physiboss_inputs[id][5].deleteLater()
        self.physiboss_inputs[id][6].clicked.disconnect()
        self.physiboss_inputs[id][6].deleteLater()
        del self.physiboss_inputs[id]

        # Here we should remap the clicked method to have the proper id
        for i, input in enumerate(self.physiboss_inputs):
            signal, node, action, threshold, inact_threshold, smoothing, button, _ = input
            signal.currentIndexChanged.disconnect()
            signal.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_signal_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index, i=i: self.physiboss_inputs_action_changed(i, index))
            threshold.textChanged.disconnect()
            threshold.textChanged.connect(lambda text, i=i: self.physiboss_inputs_threshold_changed(i, text))
            inact_threshold.textChanged.disconnect()
            inact_threshold.textChanged.connect(lambda text, i=i: self.physiboss_inputs_inact_threshold_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text, i=i: self.physiboss_inputs_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_input(i))
        
    def physiboss_clear_inputs(self):
        for i, _ in reversed(list(enumerate(self.physiboss_inputs))):
            self.physiboss_remove_input(i)

    def physiboss_clicked_add_output(self):
        self.physiboss_add_output()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"].append({
            'name': self.physiboss_behaviours[0],
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'action': 'activation',
            'value': "1.0",
            'basal_value': "0.0",
            'smoothing': "0"
        })

    def physiboss_add_output(self):

        outputs_editor = QHBoxLayout()
        outputs_behaviour_dropdown = QComboBox_custom()

        for behaviour in self.physiboss_behaviours:
            outputs_behaviour_dropdown.addItem(behaviour)
        
        outputs_node_dropdown = QComboBox_custom()

        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                outputs_node_dropdown.addItem(node)
        
        outputs_action = QComboBox_custom()

        outputs_action.addItem("activation")
        outputs_action.addItem("inhibition")
        outputs_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)
        outputs_remove.setFixedWidth(30)


        id = len(self.physiboss_outputs)
        outputs_node_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_outputs_node_changed(id, index))
        outputs_behaviour_dropdown.currentIndexChanged.connect(lambda text, id=id: self.physiboss_outputs_behaviour_changed(id, text))
        outputs_action.currentIndexChanged.connect(lambda index, id=id: self.physiboss_outputs_action_changed(id, index))
        outputs_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_output(id))

        outputs_editor.addWidget(outputs_node_dropdown)
        outputs_editor.setStretch(0, 1)
        outputs_editor.addWidget(outputs_action)
        outputs_editor.setStretch(1, 1)
        outputs_editor.addWidget(outputs_behaviour_dropdown)
        outputs_editor.setStretch(2, 1)
        
        outputs_value = QLineEdit("1.0")
        outputs_basal_value = QLineEdit("0.0")
        outputs_smoothing = QLineEdit("0")        
        outputs_value.textChanged.connect(lambda text, id=id: self.physiboss_outputs_value_changed(id, text))
        outputs_basal_value.textChanged.connect(lambda text, id=id: self.physiboss_outputs_basal_value_changed(id, text))
        outputs_smoothing.textChanged.connect(lambda text, id=id: self.physiboss_outputs_smoothing_changed(id, text))
        
        outputs_editor.addWidget(outputs_value)
        outputs_editor.addWidget(outputs_basal_value)
        outputs_editor.addWidget(outputs_smoothing)

        outputs_value.setFixedWidth(70)
        outputs_basal_value.setFixedWidth(70)
        outputs_smoothing.setFixedWidth(70)
        
        outputs_editor.addWidget(outputs_remove)

        self.physiboss_outputs_layout.addLayout(outputs_editor)
        self.physiboss_outputs.append((outputs_behaviour_dropdown, outputs_node_dropdown, outputs_action, outputs_value, outputs_basal_value, outputs_smoothing, outputs_remove, outputs_editor))#, outputs_editor_2))
    
    def physiboss_outputs_behaviour_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["name"] = self.physiboss_behaviours[index]
        
    def physiboss_outputs_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]

    def physiboss_outputs_action_changed(self, i, index):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["action"] = "activation" if index == 0 else "inhibition"

    def physiboss_outputs_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["value"] = text

    def physiboss_outputs_basal_value_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["basal_value"] = text

    def physiboss_outputs_smoothing_changed(self, i, text):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]["smoothing"] = text

    def physiboss_clicked_remove_output(self, i):
        self.physiboss_remove_output(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"][i]

    def physiboss_remove_output(self, id):
        self.physiboss_outputs[id][0].currentIndexChanged.disconnect()
        self.physiboss_outputs[id][0].deleteLater()
        self.physiboss_outputs[id][1].currentIndexChanged.disconnect()
        self.physiboss_outputs[id][1].deleteLater()
        self.physiboss_outputs[id][2].currentIndexChanged.disconnect()
        self.physiboss_outputs[id][2].deleteLater()
        self.physiboss_outputs[id][3].textChanged.disconnect()
        self.physiboss_outputs[id][3].deleteLater()
        self.physiboss_outputs[id][4].textChanged.disconnect()
        self.physiboss_outputs[id][4].deleteLater()
        self.physiboss_outputs[id][5].textChanged.disconnect()
        self.physiboss_outputs[id][5].deleteLater()
        self.physiboss_outputs[id][6].clicked.disconnect()
        self.physiboss_outputs[id][6].deleteLater()
        del self.physiboss_outputs[id]

        # Here we should remap the clicked method to have the proper id
        for i, output in enumerate(self.physiboss_outputs):
            name, node, action, value, basal_value, smoothing, button, _ = output
            name.currentIndexChanged.disconnect()
            name.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_behaviour_changed(i, index))
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_node_changed(i, index))
            action.currentIndexChanged.disconnect()
            action.currentIndexChanged.connect(lambda index, i=i: self.physiboss_outputs_action_changed(i, index))
            value.textChanged.disconnect()
            value.textChanged.connect(lambda text, i=i: self.physiboss_outputs_value_changed(i, text))
            basal_value.textChanged.disconnect()
            basal_value.textChanged.connect(lambda text, i=i: self.physiboss_outputs_basal_value_changed(i, text))
            smoothing.textChanged.disconnect()
            smoothing.textChanged.connect(lambda text, i=i: self.physiboss_outputs_smoothing_changed(i, text))
            button.clicked.disconnect()
            button.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_output(i))
            
    def physiboss_clear_outputs(self):
        for i, _ in reversed(list(enumerate(self.physiboss_outputs))):
            self.physiboss_remove_output(i)

    def physiboss_global_inheritance_checkbox_cb(self, bval):
        self.physiboss_global_inheritance_flag = bval
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is not None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["global_inheritance"] = str(bval)

    def physiboss_clicked_add_node_inheritance(self):
        self.physiboss_add_node_inheritance()
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"].append({
            'node': self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][0] if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys() else "",
            'flag': str(not self.physiboss_global_inheritance),
        })
        
    def physiboss_add_node_inheritance(self):
        
        node_inheritance_editor = QHBoxLayout()
        node_inheritance_dropdown = QComboBox_custom()
        node_inheritance_dropdown.setFixedWidth(200)
        if "list_nodes" in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]:
            for node in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"]:
                node_inheritance_dropdown.addItem(node)
        
                
        node_inheritance_checkbox = QCheckBox_custom('Node-specific inheritance')
        node_inheritance_checkbox.setEnabled(True)
        node_inheritance_checkbox.setChecked(not self.physiboss_global_inheritance_flag)
        
        node_inheritance_remove = QPushButton(icon=QIcon(sys.path[0] +"/icon/bin.svg"), parent=self)


        id = len(self.physiboss_node_specific_inheritance)
        node_inheritance_dropdown.currentIndexChanged.connect(lambda index, id=id: self.physiboss_node_inheritance_node_changed(id, index))
        node_inheritance_checkbox.clicked.connect(lambda bval, id=id: self.physiboss_node_inheritance_flag_changed(id, bval))
        node_inheritance_remove.clicked.connect(lambda _, id=id: self.physiboss_clicked_remove_node_inheritance(id))
        node_inheritance_remove.setFixedWidth(30)
        node_inheritance_editor.addWidget(node_inheritance_dropdown)
        node_inheritance_editor.addWidget(node_inheritance_checkbox)
        node_inheritance_editor.addWidget(node_inheritance_remove)
        node_inheritance_editor.addStretch(1)
        
       
        self.physiboss_inheritance_layout.addLayout(node_inheritance_editor)
        self.physiboss_node_specific_inheritance.append((node_inheritance_dropdown, node_inheritance_checkbox, node_inheritance_remove, node_inheritance_editor))
    
    def physiboss_remove_node_inheritance(self, id):
        self.physiboss_node_specific_inheritance[id][0].currentIndexChanged.disconnect()
        self.physiboss_node_specific_inheritance[id][0].deleteLater()
        self.physiboss_node_specific_inheritance[id][1].clicked.disconnect()
        self.physiboss_node_specific_inheritance[id][1].deleteLater()
        self.physiboss_node_specific_inheritance[id][2].clicked.disconnect()
        self.physiboss_node_specific_inheritance[id][2].deleteLater()
        self.physiboss_node_specific_inheritance[id][3].deleteLater()
        del self.physiboss_node_specific_inheritance[id]
    
    
        # Here we should remap the clicked method to have the proper id
        for i, node_inheritance in enumerate(self.physiboss_node_specific_inheritance):
            node, flag, remove, _ = node_inheritance
            node.currentIndexChanged.disconnect()
            node.currentIndexChanged.connect(lambda index, i=i: self.physiboss_node_inheritance_node_changed(i, index))
            flag.clicked.disconnect()
            flag.clicked.connect(lambda bval, i=i: self.physiboss_node_inheritance_flag_changed(i, bval))
            remove.clicked.disconnect()
            remove.clicked.connect(lambda _, i=i: self.physiboss_clicked_remove_node_inheritance(i))
      
    def physiboss_node_inheritance_node_changed(self, i, index):
        if index >= 0:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"][i]["node"] = self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["list_nodes"][index]
  
    def physiboss_node_inheritance_flag_changed(self, i, bval):
        self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"][i]["flag"] = str(bval)
  
    def physiboss_clicked_remove_node_inheritance(self, i):
        self.physiboss_remove_node_inheritance(i)
        del self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"][i]
        
    def physiboss_clear_node_inheritance(self):
        for i, _ in reversed(list(enumerate(self.physiboss_node_specific_inheritance))):
            self.physiboss_remove_node_inheritance(i)

    def clear(self):
        self.physiboss_bnd_file.setText("")
        self.physiboss_cfg_file.setText("")
        self.physiboss_clear_initial_values()
        self.physiboss_clear_mutants()
        self.physiboss_clear_parameters()
        self.physiboss_clear_inputs()
        self.physiboss_clear_outputs()
        self.physiboss_clear_node_inheritance()
        self.physiboss_time_step.setText("")
        self.physiboss_time_stochasticity.setText("")
        self.physiboss_scaling.setText("")
        self.physiboss_starttime.setText("")
        self.physiboss_global_inheritance_checkbox.setChecked(False)

    def init_param_d(self):
        if self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] is None:
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"] = {"type": "maboss"}
            
        if 'initial_values' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["initial_values"] = []
            self.physiboss_clear_initial_values()
        
        if 'mutants' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["mutants"] = []
            self.physiboss_clear_mutants()

        if 'parameters' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["parameters"] = []
            self.physiboss_clear_parameters()

        if 'inputs' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["inputs"] = []
            self.physiboss_clear_inputs()

        if 'outputs' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["outputs"] = []
            self.physiboss_clear_outputs()

        if 'node_inheritance' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["node_inheritance"] = []
            self.physiboss_clear_node_inheritance()

        if 'time_step' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.physiboss_time_step.setText("12.0")

        if 'time_stochasticity' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.physiboss_time_stochasticity.setText("0.0")
        
        if 'scaling' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.physiboss_scaling.setText("1.0")
        
        if 'start_time' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.physiboss_starttime.setText("0.0")
            
        if 'global_inheritance' not in self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"].keys():
            self.celldef_tab.param_d[self.celldef_tab.current_cell_def]["intracellular"]["global_inheritance"] = "False"
            self.physiboss_global_inheritance_checkbox.setChecked(False)
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()


    #-----------------------------------------------------------
    def fill_gui(self, cdname):
        print(f'\n\n------------physiboss_intra.py: fill_gui():')

        self.physiboss_clear_initial_values()
        self.physiboss_clear_mutants()
        self.physiboss_clear_parameters()
        self.physiboss_clear_node_inheritance()
        self.physiboss_clear_inputs()
        self.physiboss_clear_outputs()

        if "bnd_filename" in self.celldef_tab.param_d[cdname]["intracellular"].keys(): 
            self.physiboss_bnd_file.setText(self.celldef_tab.param_d[cdname]["intracellular"]["bnd_filename"])
        if "cfg_filename" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.physiboss_cfg_file.setText(self.celldef_tab.param_d[cdname]["intracellular"]["cfg_filename"])

        if "time_step" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.physiboss_time_step.setText(self.celldef_tab.param_d[cdname]["intracellular"]["time_step"])
        if "time_stochasticity" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.physiboss_time_stochasticity.setText(self.celldef_tab.param_d[cdname]["intracellular"]["time_stochasticity"])
        if "scaling" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.physiboss_scaling.setText(self.celldef_tab.param_d[cdname]["intracellular"]["scaling"])
        if "start_time" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.physiboss_starttime.setText(self.celldef_tab.param_d[cdname]["intracellular"]["start_time"])
        if "global_inheritance" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
            self.physiboss_global_inheritance_checkbox.setChecked(self.celldef_tab.param_d[cdname]["intracellular"]["global_inheritance"] == "True")

        self.celldef_tab.fill_substrates_comboboxes()
        self.celldef_tab.fill_celltypes_comboboxes()
        self.physiboss_update_list_signals()
        self.physiboss_update_list_behaviours()
        self.physiboss_update_list_nodes()
        self.physiboss_update_list_parameters()
        
        for i, node_inheritance in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["node_inheritance"]):
            self.physiboss_add_node_inheritance()
            node, flag, _, _ = self.physiboss_node_specific_inheritance[i]
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(node_inheritance["node"]))
            flag.setChecked(node_inheritance["flag"] == "True")
            
        for i, initial_value in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["initial_values"]):
            self.physiboss_add_initial_values()
            node, value, _, _ = self.physiboss_initial_states[i]
            if "list_nodes" in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(initial_value["node"]))
                value.setText(initial_value["value"])
            else:
                print("----- ERROR(0): update_intracellular_params() has no 'list_nodes' key.")
                break

        for i, mutant in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["mutants"]):
            self.physiboss_add_mutant()
            node, value, _, _ = self.physiboss_mutants[i]
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(1): update_intracellular_params() has no 'list_nodes' key.")
                break
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(mutant["node"]))
            value.setText(mutant["value"])

        for i, parameter in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["parameters"]):
            self.physiboss_add_parameter()
            name, value, _, _ = self.physiboss_parameters[i]
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(2): update_intracellular_params() has no 'list_nodes' key.")
                break
            name.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_parameters"].index(parameter["name"]))
            value.setText(parameter["value"])

        
        for i, input in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["inputs"]):
            self.physiboss_add_input()
            name, node, action, threshold, inact_threshold, smoothing, _, _ = self.physiboss_inputs[i]
            logging.debug(f'update_intracellular_params(): cdname={cdname},  {input["name"]}={input["name"]}')
            logging.debug(f'  param_d= {self.celldef_tab.param_d[cdname]["intracellular"]}')
            name.setCurrentIndex(self.physiboss_signals.index(input["name"]))
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(3): update_intracellular_params() has no 'list_nodes' key.")
                break
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(input["node"]))
            action.setCurrentIndex(1 if input["action"] == "inhibition" else 0)
            threshold.setText(input["threshold"])
            inact_threshold.setText(input["inact_threshold"])
            smoothing.setText(input["smoothing"])

        for i, output in enumerate(self.celldef_tab.param_d[cdname]["intracellular"]["outputs"]):
            self.physiboss_add_output()
            name, node, action, value, basal_value, smoothing, _, _ = self.physiboss_outputs[i]
            name.setCurrentIndex(self.physiboss_behaviours.index(output["name"]))
            if "list_nodes" not in self.celldef_tab.param_d[cdname]["intracellular"].keys():
                print("----- ERROR(4): update_intracellular_params() has no 'list_nodes' key.")
                break
            node.setCurrentIndex(self.celldef_tab.param_d[cdname]["intracellular"]["list_nodes"].index(output["node"]))
            action.setCurrentIndex(1 if output["action"] == "inhibition" else 0)
            value.setText(output["value"])
            basal_value.setText(output["basal_value"])
            smoothing.setText(output["smoothing"])


    #-------------------------------------------------------------------
    # Get values from the dict and generate/write a new XML
    def fill_xml(self, pheno, cdef):
         
        # Checking if you should prevent saving because of missing input
        if 'bnd_filename' not in self.celldef_tab.param_d[cdef]['intracellular'] or self.celldef_tab.param_d[cdef]['intracellular']['bnd_filename'] in [None, ""]:
            raise PhysiBoSSCellDefException("Missing BND file in the " + cdef + " cell definition ")

        if 'cfg_filename' not in self.celldef_tab.param_d[cdef]['intracellular'] or self.celldef_tab.param_d[cdef]['intracellular']['cfg_filename'] in [None, ""]:
            raise PhysiBoSSCellDefException("Missing CFG file in the " + cdef + " cell definition ")

        intracellular = ET.SubElement(pheno, "intracellular", {"type": "maboss"})
        intracellular.text = self.celldef_tab.indent12  # affects indent of child
        intracellular.tail = "\n" + self.celldef_tab.indent10

        bnd_filename = ET.SubElement(intracellular, "bnd_filename")
        bnd_filename.text = self.celldef_tab.param_d[cdef]['intracellular']['bnd_filename']
        bnd_filename.tail = self.celldef_tab.indent12

        cfg_filename = ET.SubElement(intracellular, "cfg_filename")
        cfg_filename.text = self.celldef_tab.param_d[cdef]['intracellular']['cfg_filename']
        cfg_filename.tail = self.celldef_tab.indent12

        if len(self.celldef_tab.param_d[cdef]['intracellular']['initial_values']) > 0:
            initial_values = ET.SubElement(intracellular, "initial_values")
            initial_values.text = self.celldef_tab.indent14
            initial_values.tail = self.celldef_tab.indent12
            
            for initial_value_def in self.celldef_tab.param_d[cdef]['intracellular']['initial_values']:
                if initial_value_def["node"] != "" and initial_value_def["value"] != "":
                    initial_value = ET.SubElement(initial_values, "initial_value", {"intracellular_name": initial_value_def["node"]})
                    initial_value.text = initial_value_def["value"]
                    initial_value.tail = self.celldef_tab.indent14
            initial_value.tail = self.celldef_tab.indent12
            
        # Settings
        settings = ET.SubElement(intracellular, "settings")
        settings.text = self.celldef_tab.indent14
        settings.tail = self.celldef_tab.indent12
    
        time_step = ET.SubElement(settings, "intracellular_dt")
        time_step.text = self.celldef_tab.param_d[cdef]['intracellular']['time_step']
        time_step.tail = self.celldef_tab.indent14
        
        time_stochasticity = ET.SubElement(settings, "time_stochasticity")
        time_stochasticity.text = self.celldef_tab.param_d[cdef]['intracellular']['time_stochasticity']
        time_stochasticity.tail = self.celldef_tab.indent14
        
        scaling = ET.SubElement(settings, "scaling")
        scaling.text = self.celldef_tab.param_d[cdef]['intracellular']['scaling']
        scaling.tail = self.celldef_tab.indent12
        
        start_time = ET.SubElement(settings, "start_time")
        start_time.text = self.celldef_tab.param_d[cdef]['intracellular']['start_time']
        start_time.tail = self.celldef_tab.indent12
        
        inheritance = ET.SubElement(settings, "inheritance", {"global": self.celldef_tab.param_d[cdef]['intracellular']['global_inheritance']})
        if len(self.celldef_tab.param_d[cdef]["intracellular"]["node_inheritance"]) > 0:
            for node_inheritance_def in self.celldef_tab.param_d[cdef]["intracellular"]["node_inheritance"]:
                if node_inheritance_def["node"] != "" and node_inheritance_def["flag"] != "":
                    node_inheritance = ET.SubElement(inheritance, "inherit_node", {"intracellular_name": node_inheritance_def["node"]})
                    node_inheritance.text = node_inheritance_def["flag"]
                    node_inheritance.tail = self.celldef_tab.indent16

        if len(self.celldef_tab.param_d[cdef]["intracellular"]["mutants"]) > 0:
            scaling.tail = self.celldef_tab.indent14
            mutants = ET.SubElement(settings, "mutations")
            mutants.text = self.celldef_tab.indent16
            mutants.tail = self.celldef_tab.indent14
            
            for mutant_def in self.celldef_tab.param_d[cdef]["intracellular"]["mutants"]:
                if mutant_def["node"] != "" and mutant_def["value"] != "":
                    mutant = ET.SubElement(mutants, "mutation", {"intracellular_name": mutant_def["node"]})
                    mutant.text = mutant_def["value"]
                    mutant.tail = self.celldef_tab.indent16

            mutant.tail = self.celldef_tab.indent12

        if len(self.celldef_tab.param_d[cdef]['intracellular']['parameters']) > 0:
            scaling.tail = self.celldef_tab.indent14

            parameters = ET.SubElement(settings, "parameters")
            parameters.text = self.celldef_tab.indent16
            parameters.tail = self.celldef_tab.indent14
            
            for parameter_def in self.celldef_tab.param_d[cdef]['intracellular']['parameters']:
                if parameter_def["name"] != "" and parameter_def["value"] != "":
                    parameter = ET.SubElement(parameters, "parameter", {"intracellular_name": parameter_def["name"]})
                    parameter.text = parameter_def["value"]
                    parameter.tail = self.celldef_tab.indent16

            parameter.tail = self.celldef_tab.indent12

        # Mapping
        if len(self.celldef_tab.param_d[cdef]['intracellular']['inputs']) > 0 or len(self.celldef_tab.param_d[cdef]['intracellular']['outputs']) > 0:
            mapping = ET.SubElement(intracellular, "mapping")
            mapping.text = self.celldef_tab.indent14
            mapping.tail = self.celldef_tab.indent12

            tag_input = None
            for input in self.celldef_tab.param_d[cdef]['intracellular']['inputs']:
                
                if input['name'] != '' and input['node'] != '' and input['threshold'] != '' and input['action'] != '':
                    attribs = {
                        'physicell_name': input['name'], 'intracellular_name': input['node'], 
                    }

                    tag_input = ET.SubElement(mapping, 'input', attribs)
                    tag_input.text = self.celldef_tab.indent16
                    tag_input.tail = self.celldef_tab.indent14

                    tag_input_settings = ET.SubElement(tag_input, "settings")
                    tag_input_settings.text = self.celldef_tab.indent18
                    tag_input_settings.tail = self.celldef_tab.indent16
                    tag_input_action = ET.SubElement(tag_input_settings, "action")
                    tag_input_action.text = input["action"]
                    tag_input_action.tail = self.celldef_tab.indent18

                    tag_input_threshold = ET.SubElement(tag_input_settings, "threshold")
                    tag_input_threshold.text = input["threshold"]
                    tag_input_threshold.tail = self.celldef_tab.indent18

                    t_last_tag = tag_input_threshold
                    if input["inact_threshold"] != input["threshold"]:
                        tag_input_inact_threshold = ET.SubElement(tag_input_settings, "inact_threshold")
                        tag_input_inact_threshold.text = input["inact_threshold"]
                        tag_input_inact_threshold.tail = self.celldef_tab.indent18
                        t_last_tag = tag_input_inact_threshold
                    if input["smoothing"] != "":
                        tag_input_smoothing = ET.SubElement(tag_input_settings, "smoothing")
                        tag_input_smoothing.text = input["smoothing"]
                        tag_input_smoothing.tail = self.celldef_tab.indent18
                        t_last_tag = tag_input_smoothing

                    t_last_tag.tail = self.celldef_tab.indent14
                    
            tag_output = None
            for output in self.celldef_tab.param_d[cdef]['intracellular']['outputs']:

                if output['name'] != '' and output['node'] != '' and output['value'] != '' and output['action'] != '':
                    attribs = {
                        'physicell_name': output['name'], 'intracellular_name': output['node'], 
                    }

                    tag_output = ET.SubElement(mapping, 'output', attribs)
                    tag_output.text = self.celldef_tab.indent16
                    tag_output.tail = self.celldef_tab.indent12
                    
                    tag_output_settings = ET.SubElement(tag_output, "settings")
                    tag_output_settings.text = self.celldef_tab.indent18
                    tag_output_settings.tail = self.celldef_tab.indent14

                    tag_output_action = ET.SubElement(tag_output_settings, "action")
                    tag_output_action.text = output["action"]
                    tag_output_action.tail = self.celldef_tab.indent18

                    tag_output_value = ET.SubElement(tag_output_settings, "value")
                    tag_output_value.text = output["value"]
                    tag_output_value.tail = self.celldef_tab.indent18

                    t_last_tag = tag_output_value

                    if output["basal_value"] != output["value"]:
                        tag_output_base_value = ET.SubElement(tag_output_settings, "base_value")
                        tag_output_base_value.text = output["basal_value"]
                        tag_output_base_value.tail = self.celldef_tab.indent18
                        t_last_tag = tag_output_base_value
                    
                    if output["smoothing"] != "":
                        tag_output_smoothing = ET.SubElement(tag_output_settings, "smoothing")
                        tag_output_smoothing.text = output["smoothing"]
                        tag_output_smoothing.tail = self.celldef_tab.indent18
                        t_last_tag = tag_output_smoothing

                    t_last_tag.tail = self.celldef_tab.indent14
                    
            
            if len(self.celldef_tab.param_d[cdef]['intracellular']['outputs']) == 0 and tag_input is not None:
                tag_input.tail = self.celldef_tab.indent12
            elif tag_output is not None:
                tag_output.tail = self.celldef_tab.indent12
