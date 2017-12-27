import sublime
import sublime_plugin
from ..helper import Helper
from ..utils import Utils
from ..parser.class_parser import ClassParser


class PhpmeGenerateConstructorCommand(sublime_plugin.TextCommand):
    """Generate constructor"""

    def run(self, edit):
        self.properties = []
        self.pending = []
        self.list_properties = []
        self.collect_progress = 0
        self.helper = Helper(self.view)

        if self.helper.not_scope():
            self.helper.e_scope()
        else:
            mdef = ClassParser.create(self.helper.content(), self.helper.filename).parse()
            if self.helper.not_class(mdef, ['class']):
                self.helper.e_class()
            else:
                self.find_variables(mdef)
                self.run_schedule()

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_properties) > 0:
                options = [
                    ['Pick All', 'pick all properties {}'.format(Utils.property_info(len(self.list_properties)))],
                    ['Pick Some', 'pick multiple properties one by one'],
                    ['Pick None', 'pick no property']
                ]
                self.view.window().show_quick_panel(options+self.list_properties, self.on_property_selected)
            else:
                self.properties = self.pending
                self.collect_progress = 2
                self.run_schedule()
        elif self.collect_progress == 1:
            # ask again
            options = [['Done', 'done selecting property']]
            self.view.window().show_quick_panel(options+self.list_properties, self.on_property_selected)
        elif self.collect_progress == 2:
            self.view.run_command('phpme_post_generate_constructor', {'properties': self.properties})
        else:
            self.helper.print_message('Cancel constructor generation')

    def pick_property(self, index):
        self.properties.append(self.pending[index])
        del self.pending[index]
        del self.list_properties[index]

    def on_property_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    self.properties = self.pending
                    self.collect_progress = 2
                elif index == 1:
                    self.collect_progress = 1
                elif index == 2:
                    self.collect_progress = 2
                    self.properties.clear()
                else:
                    self.pick_property(index - 3)
                    self.collect_progress = 2
            elif self.collect_progress == 1:
                if index == 0:
                    self.collect_progress = 2
                else:
                    self.pick_property(index - 1)
                    if len(self.pending) == 0:
                        self.collect_progress = 2
        else:
            self.collect_progress = 3

        self.run_schedule()

    def find_variables(self, mdef):
        for pdef in mdef['properties']:
            if not pdef['static']:
                self.list_properties.append([
                    '${}'.format(pdef['name']),
                    pdef['hint'] if pdef['hint'] else 'mixed'
                ])
                pdef['uses'] = self.helper.decide_uses(pdef['uses'], mdef['uses'])
                self.pending.append(pdef)
