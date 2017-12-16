import sublime
import sublime_plugin
import re
from ..helper import Helper


class PhpmeGotoDefinitionScopeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.selected_region = None
        helper = Helper(self.view)

        if helper.not_scope() or self.not_in_our_scope():
            # falls back to the original functionality
            self.view.window().run_command('goto_definition')
        else:
            self.goto_definition_scope()

    def goto_definition_scope(self):
        selected_str = self.view.substr(self.selected_region)
        for symbol in self.view.symbols():
            if symbol[1] == selected_str:
                self.view.sel().clear()
                self.view.sel().add(symbol[0])
                self.view.show(symbol[0])
                break

    def not_in_our_scope(self):
        self.selected_region = self.view.word(self.view.sel()[0])
        selected_point = self.selected_region.begin()
        # the search area is 60 pts wide, maybe it is not enough
        search_str = self.view.substr(sublime.Region(selected_point - 60, selected_point))

        return re.search(r'(\$this->|self::|static::)\s*$', search_str) == None
