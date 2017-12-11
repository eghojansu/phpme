import sublime_plugin
import re
from ..phpme_command import PhpmeCommand


class PhpmeExpandFqcnCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Expand classes to fqcn"""

    def run(self, edit):
        self.pending = {}
        self.regions = {}
        self.symbols = {}

        if self.in_php_scope() and self.find_selected_symbol():
            notfound = []
            for symbol in list(self.symbols.keys()):
                namespaces = self.symbols[symbol]
                nlen = len(namespaces)
                if nlen == 1:
                    continue
                if nlen == 0:
                    notfound.append(symbol)
                else:
                    self.pending[symbol] = namespaces
                del self.symbols[symbol]

            self.run_schedule()
            if len(notfound) > 0:
                self.print_message('Symbol not found: "{}"'.format('", "'.join(notfound)))

    def has_schedule(self):
        return len(self.pending) > 0

    def has_content(self):
        return len(self.symbols) > 0

    def prepare_symbols(self):
        prepared_symbols = {}
        prefix = '\\' if self.get_setting('prefix_fqcn', True) else ''
        for symbol, namespaces in self.symbols.items():
            region = self.regions[symbol]
            prepared_symbols[symbol] = [prefix+namespaces[0][0]] + region

        return prepared_symbols

    def run_schedule(self):
        self.scheduled = None
        if self.has_schedule():
            self.scheduled = self.pending.popitem()
            namespaces = self.scheduled[1]
            self.view.window().show_quick_panel(namespaces, self.on_symbol_selected)
        elif self.has_content():
            symbols_with_region = self.prepare_symbols()
            self.symbols = None
            self.view.run_command('phpme_post_expand_fqcn', {'symbols': symbols_with_region})
        else:
            self.print_message('Expands nothing, please put your cursor in a valid symbol')

    def on_symbol_selected(self, index):
        if index > -1:
            symbol = self.scheduled[0]
            namespaces = self.scheduled[1][index]
            # insert symbol back to list
            self.symbols[symbol] = [namespaces]
            self.run_schedule()

    def find_selected_symbol(self):
        keywords = []
        for region in self.view.sel():
            keyword = self.view.substr(self.view.word(region))
            if re.match(r"\w+", keyword):
                keywords.append(keyword)
                self.regions[keyword] = [region.begin(), region.end()]
            else:
                self.print_message('Not a valid symbol: "{}"'.format(keyword))

        self.symbols = self.find_symbols(keywords)

        return True
