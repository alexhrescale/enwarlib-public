from unittest import TestCase
from enwarlib.parser import BashExpressionParser


class ParserTest(TestCase):

    def test_extract_bash_variables_from_expression(self):
        for i, (bash_expression, expected_vars) in enumerate([
            ('ls -l', []),
            ('   $X   ', ['X']),
            ('  $X  $Y  decoy;$z  ', ['X', 'Y', 'z']),
            ('$left:$right:$up:$down;  $high    $low',
             ['left', 'right', 'up', 'down', 'high', 'low']),
            (' echo $(echo $NESTY) ', ['NESTY']),
            ('echo $a $b $c', ['a', 'b', 'c']),
            ('echo $USER', ['USER']),
            ('echo $(( ONE + TWO ))', ['ONE', 'TWO']),
            ('${asdf} ', ['asdf']),
            ('${bat}  ${cat}${hat}_${mat} ', ['bat', 'cat', 'hat', 'mat']),
            ('echo $fee ${fi}${fo}___${fum} ', ['fee', 'fi', 'fo', 'fum']),
            ('echo $(( $three + $Four )) $(cat $someval) '
             '$(echo $(( one + two ))) and more',
             ['three', 'Four', 'someval', 'one', 'two']),
            ('echo $( cat /etc/passwd | wc -l )',
             []),
            ('echo $(( $(cat $(echo /etc/passwd) | wc -l) * 2 + 3 + BLAH ))',
             ['cat', 'echo', 'etc', 'passwd', 'wc', 'l', 'BLAH']),
            ('if [ "w" == "!" ]; then echo $(date +%F); else echo date +%s; fi',
             []),
            ('echo $(( ONE + TWO + $(echo $foo bar) baz ))',
             ['ONE', 'TWO', 'echo', 'foo', 'bar', 'baz']),
            ('echo $(( ALICE + Bob + $(echo cherry durian) ))',
             ['ALICE', 'Bob', 'echo', 'cherry', 'durian']),
            ('$A;__$b/slash-$DASHDIVIDE-$c', ['A', 'b', 'DASHDIVIDE', 'c']),
        ]):
            parser = BashExpressionParser(bash_expression)
            bash_vars = parser.get_variables()
            self.assertEquals(bash_vars, expected_vars)
