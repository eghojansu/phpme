import sublime_plugin
from ..helper import Helper


class PhpmePostExpandFqcnCommand(sublime_plugin.TextCommand):
    def run(self, edit, symbols):
        helper = Helper(self.view)

        if len(symbols) > 0:
            expanded = []
            failed = []
            for region in self.view.sel():
                word_region = self.view.word(region)
                symbol = self.view.substr(word_region)
                if symbol in symbols:
                    self.view.replace(edit, word_region, symbols[symbol])
                    expanded.append(symbol)
                else:
                    failed.append(symbol)

            if len(expanded) > 0:
                helper.print_message('Successfully expands: "{}"'.format('", "'.join(expanded)))
            if len(failed) > 0:
                helper.print_message('Failed expands: "{}"'.format('", "'.join(failed)))
