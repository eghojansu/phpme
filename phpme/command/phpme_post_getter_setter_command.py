import sublime_plugin
from ..helper import Helper
from ..utils import Utils
from ..constant import Constant


class PhpmePostGetterSetterCommand(sublime_plugin.TextCommand):
    """Do generate getter setter"""

    def run(self, edit, mode, properties, cname):
        self.uses = []
        self.methods = []
        self.cname = cname;
        self.helper = Helper(self.view)

        prefixes = []
        if mode & Constant.gen_getter:
            prefixes.append('Getter')
        if mode & Constant.gen_setter:
            prefixes.append('Setter')
        title = ' and '.join(prefixes)

        self.prepare(mode, properties)

        # insert uses
        self.view.run_command('phpme_post_use_class', {'namespaces': self.uses})

        self.view.insert(edit, self.view.sel()[0].end(), '\n\n\t'.join(self.methods))
        self.helper.print_message('Successfully generate properties {}'.format(title))

    def prepare(self, mode, properties):
        option = {
            'generate_docblock': self.helper.setting_get('generate_docblock', False),
            'hint_default_null': self.helper.setting_get('hint_default_null', False),
            'allow_native_hint': self.helper.setting_get('native_hint', False),
            'static_property': self.helper.setting_get('static_property', 'static'),
            'setter_chainable': self.helper.setting_get('setter_chainable', True)
        }

        for pdef in properties:
            if mode & Constant.gen_getter:
                self.methods.append(self.generate_getter(pdef, option))
            if mode & Constant.gen_setter:
                self.methods.append(self.generate_setter(pdef, option))

    def generate_getter(self, pdef, option):
        prop = pdef['name']
        method = 'get{}'.format(Utils.ucfirst(prop))
        if pdef['static']:
            line = 'public static function {}()'.format(method)
            content = ['\treturn {}::${};'.format(option['static_property'], prop)]
        else:
            line = 'public function {}()'.format(method)
            content = ['\treturn $this->{};'.format(prop)]

        hint = self.helper.decide_hint(pdef['hint'], option['allow_native_hint'])
        if hint[0]:
            line += ': ' + hint[0]

        docblocks = None
        if option['generate_docblock']:
            docblocks = '\n\t'.join([
                '/**',
                ' * Get {}.'.format(prop),
                ' *',
                ' * @return {}'.format(pdef['hint'] if pdef['hint'] else 'mixed'),
                ' */'
            ])

        return self.helper.create_method_stub({
            'docblocks': docblocks,
            'def': line,
            'content': content,
            'force_docblock': True
        })

    def generate_setter(self, pdef, option):
        prop = pdef['name']
        method = 'set{}'.format(Utils.ucfirst(prop))

        hint = self.helper.decide_hint(pdef['hint'], option['allow_native_hint'])
        default = ' = null' if hint[0] and option['hint_default_null'] else ''

        args = (hint[0] + ' ' + '$' + prop + default).strip()
        if pdef['static']:
            line = 'public static function {}({})'.format(method, args)
            content = ['\t{0}::${1} = ${1};'.format(option['static_property'], prop)]
        else:
            line = 'public function {}({})'.format(method, args)
            content = ['\t$this->{0} = ${0};'.format(prop)]
            if option['setter_chainable']:
                content.append('')
                content.append('\treturn $this;')

                if option['allow_native_hint']:
                    line += ': ' + self.cname
        self.uses += pdef['uses']

        docblocks = None
        if option['generate_docblock']:
            docblocks = [
                '/**',
                ' * Set {}.'.format(prop),
                ' *',
                ' * @param {} ${}'.format(hint[1], prop)
            ]
            if option['setter_chainable'] and not pdef['static']:
                docblocks += [' *', ' * @return ' + self.cname]
            docblocks += [' */']
            docblocks = '\n\t'.join(docblocks)

        return self.helper.create_method_stub({
            'docblocks': docblocks,
            'def': line,
            'content': content,
            'force_docblock': True
        })
