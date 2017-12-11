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
            return json.load(open(project_dir + 'composer.json'))

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
