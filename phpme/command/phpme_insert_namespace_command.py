import sublime
import sublime_plugin
import os
from ..helper import Helper
from ..composer import Composer


class PhpmeInsertNamespaceCommand(sublime_plugin.TextCommand):
    """Insert guessed namespace"""

    def run(self, edit):
        self.edit = edit
        self.helper = Helper(self.view)

        if self.helper.not_file():
            self.helper.e_file()
        elif self.helper.not_php():
            self.helper.e_php()
        else:
            namespace = self.find_namespace()
            if self.replace_namespace(namespace) or self.insert_namespace(namespace):
                self.helper.print_message('Inserted namespace: "{}"'.format(namespace))
            else:
                self.helper.e_scope()

    def replace_namespace(self, namespace):
        region = self.view.find(r'^namespace\s+[^;]+;', 0)
        if not region.empty():
            replace_region = sublime.Region(region.begin()+10, region.end()-1)
            self.view.replace(self.edit, replace_region, namespace)
            return True

    def insert_namespace(self, namespace):
        region = self.view.find(r"<\?php", 0)
        if not region.empty():
            line = self.view.line(region)
            line_content = '\n\nnamespace {};'.format(namespace)
            self.view.insert(self.edit, line.end(), line_content)
            return True

    def find_namespace(self):
        project_dir = self.helper.project_dir() + os.sep
        dir_prefix = os.path.dirname(self.helper.filename).replace(project_dir, '') + os.sep
        dp_flex = [dir_prefix, dir_prefix[:-1]]

        lookups = self.helper.setting_get('namespaces', {})
        lookups.update(Composer.create(project_dir).autoload())
        for namespace, path in lookups.items():
            for dp in dp_flex:
                if (path == dp) or (isinstance(path, list) and dp in path):
                    return namespace.strip('\\')

        return dir_prefix.replace('/', '\\')
