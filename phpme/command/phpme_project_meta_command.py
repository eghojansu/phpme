import sublime_plugin
import os
import re
import datetime
import getpass
from ..helper import Helper
from ..composer import Composer
from ..binx.console import Console


class PhpmeProjectMetaCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.helper = Helper(self.view)
        self.composer = Composer(self.helper.project_dir())
        self.author = self.composer.author()

        if self.helper.not_file():
            self.helper.e_file()
        elif self.helper.not_php():
            self.helper.e_php()
        elif self.helper.not_scope():
            self.helper.e_scope()
        else:
            self.insert_meta(edit)
            self.helper.print_message('Project meta has been inserted')

    def config_author(self):
        if self.author:
            author = self.author['name']
        else:
            author = Console.git_config('user.name')
            if not author:
                author = getpass.getuser()

        return author

    def config_email(self):
        if self.author:
            email = self.author['email']
        else:
            email = Console.git_config('user.email')

        return email

    def insert_meta(self, edit):
        region = self.view.find(r"<\?php", 0)
        line = self.view.line(region)

        replaces = {
            'author': self.config_author(),
            'email': self.config_email(),
            'type': self.composer.value('type'),
            'project': self.composer.value('name')
        }

        line_content = '\n * '.join(self.helper.setting_get('project_meta', [
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
