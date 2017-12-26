import sublime_plugin
import os
import re
from ..constant import Constant
from ..helper import Helper
from ..utils import Utils
from ..parser.class_parser import ClassParser


class PhpmeGenerateTestMethodCommand(sublime_plugin.TextCommand):
    """Generate test method"""

    def run(self, edit):
        self.pending = []
        self.classes = []
        self.methods = {}
        self.pending_methods = {}
        self.list_methods = []
        self.method_collected = False
        self.collect_progress = 0
        self.invalid = True
        self.class_name = None
        self.helper  = Helper(self.view)
        self.generate_content = self.helper.setting_get('test_generate_content', True)

        if self.helper.not_scope():
            self.helper.e_scope()
        else:
            mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
            if self.helper.not_class(mdef, ['class']):
                self.helper.e_class()
            else:
                pattern = self.helper.setting_get('test_case_pattern', r'^(\w+)Test$')
                pre = re.compile(pattern)
                match = pre.search(mdef['name'])

                if match and len(match.groups()) > 0 and match.group(1):
                    self.class_name = match.group(1)
                    self.find_class()

                    if self.invalid:
                        self.helper.print_message('Symbol not found: "{}"'.format(self.class_name))
                    else:
                        self.run_schedule()
                else:
                    self.helper.print_message('Current class is not valid TestCase: "{}"'.format(mdef['name']))

    def run_schedule(self):
        if len(self.pending) > 0:
            self.view.window().show_quick_panel(self.pending, self.on_symbol_selected)
        else:
            if not self.method_collected:
                self.collect_methods()
            self.run_method_schedule()

    def on_symbol_selected(self, index):
        if index > -1:
            self.classes.append(self.pending[index])
            self.pending = []
            self.run_schedule()

    def run_method_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_methods) > 0:
                options = [
                    ['Pick All', 'pick all method'],
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
            self.view.run_command('phpme_post_generate_method', {'methods': self.methods})
        else:
            self.helper.print_message('No method to generate')

    def pick_method(self, index):
        method = self.list_methods[index][0]
        namespace = self.list_methods[index][1]
        found = Utils.find(self.pending_methods[namespace], 'name', method)
        if found:
            if namespace not in self.methods:
                self.methods[namespace] = []

            new_def = found['def']
            new_def = re.sub(r'static\s+', '', new_def)
            new_def = re.sub(r'(private|protected)\s+', 'public ', new_def)
            new_def = re.sub(found['name'] + r'\s*\(', found['test_name'] + '(', new_def)

            pdef = re.search(r'\((.*?)\)', new_def)
            if pdef.group(1):
                new_def = pdef.re.sub('()', pdef.string)

            if self.generate_content:
                if found['static']:
                    caller = '{}::'.format(self.class_name)
                else:
                    caller = '$this->{}->'.format(Utils.lcfirst(self.class_name))

                args = re.findall('\$\w+', pdef.group(1)) if pdef.group(1) else []
                args_str = ' = null, '.join(args)
                if args:
                    args_str += ' = null'

                found['content'] = [
                    '\t$expected = "you";',
                    '\t$result = {}{}({});'.format(caller, found['name'], args_str),
                    '\t$this->assertEquals($expected, $result);'
                ]

            found['name'] = found['test_name']
            found['def'] = new_def
            self.methods[namespace].append(found)
            del self.list_methods[index]

    def on_method_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    for i in range(len(self.list_methods)):
                        self.pick_method(0)
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

    def find_class(self):
        namespaces = self.helper.find_symbol(self.class_name, in_globals = False)
        nlen = len(namespaces)
        self.invalid = nlen == 0
        if nlen == 1:
            self.classes.append(namespaces[0])
        else:
            self.pending = sorted(namespaces, key = lambda i: len(i[0]))

    def collect_methods(self):
        mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
        indexes = []
        public_only = self.helper.setting_get('test_public_only', True)

        for namespace in self.classes:
            mmdef = ClassParser.create(None, namespace[1]).parse()
            proposed_methods = []
            for method in mmdef['methods']:
                test_name = 'test{}'.format(Utils.ucfirst(method['name']))
                found = Utils.find(mdef['methods'], 'name', test_name)
                if not found and method['name'] not in Constant.magic_methods and test_name not in indexes and not method['abstract'] and (not public_only or method['visibility'] == 'public'):
                    method['test_name'] = test_name
                    method['uses'] = self.helper.decide_class_uses(method['uses'], mmdef, mdef)
                    indexes.append(method['name'])
                    self.list_methods.append([method['name'], namespace[0]])
                    proposed_methods.append(method)
            if len(proposed_methods) > 0:
                self.pending_methods[namespace[0]] = proposed_methods;

        self.method_collected = True
        self.classes = None
