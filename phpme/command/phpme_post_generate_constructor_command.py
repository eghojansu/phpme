import sublime_plugin
from ..helper import Helper


class PhpmePostGenerateConstructorCommand(sublime_plugin.TextCommand):
    """Do generate constructor"""

    def run(self, edit, properties):
        self.uses = []
        self.method = None
        self.helper = Helper(self.view)

        self.prepare(properties)

        # insert uses
        self.view.run_command('phpme_post_use_class', {'namespaces': self.uses})

        self.view.insert(edit, self.view.sel()[0].end(), self.method)
        self.helper.print_message('Successfully generate constructor method')

    def prepare(self, properties):
        generate_docblock = self.helper.setting_get('generate_docblock', False)
        hint_default_null = self.helper.setting_get('hint_default_null', False)
        allow_native_hint = self.helper.setting_get('native_hint', False)

        args = []
        content = []
        docblocks = [
            '/**',
            ' * Class constructor',
            ' *',
        ]
        for pdef in properties:
            hint = self.helper.decide_hint(pdef['hint'], allow_native_hint)
            default = ' = null' if hint[0] and hint_default_null else ''

            args.append((hint[0] + ' ' + '$' + pdef['name'] + default).strip())
            content.append('\t$this->{0} = ${0};'.format(pdef['name']))
            docblocks.append(' * @param {} ${}'.format(hint[1], pdef['name']))
            self.uses += pdef['uses']
        docblocks += [' */']

        if generate_docblock:
            docblocks = '\n\t'.join(docblocks)
        else:
            docblocks = None

        self.method = self.helper.create_method_stub({
            'docblocks': docblocks,
            'content': content,
            'def': 'public function __construct({})'.format(', '.join(args)),
            'force_docblock': True
        })
