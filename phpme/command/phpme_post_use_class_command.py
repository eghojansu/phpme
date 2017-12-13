import sublime_plugin
from ..phpme_command import PhpmeCommand


class PhpmePostUseClassCommand(sublime_plugin.TextCommand, PhpmeCommand):
    def run(self, edit, namespaces):
        exists = []
        used = []
        for namespace in list(set(namespaces)):
            if self.is_already_used(namespace):
                exists.append(namespace)
            else:
                used.append(namespace)

        if len(used) > 0:
            if self.insert_first_use(edit, used) or self.insert_use_among_others(edit, used):
                self.print_message('Successfully use: "{}"'.format('", "'.join(used)))
            else:
                self.print_message('Something wrong but we have no clue, sorry')

        if len(exists) > 0:
            self.print_message('Namespaces is already used: "{}"'.format('", "'.join(exists)))

    def is_already_used(self, namespace):
        return not self.view.find(r'use\s+{}\s*([^;]+)?;'.format(namespace.replace('\\', '\\\\')), 0).empty()

    def insert_first_use(self, edit, namespaces):
        first_use = self.view.find(r'^use\s+[^;]+;', 0)
        if first_use.empty():
            for pattern in [r'^\s*namespace\s+[^;]+;', r'<\?php']:
                region = self.view.find(pattern, 0)
                if not region.empty():
                    line = self.view.line(region)
                    self.view.insert(edit, line.end(), '\n\n' + self.build_uses(namespaces))
                    return True

    def insert_use_among_others(self, edit, namespaces):
        regions = self.view.find_all(r'^use\s+[^;]+;', 0)
        if len(regions) > 0:
            use_region = regions[0]
            for region in regions:
                use_region = use_region.cover(region)
            self.view.replace(edit, use_region, self.build_uses(namespaces))

            return True

    def build_uses(self, namespaces):
        uses = []

        self.view.find_all(r'^(use\s+[^;]+;)', 0, '$1', uses)
        uses += ['use {};'.format(namespace) for namespace in namespaces]
        uses.sort()
        if self.get_setting('use_sort_length'):
            uses.sort(key = len)

        return '\n'.join(uses)
