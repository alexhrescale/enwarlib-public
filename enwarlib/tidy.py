import toolz as z
import re
from toposort import toposort
from .parser import BashExpressionParser
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def _is_bash_injection(expression):
    return re.match(r'^\s*"\s*;', expression) \
           and re.match(r'.*=\s*"\s*$', expression)


def tidy_sort_groups(sort_group_envvars, debug_level=0):
    deptree = defaultdict(set)
    current_vars = {}
    for ev in sort_group_envvars:
        ev_name = ev['name']
        ev_value = ev['value']
        current_vars[ev_name] = ev

        if _is_bash_injection(ev_value):
            if debug_level < 10:
                logger.warn('found bash injection: {}={}'.format(
                    ev_name, ev_value,
                ))
            continue

        for var in BashExpressionParser(ev_value).get_variables():
            deptree[ev_name].add(var)

    new_sort_group_mapping = {}
    for topsort_sort_group, parent_vars \
            in enumerate(toposort(deptree), start=1):
        for ev_name in parent_vars:
            if ev_name not in current_vars:
                continue
            new_sort_group_mapping[ev_name] = topsort_sort_group

    new_evs = []
    for ev in sort_group_envvars:
        current_sort_group = ev.get('sort_group')
        ev_name = ev['name']
        new_sort_group = new_sort_group_mapping.get(ev_name, 1)
        if current_sort_group != new_sort_group:
            if debug_level:
                logger.warn('sort_group changed from\t{} to\t{} for\t{}'.format(
                    current_sort_group,
                    new_sort_group,
                    ev_name,
                ))
            new_evs.append(z.assoc(ev, 'sort_group', new_sort_group))
        else:
            new_evs.append(ev)

    return new_evs


def clean_special_vars(evs):
    '''
    strip $PATH and $LD_LIBRARY_PATH prefixes in envvar exports
    '''
    out = []
    for ev in evs:
        ev_name = ev['name']
        if ev_name in ('PATH', 'LD_LIBRARY_PATH'):
            ev_value = re.sub('\\${}:?'.format(ev_name), '', ev['value'])
        else:
            ev_value = ev['value']
        out.append(z.assoc(ev, 'value', ev_value))
    return out


def from_bash_expression(expression):
    vars = []
    for line in expression.splitlines():
        maybe_match = re.match(
            r'^(?:export\s+)?([_a-zA-Z0-9]+)=(\S.*)$',
            line.strip())
        if maybe_match is None:
            continue
        vars.append(dict(
            name=maybe_match.group(1),
            value=maybe_match.group(2),
        ))
    return vars


def to_bash_expression(sort_group_evs, prefix='export '):
    out = []
    for ev in sorted(sort_group_evs,
                     key=lambda ev: (ev.get('sort_group', 1), ev['name'])):
        ev_name = ev['name']
        if ev_name in ('PATH', 'LD_LIBRARY_PATH'):
            ev_value = '${}:{}'.format(ev_name, ev['value'])
        else:
            ev_value = ev['value']
        out.append('{}{}={}'.format(
            prefix or '', ev_name, ev_value))
    return '\n'.join(out)
