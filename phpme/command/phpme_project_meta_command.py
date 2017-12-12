import sublime_plugin
import os, re, datetime, getpass
from ..phpme_command import PhpmeCommand
from ..utils import Utils
from ..binx.console import Console


class PhpmeProjectMetaCommand(sublime_plugin.TextCommand, PhpmeCommand):
    def run(self, edit):
        if self.in_php_scope():
            if self.insert_meta(edit):
                self.print_message('Project meta has been inserted')
            else:
                self.print_message('No php area')

    def config_author(self):
        author = Utils.composer_author(self.pdir)
        if author:
            author = author['name']
        else:
            author = Console.git_config('user.name')
            if not author:
                author = getpass.getuser()

        return author

    def config_email(self):
        author = Utils.composer_author(self.pdir)
        if author:
            email = author['email']
        else:
            email = Console.git_config('user.email')

        return email

    def insert_meta(self, edit):
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

        self.pdir = self.project_dir(filename)

        region = self.view.find(r"<\?php", 0)
        if not region.empty():
            line = self.view.line(region)

            replaces = {
                'author': self.config_author(),
                'email': self.config_email(),
                'type': Utils.composer_value(self.pdir, 'type'),
                'project': Utils.composer_value(self.pdir, 'name')
            }

            line_content = '\n * '.join(self.get_setting('project_meta', [
                r'This file is part of the {project} {type}.',
                '',
                r'(c) {author} <{email}>',
                '',
                'For the full copyright and license information, please view the LICENSE',
                'file that was distributed with this source code.',
                '',
                r'Created at {time(%b %d, %Y %H:%M)}'
            ]))
            for key, replace in replaces.items():
                line_content = line_content.replace('{'+key+'}', replace)

            match_time = re.search(r'\{time(?:\(([^\)]*)\))?\}', line_content)
            if match_time:
                line_content = re.sub(match_time.re.pattern, datetime.datetime.now().strftime(match_time.group(1)), match_time.string)

            line_content = '\n\n/**\n * ' + line_content + '\n */'

            self.view.insert(edit, line.end(), line_content)

            return True
