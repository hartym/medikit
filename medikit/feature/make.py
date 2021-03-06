import datetime
import itertools
import textwrap
from collections import deque

import six
from edgy.event import Event
from medikit.events import subscribe

from . import Feature, HIGH_PRIORITY, Script


@six.python_2_unicode_compatible
class Makefile(object):
    @property
    def targets(self):
        for key in self._target_order:
            yield key, self._target_values[key]

    @property
    def environ(self):
        return self._env_values

    def __init__(self):
        self._env_order, self._env_values, self._env_assignment_operators = deque(), {}, {}
        self._target_order, self._target_values = deque(), {}
        self.phony = set()

    def __delitem__(self, key):
        self._env_order.remove(key)
        del self._env_values[key]

    def __getitem__(self, item):
        return self._env_values[item]

    def __setitem__(self, key, value):
        self._env_values[key] = value
        if not key in self._env_order:
            self._env_order.append(key)

    def __iter__(self):
        for key in self._env_order:
            yield key, self._env_values[key]

    def __len__(self):
        return len(self._env_order)

    def __str__(self):
        content = [
            '# This file has been auto-generated.',
            '# All changes will be lost, see Projectfile.',
            '#',
            '# Updated at ' + six.text_type(datetime.datetime.now()),
            '',
        ]

        if len(self):
            for k, v in self:
                v = textwrap.dedent(str(v)).strip()
                v = v.replace('\n', ' \\\n' + ' ' * (len(k) + 4))
                content.append('{} {} {}'.format(k, self._env_assignment_operators.get(k, '?='), v))
            content.append('')

        if len(self.phony):
            content.append('.PHONY: ' + ' '.join(sorted(self.phony)))
            content.append('')

        for target, details in self.targets:
            deps, rule, doc = details
            if doc:
                for line in doc.split('\n'):
                    content.append('# ' + line)
            content.append('{}: {}'.format(target, ' '.join(deps)).strip())

            script = textwrap.dedent(str(rule)).strip()

            for line in script.split('\n'):
                content.append('\t' + line)

            content.append('')

        return '\n'.join(content)

    def add_target(self, target, rule, deps=None, phony=False, first=False, doc=None):
        if target in self._target_order:
            raise RuntimeError('Duplicate definition for make target «{}».'.format(target))

        if isinstance(rule, str):
            rule = Script(rule)

        self._target_values[target] = (deps or list(), rule, textwrap.dedent(doc or '').strip(), )
        self._target_order.appendleft(target) if first else self._target_order.append(target)

        if phony:
            self.phony.add(target)

    def get_target(self, target):
        return self._target_values[target][1]

    def set_deps(self, target, deps=None):
        self._target_values[target] = (deps or list(), self._target_values[target][1], self._target_values[target][2], )

    def set_assignment_operator(self, key, value):
        assert value in ('?=', '=', '+=', ':=', '::=', '!='), 'Invalid operator'
        self._env_assignment_operators[key] = value

    def setleft(self, key, value):
        self._env_values[key] = value
        if not key in self._env_order:
            self._env_order.appendleft(key)

    def updateleft(self, *lst):
        for key, value in reversed(lst):
            self.setleft(key, value)


class MakefileEvent(Event):
    def __init__(self, package_name, makefile):
        self.package_name = package_name
        self.makefile = makefile
        super(MakefileEvent, self).__init__()


class InstallScript(Script):
    def __init__(self, script=None):
        super(InstallScript, self).__init__(script)

        self.before_install = []
        self.install = self.script
        self.after_install = []

    def __iter__(self):
        yield 'if [ -z "$(QUICK)" ]; then \\'
        for line in map(
            lambda x: '    {} ; \\'.format(x), itertools.chain(self.before_install, self.install, self.after_install)
        ):
            yield line
        yield 'fi'


class CleanScript(Script):
    remove = [
        'build',
        'dist',
        '*.egg-info',
    ]

    def __iter__(self):
        yield 'rm -rf {}'.format(' '.join(self.remove))


class MakeFeature(Feature):
    class Config(Feature.Config):
        def __init__(self):
            pass

    def configure(self):
        self.makefile = Makefile()

    @subscribe('medikit.on_start', priority=HIGH_PRIORITY)
    def on_start(self, event):
        """
        :param ProjectEvent event:
        """
        for k in event.variables:
            self.makefile[k.upper()] = event.variables[k]

        self.makefile.updateleft(
            ('QUICK', '', ),
        )

        self.makefile.add_target(
            'install', InstallScript(), phony=True, doc='''Installs the local project dependencies.'''
        )
        self.makefile.add_target(
            'install-dev',
            InstallScript(),
            phony=True,
            doc='''Installs the local project dependencies, including development-only libraries.'''
        )
        self.makefile.add_target('clean', CleanScript(), phony=True, doc='''Cleans up the local mess.''')

        self.dispatcher.dispatch(__name__ + '.on_generate', MakefileEvent(event.setup['name'], self.makefile))

        self.render_file_inline('Makefile', self.makefile.__str__(), override=True)


__feature__ = MakeFeature
