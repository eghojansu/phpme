import os, json


class Utils:
    """
    Plugin common utils
    """

    def fixslash(path, suffix = False):
        """
        Normalize backslash to slash
        """
        return path.replace('\\', '/').rstrip('/') + ('/' if suffix and path else '')

    def composer_json(project_dir):
        """
        composer.json file location (assume on its project dir)
        """
        if os.path.isfile(project_dir + 'composer.json'):
            try:
                return json.load(open(project_dir + 'composer.json'))
            except Exception as e:
                pass

    def composer_autoload(project_dir):
        """
        Get autoload schema from composer.json
        """
        autoload = {}

        composer = Utils.composer_json(project_dir)
        if composer:
            for key in ['autoload', 'autoload-dev']:
                for psr in ['psr-0','psr-4']:
                    if (key in composer) and (psr in composer[key]):
                        autoload.update(composer[key][psr])

        return autoload

    def composer_value(project_dir, key):
        """
        Get project value
        """
        composer = Utils.composer_json(project_dir)
        if composer and key in composer:
            return composer[key]

    def composer_author(project_dir):
        """
        Get single author from composer.json
        """
        author = Utils.composer_value(project_dir, 'author')
        if author and isinstance(author, list):
            author = author[0]

        return author
