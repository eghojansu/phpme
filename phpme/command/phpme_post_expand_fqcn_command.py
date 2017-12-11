import sublime_plugin
from ..phpme_command import PhpmeCommand


class PhpmePostExpandFqcnCommand(sublime_plugin.TextCommand, PhpmeCommand):
    def run(self, edit, symbols):
        if len(symbols) > 0:
            expanded = []
            failed = []
            for region in self.view.sel():
                word_region = self.view.word(region)
                symbol = self.view.substr(word_region)
                if symbol in symbols:
                    namespace = symbols[symbol][0]
                    self.view.replace(edit, word_region, namespace)
                    expanded.append(symbol)
                else:
                    failed.append(symbol)

            if len(expanded) > 0:
                self.print_message('Successfully expands: "{}"'.format('", "'.join(expanded)))
            if len(failed) > 0:
                self.print_message('Failed expands: "{}"'.format('", "'.join(failed)))
