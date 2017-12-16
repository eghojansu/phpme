import os
import json


class Composer():

    __composer = 'composer.json'

    def __init__(self, project_dir):
        self.content = self.load(project_dir + os.sep + self.__composer)

    def create(project_dir):
        return Composer(project_dir)

    def load(self, file):
        try:
            with open(file) as f:
                return json.load(f)
        except Exception as e:
            pass

    def value(self, key):
        try:
            return self.content[key]
        except Exception as e:
            pass

    def values(self, keys):
        values = {}

        for key in keys:
            try:
                values[key] = self.content[key]
            except Exception as e:
                values[key] = None

        return values

    def autoload(self):
        autoload = {}

        for key in (['autoload', 'autoload-dev'] if self.content else []):
            for psr in ['psr-0','psr-4']:
                if (key in self.content) and (psr in self.content[key]):
                    autoload.update(self.content[key][psr])

        return autoload

    def author(self):
        author = self.value('author')

        return author[0] if author and isinstance(author, list) else author
