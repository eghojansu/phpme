import sublime_plugin
import re
from ..helper import Helper
from ..constant import Constant
from ..utils import Utils
from ..binx.console import Console
from ..parser.class_parser import ClassParser


class PhpmeCopyMethodCommand(sublime_plugin.TextCommand):
    """Copy method from selected class (method definition only)"""

    def run(self, edit):
        self.pending = {}
        self.classes = []
        self.notfound = []
        self.invalid = []
        self.methods = {}
        self.pending_methods = {}
        self.list_methods = []
        self.method_collected = False
        self.collect_progress = 0
        self.helper  = Helper(self.view)

        if self.helper.not_scope():
            self.helper.e_scope()
        else:
            mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
            if self.helper.not_class(mdef, ['class']):
                self.helper.e_class()
            else:
                self.find_selected_symbols()
                self.run_schedule()

                if len(self.notfound) > 0:
                    self.helper.print_message('Symbol not found: "{}"'.format('", "'.join(self.notfound)))

                if len(self.invalid) > 0:
                    self.helper.print_message('Not a valid symbol: "{}"'.format(self.invalid))

    def run_schedule(self):
        self.scheduled = None
        if len(self.pending) > 0:
            self.scheduled = self.pending.popitem()
            self.view.window().show_quick_panel(self.scheduled[1], self.on_symbol_selected)
        else:
            if not self.method_collected:
                self.collect_methods()
            self.run_method_schedule()

    def on_symbol_selected(self, index):
        if index > -1:
            namespace = self.scheduled[1][index]
            self.classes.append(namespace)
            self.run_schedule()

    def run_method_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_methods) > 0:
                options = [
                    ['Pick All', 'pick all method {}'.format(Utils.method_info(len(self.list_methods)))],
                    ['Pick Some', 'pick multiple method one by one']
                ]
                self.view.window().show_quick_panel(options+self.list_methods, self.on_method_selected)
            else:
                self.methods = self.pending_methods
                self.collect_progress = 2
                self.run_method_schedule()
        elif self.collect_progress == 1:
            # ask again
            options = [['Done', 'done selecting method']]
            self.view.window().show_quick_panel(options+self.list_methods, self.on_method_selected)
        elif len(self.methods) > 0:
            self.view.run_command('phpme_do_generate_method', {'methods': self.methods, 'job': 'copy'})
        else:
            self.helper.print_message('No method to generate')

    def pick_method(self, index):
        method = self.list_methods[index][0]
        namespace = self.list_methods[index][1]
        found = Utils.find(self.pending_methods[namespace], 'name', method)
        if found:
            if namespace not in self.methods:
                self.methods[namespace] = []
            self.methods[namespace].append(found)
            del self.list_methods[index]

    def on_method_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    self.methods = self.pending_methods
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

        self.run_method_schedule()

    def find_selected_symbols(self):
        for region in self.view.sel():
            keyword = self.view.substr(self.view.word(region))
            if re.match(r"\w+", keyword):
                namespaces = self.helper.find_symbol(keyword, in_globals = False)
                nlen = len(namespaces)
                if nlen == 0:
                    self.notfound.append(keyword)
                elif nlen == 1:
                    self.classes.append(namespaces[0])
                else:
                    namespaces.sort(key = lambda i: len(i[0]))
                    self.pending[keyword] = namespaces
            else:
                self.invalid.append(keyword)

    def collect_methods(self):
        mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
        indexes = []

        for namespace in self.classes:
            mmdef = ClassParser.create(None, namespace[1]).parse()
            proposed_methods = []
            for method in mmdef['methods']:
                found = Utils.find(mdef['methods'], 'name', method['name'])
                if not found and method['name'] not in indexes and not method['abstract']:
                    method['uses'] = self.helper.decide_class_uses(method['uses'], mmdef, mdef)
                    indexes.append(method['name'])
                    self.list_methods.append([method['name'], namespace[0]])
                    proposed_methods.append(method)
            if len(proposed_methods) > 0:
                self.pending_methods[namespace[0]] = proposed_methods;

        self.method_collected = True
        self.classes = None
