import sublime, sublime_plugin
import re, os
from ..phpme_command import PhpmeCommand
from ..parser.class_parser import ClassParser
from ..utils import Utils
from ..binx.console import Console


class PhpmeImplementsCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Implements interface"""

    def run(self, edit):
        self.methods = {}
        self.selected_methods = {}
        self.list_methods = []
        self.collect_progress = 0

        if self.in_php_scope() and self.find_interfaces():
            self.run_schedule()

    def has_method(self):
        return len(self.selected_methods) > 0

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_methods) > 0:
                options = [
                    ['Implement All', 'implement all methods'],
                    ['Implement Some', 'pick multiple method one by one']
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
            self.view.run_command('phpme_post_implements', {'methods': self.selected_methods})
        else:
            self.print_message('No method to implements')

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

    def find_interfaces(self):
        all_region = sublime.Region(0, self.view.size())
        content = self.view.substr(all_region)

        if len(content) == 0:
            sublime.status_message('File has no content')
            return

        # current view content
        file = os.path.abspath(self.view.file_name())
        mdef = ClassParser.create(content, file).parse()
        if not self.in_class_scope(mdef):
            return

        if mdef['is_interface'] or mdef['is_trait']:
            self.print_message('Cannot implements method in {} context'.format(mdef['type']))
            return

        if len(mdef['implements']) == 0:
            self.print_message('Class was not implements any interface')
            return

        for alias, namespace in mdef['implements'].items():
            interface = alias.split('\\')[-1]
            interface_namespace = namespace if namespace else alias
            for namespaces in self.find_symbol(interface):
                if namespaces[0] == interface_namespace:
                    methods = self.parse_class_tree(None, namespaces[0], namespaces[1])
                    for namespace, namespace_methods in methods.items():
                        self.methods[namespace] = {}
                        for method in namespace_methods:
                            if not method in mdef['methods']:
                                self.list_methods.append([method, namespace])
                                self.methods[namespace][method] = namespace_methods[method]
                        if len(self.methods[namespace]) == 0:
                            del self.methods[namespace]
                    break
            else:
                self.print_message('Interface not found: {}'.format(interface_namespace))

        return True
