import sublime_plugin
import re
import os
from ..helper import Helper
from ..constant import Constant
from ..parser.class_parser import ClassParser


class PhpmeImplementsCommand(sublime_plugin.TextCommand):
    """Implements interface"""

    def run(self, edit):
        self.methods = {}
        self.pending = {}
        self.list_methods = []
        self.collect_progress = 0
        self.helper = Helper(self.view)

        if self.helper.not_scope():
            self.helper.e_scope()
        else:
            mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
            if self.helper.not_class(mdef, ['class']):
                self.helper.e_class()
            elif len(mdef['implements']) == 0:
                self.helper.print_message('Class was not implement any interface')
            else:
                self.find_methods(mdef)
                self.run_schedule()

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_methods) > 0:
                options = [
                    ['Implement All', 'implement all methods'],
                    ['Implement Some', 'pick multiple method one by one']
                ]
                self.view.window().show_quick_panel(options+self.list_methods, self.on_method_selected)
            else:
                self.methods = self.pending
                self.collect_progress = 2
                self.run_schedule()
        elif self.collect_progress == 1:
            # ask again
            options = [['Done', 'done selecting method']]
            self.view.window().show_quick_panel(options+self.list_methods, self.on_method_selected)
        elif len(self.methods) > 0:
            self.view.run_command('phpme_post_implements', {'methods': self.methods})
        else:
            self.helper.print_message('No method to implements')

    def pick_method(self, index):
        method = self.list_methods[index][0]
        namespace = self.list_methods[index][1]
        if namespace not in self.methods:
            self.methods[namespace] = {}
        self.methods[namespace][method] = self.pending[namespace][method]
        del self.list_methods[index]

    def on_method_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    self.methods = self.pending
                    self.collect_progress = 2
                elif index == 1:
                    self.collect_progress = 1
                else:
                    self.pick_method(index - 2)
                    self.collect_progress = 2
            elif self.collect_progress == 1:
                if index == 0:
                    self.collect_progress = 2
                else:
                    self.pick_method(index - 1)
                    if len(self.list_methods) == 0:
                        self.collect_progress = 2
        else:
            self.collect_progress = 2

        self.run_schedule()

    def find_methods(self, mdef):
        indexes = []
        for alias, namespace in mdef['implements'].items():
            use = self.helper.decide_use(alias, namespace, mdef['namespace'], mdef['uses'])
            symbol = use.split('\\')[-1]
            for namespaces in self.helper.find_symbol(symbol, use):
                if namespaces[0] == use:
                    methods = self.helper.parse_class_tree(None, namespaces[0], namespaces[1], mdef)
                    for namespace, namespace_methods in methods.items():
                        interface_methods = {}
                        for method in namespace_methods:
                            if method not in mdef['methods'] and method not in indexes:
                                indexes.append(method)
                                self.list_methods.append([method, namespace])
                                interface_methods[method] = namespace_methods[method]
                        if len(interface_methods) > 0:
                            self.pending[namespace] = interface_methods
                    break
