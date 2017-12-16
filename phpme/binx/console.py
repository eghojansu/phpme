import os, json, subprocess


class Console():
    """Run PHP job"""

    def get_interface_methods(namespace):
        try:
            output = Console.run_command('interface-methods', [namespace])

            return json.loads(output)
        except Exception as e:
            return {}

    def get_class_methods(namespace):
        try:
            output = Console.run_command('class-methods', [namespace])

            return json.loads(output)
        except Exception as e:
            return {}

    def get_classes(symbol):
        try:
            output = Console.run_command('classes', [symbol])

            return json.loads(output)
        except Exception as e:
            return []

    def git_config(config):
        try:
            return subprocess.check_output(['git', 'config', '--get', config]).decode('utf-8')
        except Exception as e:
            print('[Phpme]', 'error: ' + str(e))

    def run_command(command, args):
        try:
            console = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'console.php'
            output = subprocess.check_output(['php', '-f', console, command] + args).decode('utf-8')

            if output.startswith('error'):
                print('[Phpme]', output)
            else:
                return output
        except Exception as e:
            print('[Phpme]', 'error: ' + str(e))
