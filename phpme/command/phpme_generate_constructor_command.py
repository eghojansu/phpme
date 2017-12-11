import sublime, sublime_plugin
from ..phpme_command import PhpmeCommand
from ..parser.class_parser import ClassParser


class PhpmeGenerateConstructorCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Generate constructor"""

    def run(self, edit):
        self.properties = {}
        self.selected_properties = {}
        self.list_properties = []
        self.fqcn = None
        self.collect_progress = 0

        if self.in_php_scope() and self.find_variables():
            self.run_schedule()

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_properties) > 0:
                options = [
                    ['Pick All', 'pick all properties'],
                    ['Pick Some', 'pick multiple properties one by one']
                ]
                self.view.window().show_quick_panel(options+self.list_properties, self.op_property_selected)
            else:
                self.selected_properties = self.properties
                self.collect_progress = 2
                self.run_schedule()
        elif self.collect_progress == 1:
            # ask again
            options = [['Done', 'done selecting property']]
            self.view.window().show_quick_panel(options+self.list_properties, self.op_property_selected)
        else:
            self.view.run_command('phpme_post_generate_constructor', {'methods': self.generate_method(), 'fqcn': self.fqcn})

    def no_property_to_select(self):
        return len(self.list_properties) == 0

    def pick_property(self, index):
        prop = self.list_properties[index][0][1:]
        self.selected_properties[prop] = self.properties[prop]
        del self.list_properties[index]

    def op_property_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    self.selected_properties = self.properties
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
        else:
            self.list_properties = []

        if self.no_property_to_select():
            self.collect_progress = 2
        self.run_schedule()

    def find_variables(self):
        region = sublime.Region(0, self.view.size())
        content = self.view.substr(region)
        if len(content) == 0:
            sublime.status_message('File has no content')
            return

        mdef = ClassParser.create(content).parse()
        if not self.in_class_scope(mdef):
            return

        self.fqcn = mdef['fqcn']
        self.generate_docblock = self.get_setting('generate_docblock', False)
        self.properties = mdef['properties']
        for prop, pdef in mdef['properties'].items():
            self.list_properties.append(['${}'.format(prop), pdef['hint'] if pdef['hint'] else 'mixed'])

        return True

    def generate_method(self):
        method = '__construct'
        args = []
        content = []
        docblocks = [
            '/**',
            ' * Class constructor',
            ' *',
        ]
        uses = {}
        for prop, pdef in self.selected_properties.items():
            args += [' '.join([
                pdef['hint'] if pdef['hint'] else '',
                '${}'.format(prop)
            ]).strip()]
            content += ['\t$this->{0} = ${0};'.format(prop)]
            docblocks += [' * @param {} ${}'.format(pdef['hint'] if pdef['hint'] else 'mixed', prop)]
            uses.update(pdef['uses'])
        docblocks += [' */']

        if self.generate_docblock:
            docblocks = '\n\t'.join(docblocks)
        else:
            docblocks = None

        return {method: {
            'docblocks': docblocks,
            'uses': uses,
            'def': 'public function {}({})'.format(method, ', '.join(args)),
            'content': content,
            'force_docblock': True
        }}
