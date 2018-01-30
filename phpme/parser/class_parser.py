import os
import re
from ..constant import Constant


class ClassParser:
    """
    Parse class content, not support multiple class definition
    """

    def __init__(self, content, file = None):
        self.content = content
        self.file = file

    def is_native_hintable(hint):
        excludes = r'(array)'

        return re.search(excludes, hint) != None

    def is_native_hint(hint):
        excludes = r'(null|array|bool|boolean|string|int|integer|long|object|resource|float|double|decimal|real|numeric)'

        return re.search(excludes, hint) != None

    def remove_native_hint(line):
        type_hints = re.findall(r'(([\w\\]+)\s+)\$', line)
        if type_hints:
            for hint in type_hints:
                if ClassParser.is_native_hint(hint[1]) and not ClassParser.is_native_hintable(hint[1]):
                    line = line.replace(hint[0], '')

        return line

    def create(content, file = None):
        return ClassParser(content, file)

    def get_lines(self):
        if self.content:
            return self.content.splitlines()

        if self.file:
            with open(self.file, "r") as f:
                content = f.read()

            return content.splitlines()

        return []

    def same_dir_namespace(self, alias):
        if self.file and self.result['namespace'] and alias != os.path.basename(self.file).split('.')[0]:
            sep = '\\'
            pfile = os.path.dirname(self.file) + os.sep + alias.lstrip(sep).replace(sep, os.sep) + '.php'

            return os.path.isfile(pfile)

    def parse(self):
        lines = self.get_lines()
        self.ctr = 0
        self.llen = len(lines)
        self.maxi = self.llen - 1
        self.do_parse = self.llen > 0
        self.comments = {}
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
            # uses alias can refer declaration of 'as'
            # if uses has no alias (eg: fqcn), namespace should be None
            # list of dict with key ns and as
            'uses': [],
            'implements': [],
            'methods': [],
            'properties': [],
            'parent': None
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
            comment = line
            while check():
                self.inc()
                comment += '\n' + lines[self.ctr]
                line = lines[self.ctr].strip()
            else:
                self.inc()

            next_line = lines[self.ctr].strip()
            if next_line:
                self.comments[next_line] = comment

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
                    self.result['uses'].append({'ns': match[0], 'as': match[1]})
                else:
                    self.result['uses'].append({'ns': None, 'as': match[0]})
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
            self.result['fqcn'] = self.result['namespace'] + '\\' + self.result['name'] if self.result['namespace'] else None

            # has extension or implements interface
            if match.group(4):
                rest = match.group(4).strip().split('implements')
                # parse interfaces
                if len(rest) > 1 and rest[1].strip():
                    for interface in rest[1].strip().split(','):
                        interface = interface.strip()
                        found = self.find_used_use(interface)
                        if found:
                            self.result['implements'].append(found)

                # parse parent
                if rest[0].strip():
                    x = rest[0].strip().split('extends')
                    if len(x) > 1 and x[-1].strip():
                        parent = x[-1].strip()
                        self.result['parent'] = self.find_used_use(parent)

            return True

    def match_property(self, line, lines):
        """Recognize variable in class"""
        if self.incontext['class'] and not self.incontext['function']:
            start_line = line
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
                docblocks = self.get_docblocks(start_line)
                hint = None
                uses = []
                if docblocks:
                    match_hint = re.search(r'@var\s+([\w\\]+)', docblocks)
                    if match_hint:
                        hint = match_hint.group(1)
                        found = self.find_used_use(hint)
                        if found:
                            uses.append(found)

                for i in range(0, len(matches)):
                    if i > 0:
                        hint = None
                        uses = []

                    self.result['properties'].append({
                        'name': matches[i][3],
                        'hint': hint,
                        'uses': uses,
                        'docblocks': docblocks,
                        'visibility': matches[i][1],
                        'static': matches[i][2].strip() == 'static'
                    })

                return True

    def match_method(self, line, lines):
        """Recognize method declaration in class"""
        if self.incontext['class']:
            start_line = line
            if re.search(r'(abstract\s+)?((public|protected|private)?(\s+static)?\s*function\s*([&|\w]+))', line):
                closed = lambda: '{' in line or line.strip().endswith(';')
                while not closed():
                    self.inc()
                    line += '\n' + lines[self.ctr]
                else:
                    self.inc()

            p = r'(abstract\s+)?((public|protected|private)?(\s+static)?\s*function\s*([&|\w]+)\s*\((.*?)\)(?:\s*\:\s*\w+)?)(?:\s*;|.*?{)'
            match = re.search(p, line, re.S)
            if match:
                self.result['methods'].append({
                    'name': match.group(5),
                    'docblocks': self.get_docblocks(start_line),
                    'def': match.group(2),
                    'uses': self.find_uses_args(match.group(6)),
                    'visibility': match.group(3) if match.group(3) else 'public',
                    'static': (match.group(4) and (match.group(4).strip() == 'static')),
                    'abstract': (match.group(1) and (match.group(1).strip() == 'abstract'))
                })

                # move until method close
                closed = (self.ctr == self.maxi) or line.strip().endswith(';')
                self.incontext['function'] = not closed

                brace_start = self.count_brace(line)
                brace_open  = brace_start - 1 if brace_start else 0

                while not closed:
                    next_line = lines[self.ctr]

                    brace_open += self.count_brace(next_line)
                    closed = (self.ctr == self.maxi) or ('}' in next_line and brace_open + brace_start < 1)

                    self.incontext['function'] = not closed
                    self.inc()

                return True

    def count_brace(self, line):
        open_brace = len(re.findall(r'(\{)(?=(?:[^\'"]|["\'][^\'"]*["\'])*$)', line))
        close_brace = len(re.findall(r'(\})(?=(?:[^\'"]|["\'][^\'"]*["\'])*$)', line))

        return open_brace - close_brace

    def find_uses_args(self, line):
        uses = []
        type_hints = re.findall(r'([\w\\]+)\s+\$', line)
        if type_hints:
            for hint in type_hints:
                found = self.find_used_use(hint)
                if found:
                    uses.append(found)

        return uses

    def find_used_use(self, namespace):
        namespace = namespace.strip('\\')
        if not ClassParser.is_native_hint(namespace):
            for r in self.result['uses']:
                if r['as'] == namespace or (r['as'].endswith(namespace) and not r['ns']):
                    return r

            if self.same_dir_namespace(namespace):
                return {'as': namespace, 'ns': Constant.in_dir}
            else:
                return {'as': namespace, 'ns': Constant.in_globals}

    def get_docblocks(self, line):
        docblocks = None
        if line in self.comments:
            docblocks = self.comments[line]
            del self.comments[line]

        return docblocks
