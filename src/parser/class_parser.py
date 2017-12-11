import re, os
from ..utils import Utils

class ClassParser:
    """
    Parse class content, not support multiple class definition
    """

    def __init__(self, content, file = None):
        self.content = content
        self.file = file

    def create(content, file = None):
        return ClassParser(content, file)

    def get_lines(self):
        if self.content:
            return self.content.splitlines()

        if self.file:
            return self.file_content(self.file).splitlines()

        return []

    def file_content(self, file):
        # Get the contents of the file at the given path
        with open(file, "r") as f:
            content = f.read()

        return content

    def same_dir_namespace(self, alias):
        if self.file and self.result['namespace']:
            pfile = os.path.dirname(self.file) + '/' + Utils.fixslash(alias) + '.php'
            if os.path.isfile(pfile):
                return self.result['namespace'] + '\\' + alias;

    def parse(self):
        lines = self.get_lines()
        self.ctr = 0
        self.llen = len(lines)
        self.maxi = self.llen - 1
        self.do_parse = self.llen > 0
        self.incontext = {
            'class': False,
            'function': False
        }
        self.result = {
            'name': None,
            'namespace': None,
            'fqcn': None,
            'abstract': False,
            'final': False,
            'type': None,
            'is_interface': False,
            'is_trait': False,
            # dict with key namespace and alias
            'parent': None,
            # @see uses
            'implements': {},
            'methods': {},
            'properties': {},
            # uses alias can refer declaration of 'as'
            # if uses has no alias (eg: fqcn), namespace should be None
            'uses': {}
        }

        while self.do_parse:
            line = lines[self.ctr].strip()
            if line:
                if self.match_comment(line, lines):
                    pass
                elif self.match_namespace(line):
                    pass
                elif self.match_use(line):
                    pass
                elif self.match_class(line, lines):
                    pass
                elif self.match_method(line, lines):
                    pass
                elif self.match_property(line, lines):
                    pass
                else:
                    self.inc()
            else:
                self.inc()
            if self.do_parse:
                self.do_parse = self.ctr < self.maxi

        return self.result

    def inc(self):
        self.ctr += 1

    def match_comment(self, line, lines):
        """Recognize comment section"""
        if line.startswith('//') or line.startswith('#'):
            self.inc()

            return True

        elif line.startswith('/*'):
            # move until ends of block comment
            check = lambda: self.ctr <= self.maxi and not line.endswith('*/')
            while check():
                self.inc()
                line = lines[self.ctr].strip()
            else:
                self.inc()

            return True

    def match_namespace(self, line):
        """Recognize namespace in the beginning of line or after php open tag"""
        p = r'^(?:<\?php\s+)?namespace\s+([^;]+);'
        match = re.search(p, line)
        if match and not self.result['namespace']:
            self.result['namespace'] = match.group(1)
            self.inc()

            return True

    def match_use(self, line):
        """Recognize inline use statement to"""
        p = r'use\s+([^; ]+)(?:\s+as\s+(\w+))?;'
        matches = re.findall(p, line)
        if matches:
            for match in matches:
                if match[1]:
                    self.result['uses'][match[1]] = match[0]
                else:
                    self.result['uses'][match[0]] = None
            self.inc()

            return True

    def match_class(self, line, lines):
        """Recognize class opening"""
        if self.incontext['class']:
            # not support multiple class (as we dont know how to find class section)
            return

        if re.search(r'^(?:(abstract|final)\s+)?(class|interface|trait)', line):
            self.incontext['class'] = True
            closed = lambda: '{' in line
            while not closed():
                self.inc()
                line += '\n' + lines[self.ctr]
            else:
                self.inc()

        p = r'^(?:(abstract|final)\s+)?(class|interface|trait)\s+(\w+)(?:\s+([^\{]+))?'
        match = re.search(p, line)
        if match:
            self.result['abstract'] = match.group(1) == 'abstract'
            self.result['final'] = match.group(1) == 'final'
            self.result['type'] = match.group(2)
            self.result['name'] = match.group(3)
            self.result['fqcn'] = self.result['name']
            self.result['is_interface'] = self.result['type'] == 'interface'
            self.result['is_trait'] = self.result['type'] == 'trait'

            if self.result['namespace']:
                self.result['fqcn'] = '\\'.join([self.result['namespace'], self.result['name']])

            # has extension or implements interface
            if match.group(4):
                rest = match.group(4).strip().split('implements')
                # parse interfaces
                if len(rest) > 1 and rest[1].strip():
                    for interface in rest[1].strip().split(','):
                        interface = interface.strip().strip('\\')
                        if interface in self.result['uses']:
                            self.result['implements'][interface] = self.result['uses'][interface]
                        else:
                            self.result['implements'][interface] = self.same_dir_namespace(interface)
                # parse parent
                if rest[0].strip():
                    x = rest[0].strip().split('extends')
                    if len(x) > 1 and x[-1].strip():
                        parent = x[-1].strip().strip('\\')
                        if parent in self.result['uses']:
                            self.result['parent'] = {
                                'alias': parent,
                                'namespace': self.result['uses'][parent]
                            }
                        else:
                            self.result['parent'] = {
                                'alias': parent,
                                'namespace': self.same_dir_namespace(parent)
                            }

            return True

    def match_property(self, line, lines):
        """Recognize variable in class"""
        if self.incontext['class'] and not self.incontext['function']:
            start_line = self.ctr
            if re.search(r'((public|private|protected)?(\s*static)?\s*\$\w+)', line):
                closed = lambda: line.strip().endswith(';')
                while not closed():
                    self.inc()
                    line += '\n' + lines[self.ctr]
                else:
                    self.inc()

            p = r'((public|private|protected)?(\s*static)?\s*\$(\w+)(?:\s+=\s+[^;]+)?;)'
            matches = re.findall(p, line)
            if matches:
                docblocks = self.find_docblocks(start_line - 1, lines)
                hint = None
                uses = {}
                if docblocks:
                    match_hint = re.search(r'@var\s+([\w\\]+)', docblocks)
                    if match_hint:
                        hint = match_hint.group(1)
                        found = self.find_used_uses(hint)
                        if found:
                            uses[found[0]] = found[1]

                for i in range(0, len(matches)):
                    name = matches[i][3]
                    if i > 0:
                        hint = None
                        uses = {}

                    self.result['properties'][name] = {
                        'hint': hint,
                        'uses': uses,
                        'visibility': matches[i][1],
                        'public': 'public' == matches[i][1],
                        'private': 'private' == matches[i][1],
                        'protected': 'protected' == matches[i][1],
                        'static': matches[i][2].strip() == 'static'
                    }

                return True

    def match_method(self, line, lines):
        """Recognize method declaration in class"""
        if self.incontext['class']:
            start_line = self.ctr
            if re.search(r'(abstract\s+)?((public|protected|private)?(\s+static)?\s*function\s*([\w]+))', line):
                closed = lambda: '{' in line or line.strip().endswith(';')
                while not closed():
                    self.inc()
                    line += '\n' + lines[self.ctr]
                else:
                    self.inc()

            p = r'(abstract\s+)?((public|protected|private)?(\s+static)?\s*function\s*([\w]+)\s*\((.*?)\)(?:\s*\:\s*\w+)?)(?:\s*;|.*?{)'
            match = re.search(p, line, re.S)
            if match:
                docblocks = self.find_docblocks(start_line - 1, lines)

                name = match.group(5)
                visibility = match.group(3)
                self.result['methods'][name] = {
                    'docblocks': docblocks,
                    'def': match.group(2),
                    'uses': self.find_uses_args(match.group(6)),
                    'visibility': visibility,
                    'public': 'public' == visibility,
                    'private': 'private' == visibility,
                    'protected': 'protected' == visibility,
                    'static': (match.group(4) and (match.group(4).strip() == 'static')),
                    'abstract': (match.group(0) and (match.group(0).strip() == 'abstract')),
                }

                # move until method close
                brace_open = line.count('{') - 1
                closed = (self.ctr == self.maxi) or line.strip().endswith(';')
                self.incontext['function'] = not closed
                while not closed:
                    next_line = lines[self.ctr]
                    brace_open += (next_line.count('{') - next_line.count('}'))
                    closed = (self.ctr == self.maxi) or ('}' in next_line and brace_open < 1)
                    self.inc()
                    self.incontext['function'] = not closed

                return True

    def find_uses_args(self, line):
        uses = {}
        type_hints = re.findall(r'([\w\\]+)\s+\$', line)
        if type_hints:
            for hint in type_hints:
                found = self.find_used_uses(hint)
                if found:
                    uses[found[0]] = found[1]

        return uses

    def find_used_uses(self, symbol):
        excludes = r'(null|array|bool|boolean|string|int|integer|long|object|resource|float|double|decimal|real|numeric)'
        if not re.search(excludes, symbol):
            if symbol in self.result['uses']:
                return (symbol, self.result['uses'][symbol])
            else:
                return (symbol, self.same_dir_namespace(symbol))

    def find_docblocks(self, line_end, lines):
        if line_end < 1:
            return

        line_end_content = lines[line_end].strip()
        if len(line_end_content) == 0 or not line_end_content.endswith('*/'):
            return

        docblocks = lines[line_end]
        closed = line_end_content.startswith('/*')
        ctr = line_end - 1
        while not closed:
            tmp_line = lines[ctr]
            docblocks = tmp_line + '\n' + docblocks
            ctr -= 1
            closed = (ctr < 1) or tmp_line.strip().startswith('/*')

        return docblocks.lstrip()
