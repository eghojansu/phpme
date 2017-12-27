import sublime_plugin
from ..helper import Helper


class PhpmeDoGenerateMethodCommand(sublime_plugin.TextCommand):
    """Do generate methods"""

    def run(self, edit, methods, job = 'generate'):
        helper = Helper(self.view)

        arranged = helper.arrange_methods(methods)

        # insert uses
        self.view.run_command('phpme_post_use_class', {'namespaces': arranged['uses']})

        # Find the closing brackets. We'll place the method
        # stubs just before the last closing bracket.
        closing_brackets = self.view.find_all('}')
        region = closing_brackets[-1]
        point = region.end() - 1

        self.view.insert(edit, point, '\n\t' + ('\n\n\t'.join(arranged['methods']))+'\n')
        helper.print_message('Successfully ' + job + ': ' + (', '.join(arranged['arranged'])))
