import sublime_plugin
import os
from ..helper import Helper
from ..utils import Utils
from ..parser.class_parser import ClassParser


class PhpmeOverrideMethodCommand(sublime_plugin.TextCommand):
    """Override method"""

    def run(self, edit, abstract_only = False):
        self.methods = {}
        self.pending = {}
        self.list_methods = []
        self.collect_progress = 0
        self.abstract_only = abstract_only
        self.helper = Helper(self.view)

        if self.helper.not_scope():
            self.helper.e_scope()
        else:
            mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
            if self.helper.not_class(mdef, ['class']):
                self.helper.e_class()
            elif not mdef['parent']:
                self.helper.print_message('Class have no parent')
            else:
                self.find_methods(mdef)
                self.run_schedule()

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_methods) > 0:
                options = []
                if self.abstract_only:
                    options.append(['Override All', 'override all methods'])
                options.append(['Override Some', 'pick multiple method one by one'])
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
            self.view.run_command('phpme_post_override_method', {'methods': self.methods})
        else:
            self.helper.print_message('No method to override')

    def pick_method(self, index):
        method = self.list_methods[index][0]
        namespace = self.list_methods[index][1]
        found = Utils.find(self.pending[namespace], 'name', method)
        if found:
            if namespace not in self.methods:
                self.methods[namespace] = []
            self.methods[namespace].append(found)
            del self.list_methods[index]

    def on_method_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if self.abstract_only:
                    if index == 0:
                        self.methods = self.pending
                        self.collect_progress = 2
                    elif index == 1:
                        self.collect_progress = 1
                    else:
                        self.pick_method(index - 2)
                        self.collect_progress = 2
                else:
                    if index == 0:
                        self.collect_progress = 1
                    else:
                        self.pick_method(index - 1)
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
        use = self.helper.decide_use(mdef['parent']['as'], mdef['parent']['ns'], mdef['namespace'], mdef['uses'])
        symbol = use.split('\\')[-1]
        for namespaces in self.helper.find_symbol(symbol, use):
            if namespaces[0] == use:
                methods = self.helper.parse_class_tree(None, namespaces[0], namespaces[1], mdef)
                for namespace in sorted(list(methods.keys())):
                    namespace_methods = methods[namespace]
                    parent_methods = []
                    for method in namespace_methods:
                        found = Utils.find(mdef['methods'], 'name', method['name'])
                        if not found and method['name'] not in indexes and (not self.abstract_only or method['abstract']):
                            indexes.append(method['name'])
                            self.list_methods.append([method['name'], namespace])
                            parent_methods.append(method)
                    if len(parent_methods) > 0:
                        self.pending[namespace] = parent_methods
                break
