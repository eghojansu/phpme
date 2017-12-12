import os, json, subprocess


class Console():
    """Run PHP job"""

    def get_interface_methods(namespace):
        output = Console.run_command('interface-methods', [namespace])
        if output:
            return json.loads(output)

        return {}

    def get_class_methods(namespace):
        output = Console.run_command('class-methods', [namespace])
        if output:
            return json.loads(output)

        return {}

    def get_classes(symbol):
        output = Console.run_command('classes', [symbol])
        if output:
            classes = json.loads(output)
            return [[phpClass, 'Found in globals'] for phpClass in classes]

        return []

    def git_config(config):
        try:
            return subprocess.check_output(['git', 'config', '--get', config]).decode('utf-8')
        except Exception as e:
            print('[Phpme]', 'error: ' + str(e))

    def run_command(command, args):
        try:
            console = os.path.dirname(os.path.abspath(__file__)) + '/console.php'
            output = subprocess.check_output(['php', '-f', console, command] + args).decode('utf-8')

            if output.startswith('error'):
                print('[Phpme]', output)
            else:
                return output
        except Exception as e:
            print('[Phpme]', 'error: ' + str(e))
