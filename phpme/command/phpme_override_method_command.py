import sublime, sublime_plugin
import os
from ..phpme_command import PhpmeCommand
from ..parser.class_parser import ClassParser
from ..binx.console import Console


class PhpmeOverrideMethodCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Override method"""

    def run(self, edit):
        self.methods = {}
        self.selected_methods = {}
        self.list_methods = []
        self.collect_progress = 0

        if self.in_php_scope() and self.build_definition():
            self.run_schedule()

    def has_method(self):
        return len(self.selected_methods) > 0

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_methods) > 0:
                options = [
                    ['Override All', 'override all methods'],
                    ['Override Some', 'pick multiple method one by one']
                ]
                self.view.window().show_quick_panel(options+self.list_methods, self.on_method_selected)
            else:
                self.selected_methods = self.methods
                self.collect_progress = 2
                self.run_schedule()
        elif self.collect_progress == 1:
            # ask again
            options = [['Done', 'done selecting method']]
            self.view.window().show_quick_panel(options+self.list_methods, self.on_method_selected)
        elif self.has_method():
            self.view.run_command('phpme_post_override_method', {'methods': self.selected_methods})
        else:
            self.print_message('No method to override')

    def no_method_to_select(self):
        return len(self.list_methods) == 0

    def pick_method(self, index):
        method = self.list_methods[index][0]
        namespace = self.list_methods[index][1]
        if not namespace in self.selected_methods:
            self.selected_methods[namespace] = {}
        self.selected_methods[namespace][method] = self.methods[namespace][method]
        del self.list_methods[index]

    def on_method_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    self.selected_methods = self.methods
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
        else:
            self.list_methods = []

        if self.no_method_to_select():
            self.collect_progress = 2
        self.run_schedule()

    def build_definition(self):
        region = sublime.Region(0, self.view.size())
        content = self.view.substr(region)
        if len(content) == 0:
            self.print_message('File has no content')
            return

        # current view content
        file = os.path.abspath(self.view.file_name())
        mdef = ClassParser.create(content, file).parse()
        if not self.in_class_scope(mdef):
            return

        if mdef['is_interface'] or mdef['is_trait']:
            self.print_message('Cannot override method in {} context'.format(mdef['type']))
            return

        if not mdef['parent']:
            self.print_message('Class have no parent')
            return

        parent = mdef['parent']['alias'].split('\\')[-1]
        parent_namespace = mdef['parent']['namespace'] if mdef['parent']['namespace'] else mdef['parent']['alias']
        for namespace in self.find_symbol(parent):
            if namespace[0] == parent_namespace:
                methods = self.parse_class_tree(None, namespace[0], namespace[1])
                for namespace, namespace_methods in methods.items():
                    self.methods[namespace] = {}
                    for method in namespace_methods:
                        if not method in mdef['methods']:
                            self.list_methods.append([method, namespace])
                            self.methods[namespace][method] = namespace_methods[method]
                    if len(self.methods[namespace]) == 0:
                        del self.methods[namespace]
                break

        return True
