import sublime
import contextlib
import mmap
import re
import os
from .binx.console import Console
from .constant import Constant
from .utils import Utils
from .parser.class_parser import ClassParser


class Helper():

    def __init__(self, view):
        filename = view.file_name()

        self.filename = os.path.abspath(filename) if filename else filename
        self.view = view
        # setting cache
        self.cache = {}

    def content(self):
        return self.view.substr(sublime.Region(0, self.view.size()))

    def project_dir(self, filename = None):
        if not filename:
            filename = self.filename
        for folder in sorted(self.view.window().folders(), reverse = True):
            if filename.startswith(folder):
                return folder

        return ''

    def setting_get(self, name, default = None):
        setting_cache = self.cache.get(name)
        if setting_cache == None:
            # setting in run time
            view_setting = self.view.settings().get(name)
            if view_setting == None:
                pd = self.view.window().project_data()
                try:
                    return pd['phpme'][name]
                except Exception as e:
                    return sublime.load_settings(Constant.setting).get(name, default)
            else:
                return view_setting
        else:
            return setting_cache

    def is_file_excluded(self, file):
        for pattern in self.setting_get('exclude_dir', []):
            if re.compile(pattern).match(file):
                return True

        return False

    def is_global(self, found):
        return found and found[1] == Constant.in_globals

    def find_symbol(self, symbol, namespace = None, in_globals = True):
        pattern = re.compile(b'^namespace\s+([^;]+);', re.M)
        namespaces = []
        index = []
        for file in self.view.window().lookup_symbol_in_index(symbol):
            if namespace and namespace in index:
                break
            if not self.is_file_excluded(file[1]):
                with open(file[0], "rb") as f:
                    with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
                        match = re.search(pattern, m)
                        if match:
                            ns_in_file = match.group(1).decode('utf-8') + '\\' + symbol
                            namespaces.append([ns_in_file, file[0]])
                            index.append(ns_in_file)

        if in_globals and self.setting_get('allow_use_from_global_namespace', False):
            for ns in Console.get_classes(symbol):
                if namespace and namespace in index:
                    break
                namespaces.append([ns, Constant.in_globals])
                index.append(ns)

        return namespaces

    def print_message(self, message):
        print('[Phpme]', message)
        sublime.status_message(message)

    def e_file(self):
        self.print_message('Not a file')

    def e_php(self):
        self.print_message('No .php extension')

    def e_scope(self):
        self.print_message('No php area')

    def e_class(self):
        self.print_message('Not a class')

    def e_interface(self):
        self.print_message('Not an interface')

    def e_trait(self):
        self.print_message('Not a trait')

    def not_file(self):
        return not self.filename

    def not_php(self):
        return not self.filename or not self.filename.endswith('.php')

    def not_scope(self):
        return None == self.view.find(r'<\?php', 0)

    def not_class(self, mdef, types = None):
        try:
            if not types:
                types = ['class', 'interface', 'trait']

            return mdef['type'] not in types
        except Exception as e:
            return True

    def create_method_stub(self, mdef):
        stub = ''
        mode = 'copy' if mdef.get('force_docblock', False) else self.setting_get('docblock_inherit')
        if mdef['docblocks'] and (mode in ['copy', 'inheritdoc']):
            if 'copy' == mode:
                docblocks = mdef['docblocks']
            elif 'inheritdoc' == mode:
                docblocks = '\n\t'.join(['/**', ' * {@inheritdoc}', ' */'])
            stub += docblocks + '\n\t'

        stub += mdef['def'].strip()
        stub += ' ' if '\n' in mdef['def'].strip() else '\n\t'
        stub += '\n\t'.join(['{'] + mdef.get('content', ['\t// TODO: write method logic']) + ['}'])

        return stub

    def arrange_methods(self, namespace_methods):
        arranged_methods = []
        uses = []
        arranged = []
        allow_native_hint = self.setting_get('native_hint', False)
        for namespace in sorted(list(namespace_methods.keys())):
            for mdef in namespace_methods[namespace]:
                if not allow_native_hint:
                    mdef['def'] = ClassParser.remove_native_hint(mdef['def'])
                arranged.append('::'.join([namespace, mdef['name']]))
                arranged_methods.append(self.create_method_stub(mdef))
                uses += mdef['uses']

        return {
            'methods': arranged_methods,
            'uses': uses,
            'arranged': arranged
        }

    def parse_class_tree(self, ctype, namespace, file, root):
        result = {}
        if file == Constant.in_globals:
            if ctype == 'interface':
                result[namespace] = Console.get_interface_methods(namespace)
            else:
                result[namespace] = Console.get_class_methods(namespace)
        else:
            mdef = ClassParser.create(None, file).parse()
            if mdef['methods']:
                result[namespace] = []
                for mmdef in mdef['methods']:
                    mmdef['uses'] = self.decide_class_uses(mmdef['uses'], mdef, root)
                    result[namespace].append(mmdef)
                if mdef['parent']:
                    use_parent = self.decide_use(
                        mdef['parent']['as'],
                        mdef['parent']['ns'],
                        mdef['namespace'],
                        mdef['uses']
                    )
                    parent = use_parent.split('\\')[-1]
                    for namespace in self.find_symbol(parent):
                        if namespace[0] == use_parent:
                            result.update(self.parse_class_tree(ctype, namespace[0], namespace[1], root))
                            break

        return result

    def decide_class_uses(self, uses, parent, root):
        uses_added = []
        for u in uses:
            use = None
            if u['ns'] == Constant.in_dir:
                if parent['namespace'] != root['namespace']:
                    use = parent['namespace'] + '\\' + u['as']
            elif u['ns'] == Constant.in_globals:
                use = u['as']
            else:
                use = u['ns'] if u['ns'] else u['as']

            if use:
                found = Utils.find(root['uses'], 'as', use)
                if not found:
                    uses_added.append(use)

        return uses_added


    def decide_use(self, alias, namespace, root, uses):
        if namespace == Constant.in_dir:
            use = root + '\\' + alias
        elif namespace == Constant.in_globals:
            use = alias
        elif namespace:
            use = namespace
        else:
            found = Utils.find(uses, 'as', alias)
            if found['ns']:
                use = found['ns']
            else:
                use = alias

        return use

    def decide_hint(self, hint, allow_native_hint):
        def_hint = ''
        doc_hint = 'mixed'
        if hint:
            def_hint = hint
            doc_hint = hint
            if ClassParser.is_native_hint(hint) and not ClassParser.is_native_hintable(hint) and not allow_native_hint:
                def_hint = ''

        return (def_hint, doc_hint)

    def decide_uses(self, uses, parent_uses):
        uses_added = []
        for u in uses:
            if u['ns'] == Constant.in_dir:
                pass
            elif u['ns'] == Constant.in_globals:
                found = Utils.find(parent_uses, 'as', u['as'])
                if not found:
                    uses_added.append(u['as'])
            else:
                use = u['ns'] if u['ns'] else u['as']
                found = Utils.find(parent_uses, 'as', use)
                if not found:
                    uses_added.append(use)

        return uses_added
