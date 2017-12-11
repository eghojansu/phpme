import sublime, sublime_plugin
import re
from ..phpme_command import PhpmeCommand


class PhpmePostImplementsCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Implements selection"""

    def run(self, edit, methods):
        arranged = self.arrange_methods(methods)

        # insert uses
        self.view.run_command('phpme_post_use_class', {'namespaces': arranged['uses']})

        # Find the closing brackets. We'll place the method
        # stubs just before the last closing bracket.
        closing_brackets = self.view.find_all('}')

        # Add the method stub(s) to the current file
        region = closing_brackets[-1]
        point = region.end() - 1

        self.view.insert(edit, point, '\n\t' + ('\n\n\t'.join(arranged['methods']))+'\n')
        self.print_message('Successfully implements: {}'.format(', '.join(arranged['overriden'])))
