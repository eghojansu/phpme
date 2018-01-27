import sublime_plugin
from ..helper import Helper


class PhpmeDoGenerateMethodCommand(sublime_plugin.TextCommand):
    """Do generate methods"""

    def run(self, edit, methods, job = 'generate'):
        helper = Helper(self.view)

        arranged = helper.arrange_methods(methods)

        # insert uses
        self.view.run_command('phpme_post_use_class', {'namespaces': arranged['uses']})

        self.view.insert(edit, self.view.sel()[0].end(), '\n\n\t'.join(arranged['methods']))
        helper.print_message('Successfully ' + job + ': ' + (', '.join(arranged['arranged'])))

