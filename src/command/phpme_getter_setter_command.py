import sublime, sublime_plugin
from ..phpme_command import PhpmeCommand
from ..parser.class_parser import ClassParser


class PhpmeGetterSetterCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Generate getter and setter"""

    def run(self, edit, mode):
        self.methods = {}
        self.selected_methods = {}
        self.list_properties = []
        self.fqcn = None
        self.collect_progress = 0
        self.mode = mode
        self.mode_getter = 1
        self.mode_setter = 2
        self.mode_all = self.mode_getter | self.mode_setter

        if self.in_php_scope() and self.find_variables():
            self.run_schedule()

    def has_method(self):
        return len(self.selected_methods) > 0

    def run_schedule(self):
        if self.collect_progress == 0:
            if len(self.list_properties) > 0:
                options = [
                    ['Generate All', 'generate all methods'],
                    ['Generate Some', 'pick multiple method one by one']
                ]
                self.view.window().show_quick_panel(options+self.list_properties, self.on_method_selected)
            else:
                self.selected_methods = self.methods
                self.collect_progress = 2
                self.run_schedule()
        elif self.collect_progress == 1:
            # ask again
            options = [['Done', 'done selecting method']]
            self.view.window().show_quick_panel(options+self.list_properties, self.on_method_selected)
        elif self.has_method():
            self.view.run_command('phpme_post_getter_setter', {'methods': self.selected_methods, 'fqcn': self.fqcn})
        else:
            self.print_message('No method to generate')

    def no_property_to_select(self):
        return len(self.list_properties) == 0

    def pick_property(self, index):
        prop = self.list_properties[index][0][1:]

        if self.mode_getter & self.mode:
            method = 'get{}'.format(prop.capitalize())
            self.selected_methods[method] = self.methods[method]

        if self.mode_setter & self.mode:
            method = 'set{}'.format(prop.capitalize())
            self.selected_methods[method] = self.methods[method]

        del self.list_properties[index]

    def on_method_selected(self, index):
        if index > -1:
            if self.collect_progress == 0:
                if index == 0:
                    self.selected_methods = self.methods
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
        self.static_property = self.get_setting('static_property', 'static')
        self.setter_chainable = self.get_setting('setter_chainable', True)
        self.generate_docblock = self.get_setting('generate_docblock', False)
        for prop, pdef in mdef['properties'].items():
            getter_method = 'get{}'.format(prop.capitalize())
            setter_method = 'set{}'.format(prop.capitalize())

            if (self.mode_getter & self.mode) and getter_method not in mdef['methods']:
                self.generate_getter(getter_method, prop, pdef)

            if self.mode_setter & self.mode and setter_method not in mdef['methods']:
                self.generate_setter(setter_method, prop, pdef)

            if self.mode == self.mode_getter:
                if getter_method in self.methods:
                    self.list_properties.append(['${}'.format(prop), 'Getter for ${}'.format(prop)])
            elif self.mode == self.mode_setter:
                if setter_method in self.methods:
                    self.list_properties.append(['${}'.format(prop), 'Setter for ${}'.format(prop)])
            elif self.mode == self.mode_all:
                if getter_method in self.methods or setter_method in self.methods:
                    self.list_properties.append(['${}'.format(prop), 'Getter and Setter for ${}'.format(prop)])

        return True

    def generate_getter(self, method, prop, pdef):
        if pdef['static']:
            line = 'public static function {}()'.format(method)
            content = ['\treturn {}::${};'.format(self.static_property, prop)]
        else:
            line = 'public function {}()'.format(method)
            content = ['\treturn $this->{};'.format(prop)]

        docblocks = None
        if self.generate_docblock:
            docblocks = '\n\t'.join([
                '/**',
                ' * Get {}'.format(prop),
                ' *',
                ' * @return {}'.format(pdef['hint'] if pdef['hint'] else 'mixed'),
                ' */'
            ])

        self.methods[method] = {
            'docblocks': docblocks,
            'uses': {},
            'def': line,
            'content': content,
            'force_docblock': True
        }

    def generate_setter(self, method, prop, pdef):
        args = ' '.join([
            pdef['hint'] if pdef['hint'] else '',
            '${}'.format(prop)
        ]).strip()

        if pdef['static']:
            line = 'public static function {}({})'.format(method, args)
            content = ['\t{0}::${1} = ${1};'.format(self.static_property, prop)]
        else:
            line = 'public function {}({})'.format(method, args)
            content = ['\t$this->{0} = ${0};'.format(prop)]
            if self.setter_chainable:
                content.append('')
                content.append('\treturn $this;')

        docblocks = None
        if self.generate_docblock:
            x = [
                '/**',
                ' * Set {}'.format(prop),
                ' *',
                ' * @param {} ${}'.format(pdef['hint'] if pdef['hint'] else 'mixed', prop)
            ]
            if self.setter_chainable and not pdef['static']:
                x += [' * @return $this']
            else:
                x += [' * @return void']
            x += [' */']
            docblocks = '\n\t'.join(x)

        self.methods[method] = {
            'docblocks': docblocks,
            'uses': pdef['uses'],
            'def': line,
            'content': content,
            'force_docblock': True
        }
