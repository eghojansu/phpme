import sublime_plugin
import re
from ..helper import Helper


class PhpmeExpandFqcnCommand(sublime_plugin.TextCommand):
    """Expand classes to fqcn"""

    def run(self, edit):
        self.pending = {}
        # prepared symbol
        self.symbols = {}
        self.notfound = []
        self.invalid = []
        self.helper  = Helper(self.view)
        self.prefix = '\\' if self.helper.setting_get('prefix_fqcn', True) else ''

        if self.helper.not_scope():
            self.helper.e_scope()
        else:
            self.find_selected_symbols()
            self.run_schedule()

            if len(self.notfound) > 0:
                self.helper.print_message('Symbol not found: "{}"'.format('", "'.join(self.notfound)))

            if len(self.invalid) > 0:
                self.helper.print_message('Not a valid symbol: "{}"'.format(self.invalid))

    def has_schedule(self):
        return len(self.pending) > 0

    def run_schedule(self):
        self.scheduled = None
        if self.has_schedule():
            self.scheduled = self.pending.popitem()
            self.view.window().show_quick_panel(self.scheduled[1], self.on_symbol_selected)
        else:
            self.view.run_command('phpme_post_expand_fqcn', {'symbols': self.symbols})

    def on_symbol_selected(self, index):
        if index > -1:
            symbol = self.scheduled[0]
            namespace = self.scheduled[1][index][0]
            self.symbols[symbol] = self.prefix + namespace
            self.run_schedule()

    def find_selected_symbols(self):
        for region in self.view.sel():
            keyword = self.view.substr(self.view.word(region))
            if re.match(r"\w+", keyword):
                namespaces = self.helper.find_symbol(keyword)
                nlen = len(namespaces)
                if nlen == 0:
                    self.notfound.append(keyword)
                elif nlen == 1:
                    self.symbols[keyword] = self.prefix + namespaces[0][0]
                else:
                    namespaces.sort(key = lambda i: len(i[0]))
                    self.pending[keyword] = namespaces
            else:
                self.invalid.append(keyword)
