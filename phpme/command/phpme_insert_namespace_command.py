import sublime, sublime_plugin
import os
from ..phpme_command import PhpmeCommand
from ..utils import Utils


class PhpmeInsertNamespaceCommand(sublime_plugin.TextCommand, PhpmeCommand):
    """Insert guessed namespace"""

    def run(self, edit):
        self.namespace = None

        if self.build_namespace():
            if self.replace_namespace(edit) or self.insert_namespace(edit):
                self.print_message('Inserted namespace: "{}"'.format(self.namespace))
            else:
                self.print_message('No php area')

    def replace_namespace(self, edit):
        region = self.view.find(r'^namespace\s+[^;]+;', 0)
        if not region.empty():
            replace_region = sublime.Region(region.begin()+10, region.end()-1)
            self.view.replace(edit, replace_region, self.namespace)
            return True

    def insert_namespace(self, edit):
        region = self.view.find(r"<\?php", 0)
        if not region.empty():
            line = self.view.line(region)
            line_content = '\n\nnamespace {};'.format(self.namespace)
            self.view.insert(edit, line.end(), line_content)
            return True

    def find_namespace(self, filename):
        project_dir = self.project_dir(filename)
        dir_prefix = Utils.fixslash(os.path.dirname(filename)).replace(project_dir, '') + '/'
        dp_flex = [dir_prefix, dir_prefix[:-1]]

        lookups = self.get_setting('namespaces', {})
        lookups.update(Utils.composer_autoload(project_dir))
        for namespace, path in lookups.items():
            for dp in dp_flex:
                if (path == dp) or (isinstance(path, list) and dp in path):
                    return namespace

        return dir_prefix.replace('/', '\\')

    def build_namespace(self):
        # current view filename
        filename = os.path.abspath(self.view.file_name())

        # abort if not a file
        if (filename is None):
            self.print_message('Not a file')
            return

        # abort if the file is not PHP
        if (not filename.endswith('.php')):
            self.print_message('No .php extension')
            return

        self.namespace = self.find_namespace(filename).strip('\\')

        return True
