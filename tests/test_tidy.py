import json
from unittest import TestCase
from enwarlib.tidy import *
from textwrap import dedent


class TidyTest(TestCase):

    def _ev(self, name, value, sort_group=1):
        return {
            'name': name,
            'value': value,
            'sort_group': sort_group,
        }

    def _evs_to_dict(self, evs):
        return dict(
            (ev['name'], ev)
            for ev in evs)

    def setUp(self):
        self.analysis_data = {
            'versions': [
                {'environment_variables': [
                    self._ev(
                        'PATH',
                        '$PROGRAM_PATH/asdf/bin',
                        99),
                    self._ev(
                        'LD_LIBRARY_PATH',
                        '$PROGRAM_PATH/asdf/lib',
                    ),
                    self._ev('SOMEVAR', 'SOMEVAL', 10),
                    self._ev('EXTVAR', 'EXTVAL:$SOMEVAR', 2),
                    self._ev('SHAMPOO', 'factor1', 2),
                    self._ev('CONDITIONER', 'factor99', 2),
                    self._ev(
                        'FORMULA',
                        '$(echo $(( SHAMPOO + CONDITIONER )) ):whatever',
                        2),
                ]}
            ]
        }

    def test_parse_json_array(self):
        json_input = json.dumps(
            self.analysis_data['versions'][0]['environment_variables'])
        input_array = json.loads(json_input)
        cleaned_evs = clean_special_vars(tidy_sort_groups(input_array))
        evdict = self._evs_to_dict(cleaned_evs)
        self.assertEqual(
            evdict['EXTVAR']['sort_group'],
            evdict['SOMEVAR']['sort_group'] + 1,
        )

    def test_parse_bash_expression(self):
        bash_expression_exports = dedent('''\
            export SOMEVAR=SOMEVAL
            export SHAMPOO=factor1
            export CONDITIONER=factor99
            export EXTVAR=EXTVAL:$SOMEVAR
            export FORMULA=$(echo $(( SHAMPOO + CONDITIONER )) ):whatever
            export PATH=$PATH:$PROGRAM_PATH/asdf/bin
            export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PROGRAM_PATH/asdf/lib
            ''')
        input_array = from_bash_expression(bash_expression_exports)
        cleaned_evs = clean_special_vars(tidy_sort_groups(input_array))
        evdict_from_exports = self._evs_to_dict(cleaned_evs)
        self.assertEqual(
            evdict_from_exports['EXTVAR']['sort_group'],
            evdict_from_exports['SOMEVAR']['sort_group'] + 1)

        bash_expression_assignment = '\n'.join(
            line[7:]
            for line in bash_expression_exports.splitlines())
        evdict_from_assignments = self._evs_to_dict(
            clean_special_vars(tidy_sort_groups(
                from_bash_expression(bash_expression_assignment)
            ))
        )
        self.assertDictEqual(evdict_from_exports,
                             evdict_from_assignments)
