import sublime_plugin
import re
from ..phpme_command import PhpmeCommand


class PhpmeUseClassCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Import class namespace"""

    def run(self, edit):
        self.symbols = {}
        self.pending = {}

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

    def merge_symbols(self):
        merged_namespaces = []
        for symbol, namespaces in self.symbols.items():
            namespace = namespaces[0][0]
            merged_namespaces.append(namespace)

        return merged_namespaces

    def run_schedule(self):
        self.scheduled = None
        if self.has_schedule():
            self.scheduled = self.pending.popitem()
            namespaces = self.scheduled[1]
            self.view.window().show_quick_panel(namespaces, self.on_symbol_selected)
        elif self.has_content():
            namespaces = self.merge_symbols()
            self.symbols = None
            self.view.run_command('phpme_post_use_class', {'namespaces': namespaces})
        else:
            self.print_message('Use nothing, please put your cursor in a valid symbol')

    def on_symbol_selected(self, index):
        if index > -1:
            symbol = self.scheduled[0]
            namespace = self.scheduled[1][index]
            # insert symbol back to list
            self.symbols[symbol] = [namespace]
            self.run_schedule()

    def find_selected_symbol(self):
        keywords = []
        for region in self.view.sel():
            keyword = self.view.substr(self.view.word(region))
            if re.match(r"\w+", keyword):
                keywords.append(keyword)
            else:
                self.print_message('Not a valid symbol: "{}"'.format(keyword))

        self.symbols = self.find_symbols(keywords)

        return True
