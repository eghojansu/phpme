import sublime
import sublime_plugin
import os
from ..helper import Helper
from ..utils import Utils
from ..constant import Constant
from ..parser.class_parser import ClassParser


class PhpmeGetterSetterCommand(sublime_plugin.TextCommand):
    """Generate getter and setter"""

    def run(self, edit, mode):
        self.properties = []
        self.pending = []
        self.list_properties = []
        self.collect_progress = 0
        self.mode = mode
        self.helper = Helper(self.view)

        if self.helper.not_scope():
            self.helper.e_scope()
        else:
            mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
            if self.helper.not_class(mdef, ['class']):
                self.helper.e_class()
            else:
                self.find_variables(mdef, mode)
                self.run_schedule()

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_properties) > 0:
                options = [
                    ['Generate All', 'generate all properties'],
                    ['Generate Some', 'pick multiple properties one by one']
                ]
                self.view.window().show_quick_panel(options+self.list_properties, self.on_method_selected)
            else:
                self.properties = self.pending
                self.collect_progress = 2
                self.run_schedule()
        elif self.collect_progress == 1:
            # ask again
            options = [['Done', 'done selecting property']]
            self.view.window().show_quick_panel(options+self.list_properties, self.on_method_selected)
        elif len(self.properties) > 0:
            self.view.run_command('phpme_post_getter_setter', {
                'properties': self.properties,
                'mode': self.mode
            })
        else:
            self.helper.print_message('No method to generate')

    def pick_property(self, index):
        self.properties.append(self.pending[index])
        del self.pending[index]
        del self.list_properties[index]

    def on_method_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    self.properties = self.pending
                    self.collect_progress = 2
                elif index == 1:
                    self.collect_progress = 1
                else:
                    self.pick_property(index - 2)
                    self.collect_progress = 2
            elif self.collect_progress == 1:
                if index == 0:
                    self.collect_progress = 2
                else:
                    self.pick_property(index - 1)
                    if len(self.pending) == 0:
                        self.collect_progress = 2
        else:
            self.collect_progress = 2
            self.properties.clear()

        self.run_schedule()

    def find_variables(self, mdef, mode):
        for pdef in mdef['properties']:
            name = Utils.ucfirst(pdef['name'])
            getter_method = 'get{}'.format(name)
            setter_method = 'set{}'.format(name)
            var = '$' + pdef['name']

            if (((mode & Constant.gen_getter) and (getter_method not in mdef['methods']))
                or ((mode & Constant.gen_setter) and (setter_method not in mdef['methods']))):
                self.list_properties.append([var, pdef['hint'] if pdef['hint'] else 'mixed'])
                pdef['uses'] = self.helper.decide_uses(pdef['uses'], mdef['uses'])
                self.pending.append(pdef)
