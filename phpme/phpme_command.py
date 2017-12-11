import sublime
import os, re, json, subprocess, contextlib, mmap
from .utils import Utils
from .binx.console import Console
from .parser.class_parser import ClassParser


class PhpmeCommand():
    """Command helper, should be used with sublime_plugin.TextCommand"""

    def setting_filename(self):
        """
        Get setting filename
        """
        return 'PHPMe.sublime-settings'

    def project_dir(self, file):
        """
        Get project dir based on absolute file path
        """
        for folder in sorted(self.view.window().folders(), reverse = True):
            if file.startswith(folder):
                return Utils.fixslash(folder, True)

        return ''

    def get_setting(self, name, default = None):
        """
        Get setting
        """
        # setting in run time
        view_setting = self.view.settings().get(name)
        if view_setting != None:
            return view_setting

        project_data = self.view.window().project_data()
        if project_data and 'phpme' in project_data and name in project_data['phpme']:
            return project_data['phpme'][name]

        return sublime.load_settings(self.setting_filename()).get(name, default)

    def is_excluded(self, file):
        """
        Check if file is excluded
        """
        excludes = self.get_setting('exclude_dir')
        if excludes:
            for pattern in excludes:
                if re.compile(pattern).match(file):
                    return True

        return False

    def find_symbols(self, keywords):
        """
        Find symbols by keywords
        """
        symbols = {}
        for keyword in keywords:
            symbols[keyword] = self.find_symbol(keyword)

        return symbols

    def find_symbol(self, symbol):
        """
        Find single symbol
        """
        namespace_pattern = re.compile(b'namespace\s+([^;]+);', re.MULTILINE)
        namespaces = []
        for file in self.view.window().lookup_symbol_in_index(symbol):
            if not self.is_excluded(file[1]):
                with open(file[0], "rb") as f:
                    with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
                        for match in re.findall(namespace_pattern, m):
                            namespaces.append([match.decode('utf-8') + "\\" + symbol, file[0]])
                            break

        if self.get_setting('allow_use_from_global_namespace', False):
            namespaces += Console.get_classes(symbol)

        namespaces.sort()

        return namespaces

    def build_use(self, namespace, alias = None):
        """
        Build use namespace string and its alias if exists
        """
        if namespace:
            use = namespace
            if alias and alias != namespace and not namespace.endswith(alias):
                use += ' as ' + alias
        else:
            use = alias

        return use

    def create_method_stub(self, method, mdef):
        """
        Create method stub
        """
        force = mdef.get('force_docblock', False)
        mode = 'copy' if force else self.get_setting('docblock_inherit')
        stub = ''
        if mdef['docblocks'] and (mode in ['copy', 'inheritdoc']):
            if 'copy' == mode:
                docblocks = mdef['docblocks']
            elif 'inheritdoc' == mode:
                docblocks = '\n\t'.join(['/**', ' * {@inheritdoc}', ' */'])
            stub += docblocks + '\n\t'

        stub += mdef['def'].strip()
        if re.search(r'\n', mdef['def'].strip()):
            stub += ' '
        else:
            stub += '\n\t'
        content = mdef.get('content', ['\t// TODO: write method logic'])
        stub += '\n\t'.join(['{'] + content + ['}'])

        return stub

    def arrange_methods(self, namespace_methods):
        """
        Arrange namespace methods
        """
        arranged_methods = []
        uses = []
        overriden = []
        for namespace, methods in namespace_methods.items():
            for method in sorted(methods.keys()):
                mdef = methods[method]
                overriden.append('::'.join([namespace, method]))
                arranged_methods.append(self.create_method_stub(method, mdef))
                if mdef['uses']:
                    for use_alias, use_namespace in mdef['uses'].items():
                        uses.append(self.build_use(use_namespace, use_alias))

        return {
            'methods': arranged_methods,
            'uses': uses,
            'overriden': overriden
        }

    def print_message(self, message):
        """
        Print and info status message
        """
        print('[Phpme]', message)
        sublime.status_message(message)

    def parse_class_tree(self, ctype, namespace, file):
        """
        Parse class and its parents (nested)
        """
        result = {}
        if file == 'Found in globals':
            if ctype == 'interface':
                result[namespace] = Console.get_interface_methods(namespace)
            else:
                result[namespace] = Console.get_class_methods(namespace)
        else:
            mdef = ClassParser.create(None, file).parse()
            if mdef['methods']:
                result[namespace] = mdef['methods']
                if mdef['parent']:
                    parent = mdef['parent']['alias'].split('\\')[-1]
                    parent_namespace = mdef['parent']['namespace'] if mdef['parent']['namespace'] else mdef['parent']['alias']
                    for namespace in self.find_symbol(parent):
                        if namespace[0] == parent_namespace:
                            result.update(self.parse_class_tree(ctype, namespace[0], namespace[1]))
                            break

        return result

    def in_php_scope(self):
        result = self.view.score_selector(self.view.sel()[0].end(), "source.php") > 0
        if not result:
            self.print_message('Not in PHP scope')

        return result

    def in_class_scope(self, mdef):
        result = mdef['type'] and mdef['type'] in ['class', 'interface', 'trait']
        if not result:
            self.print_message('Not in class scope')

        return result
