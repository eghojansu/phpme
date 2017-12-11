import sublime, sublime_plugin
import re
from ..phpme_command import PhpmeCommand


class PhpmeGotoDefinitionScopeCommand(sublime_plugin.TextCommand, PhpmeCommand):
    def run(self, edit):
        self.selected_region = None

        if self.in_php_scope() and self.find_selected_symbol():
            self.goto_definition_scope()
        else:
            # falls back to the original functionality
            self.view.window().run_command("goto_definition")

    def goto_definition_scope(self):
        selected_str = self.view.substr(self.selected_region)
        for symbol in self.view.symbols():
            if symbol[1] == selected_str:
                self.view.sel().clear()
                self.view.sel().add(symbol[0])
                self.view.show(symbol[0])
                break

    def find_selected_symbol(self):
        self.selected_region = self.view.word(self.view.sel()[0])
        selected_point = self.selected_region.begin()
        # the search area is 60 pts wide, maybe it is not enough
        search_str = self.view.substr(sublime.Region(selected_point - 60, selected_point))

        return re.search(r'(\$this->|self::|static::)\s*$', search_str) != None
