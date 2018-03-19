# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import ssl
import tempfile

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.calliope import display
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import update_manager
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util

import httplib2


class CalliopeTest(util.WithTestTool,
                   cli_test_base.CliTestBase,
                   sdk_test_base.WithOutputCapture):

  def testCLISanity(self):
    """Basic functionality test for CLI mode."""
    self.cli.Execute('command1 --coolstuff'.split())
    self.cli.Execute('sdk2 command2'.split())
    self.AssertOutputContains("""\
        are we cool? True
        filtered context
        trace_email is None
        we cool? False""", normalize_space=True)

  def testFilterOrder(self):
    self.cli.Execute('sdk2 command2'.split())
    self.AssertErrContains('Filter Sdk1\nFilter Sdk2')

  def testBadExecuteInvocationType(self):
    with self.assertRaisesRegexp(ValueError, 'Execute expects an iterable'):
      self.cli.Execute('foo bar')

  def testNonAsciiNotAllowed(self):
    """Test non-ascii character detection."""
    with self.assertRaisesRegexp(
        calliope_exceptions.InvalidCharacterInArgException,
        'Failed to read command line argument'):
      self.cli.Execute(u'command1 --format=Ṳᾔḯ¢◎ⅾℯ'.split())
    self.AssertErrContains("""\
Failed to read command line argument [--format=\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f] because it does not appear to be valid 7-bit ASCII.

test command1 --format=\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f
                       ^ invalid character""")

  def testIgnoreBroken(self):
    """Test to make sure that groups with errors don't kill everything."""
    # We can run a command ok.
    self.cli.Execute('sdk2 command2'.split())
    # If we load everything, we can see there is a broken command in there.
    with self.assertRaisesRegexp(
        command_loading.CommandLoadFailure,
        r"Problem loading test.broken-sdk.broken\: name 'asd' is not defined."):
      self.cli._TopElement().LoadAllSubElements(recursive=True)

  def testLoadingCount(self):
    """Test to make sure that groups with errors don't kill everything."""
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk5'))
    loader.AddModule('broken_sdk', os.path.join(self.calliope_test_home,
                                                'broken_sdk'))
    cli = loader.Generate()
    self.assertEqual(
        3, cli._TopElement().LoadAllSubElements(recursive=True,
                                                ignore_load_errors=True))

  def testBrokenLoadAll(self):
    """Test that we see an error if we disable lazy load of commands."""
    properties.VALUES.core.disable_command_lazy_loading.Set(True)
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.AddModule('broken_sdk', os.path.join(self.calliope_test_home,
                                                'broken_sdk'))
    with self.assertRaisesRegexp(
        command_loading.CommandLoadFailure,
        r"Problem loading test.broken-sdk.broken\: name 'asd' is not defined."):
      loader.Generate()

  def testBrokenRequiredCategory(self):
    """Test that a flag with category='REQUIRED' is an error."""
    properties.VALUES.core.disable_command_lazy_loading.Set(True)
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.AddModule('broken_required', os.path.join(self.calliope_test_home,
                                                     'broken_required'))
    with self.assertRaisesRegexp(
        parser_errors.ArgumentException,
        r"Flag \[--not-really-required\] cannot have category='REQUIRED' in "
        r"command \[test.broken-required.broken\]"):
      loader.Generate()

  def testBrokenRequiredWithCategory(self):
    """Test that a required flag with category=something is an error."""
    properties.VALUES.core.disable_command_lazy_loading.Set(True)
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.AddModule('broken_required_category',
                     os.path.join(self.calliope_test_home,
                                  'broken_required_category'))
    with self.assertRaisesRegexp(
        parser_errors.ArgumentException,
        r'Required flag \[--required-with-category\] cannot have a category in '
        r'command \[test\.broken-required-category\.broken\]'):
      loader.Generate()

  def testRequiredArgs(self):
    """Test that not providing required arguments is an error."""
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    errors_mock = self.StartObjectPatch(metrics, 'Error')

    with self.AssertRaisesArgumentErrorMatches(
        'argument --some_required_arg: Must be specified.'):
      self.cli.Execute('requiredargcommand'.split())
    self.ClearErr()
    self.assertEqual(2, commands_mock.call_count)
    self.assertEqual(2, errors_mock.call_count)
    _, commands_kwargs = commands_mock.call_args_list[0]
    self.assertIn('RequiredError', str(commands_kwargs['error']))

    self.ClearErr()
    with self.AssertRaisesArgumentErrorMatches(
        'argument --some_required_arg: Must be specified.'):
      self.cli.Execute('sdk2 requiredargcommand'.split())
    self.ClearErr()

    self.assertEqual(4, commands_mock.call_count)
    self.assertEqual(4, errors_mock.call_count)
    _, commands_kwargs = commands_mock.call_args_list[2]
    self.assertIn('RequiredError', str(commands_kwargs['error']))

  def testUnexpectedArgs(self):
    """Test that providing extra arguments is an error."""
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    errors_mock = self.StartObjectPatch(metrics, 'Error')

    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --bogus-arg=junk'):
      self.cli.Execute('command1 --bogus-arg=junk'.split())

    self.assertEqual(2, commands_mock.call_count)
    self.assertEqual(2, errors_mock.call_count)
    commands_args, commands_kwargs = commands_mock.call_args_list[0]
    self.assertIn('UnrecognizedArgumentsError', str(commands_kwargs['error']))
    self.assertEquals('test.command1', str(commands_args[0]))

  def testUnexpectedArgs2(self):
    """Test that providing extra arguments is an error."""
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --bogus-arg=junk'):
      self.cli.Execute('sdk2 --bogus-arg=junk'.split())

  def testUnexpectedArgs3(self):
    """Test that providing extra arguments is an error."""
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --bogus-arg=junk'):
      self.cli.Execute('--bogus-arg=junk'.split())

  def testUnexpectedArgs4(self):
    """Test that extra arguments print help for deepest triggered parser."""
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: unexpected'):
      self.cli.Execute('sdk2 lotsofargs --group-required-test=0 '
                       'test --command-required-test=0 '
                       'positional unexpected'. split())
    self.AssertErrContains('Usage: test sdk2 lotsofargs test')

  def testMetricsResetBetweenCommands(self):
    """Test that metrics flag arg collection resets between commands."""
    commands_mock = self.StartObjectPatch(metrics, 'Commands')

    self.cli.Execute('command1 --coolstuff'.split())
    commands_args = commands_mock.call_args_list[0][0][2]
    self.assertEquals(['--coolstuff'], commands_args)

    self.cli.Execute('command1'.split())
    commands_args = commands_mock.call_args_list[1][0][2]
    self.assertEquals([], commands_args)

    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --bogus-arg=junk'):
      self.cli.Execute('command1 --coolstuff --bogus-arg=junk'.split())
    commands_args = commands_mock.call_args_list[2][0][2]
    self.assertEquals(['--coolstuff'], commands_args)

  def testToolExceptions(self):
    """Test that any ToolExceptions thrown by Run() are given to Display()."""
    with self.assertRaisesRegexp(
        calliope_exceptions.ToolException,
        r"\('noarg', 'no reason'\)"):
      self.cli.Execute('exceptioncommand'.split())

  def testGoofyArgs(self):
    self.cli.Execute('sdk2 lotsofargs --group-not-required-test=2 '
                     '--group-required-test=1 test '
                     '--command-not-required-test=4 --command-required-test=3 6'
                     .split())
    self.AssertOutputContains('warning\n1\n2\n3\n4\n4\nNone\n6',
                              normalize_space=True)

  def testGoofyArgs2(self):
    self.cli.Execute(
        ('sdk2 '
         'lotsofargs --group-required-test=1 --group-not-required-test=2 '
         'test --command-required-test=3 --command-not-required-test=4 6'
        ).split())

    self.AssertOutputContains('warning\n1\n2\n3\n4\n4\nNone\n6',
                              normalize_space=True)

  def testGoofyArgsNoAbbreviatedLeaf(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --command-not=4 (did you mean "
        "'--command-not-required-test'?)"):
      self.cli.Execute(
          'sdk2 --verbo=info lotsofargs --group-required-test=1 test '
          '--command-required-test=3 --command-not=4 6'.split())

  def testGoofyArgsNoAbbreviatedRoot(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --verbo=info (did you mean '--verbosity'?)"):
      self.cli.Execute(
          'sdk2 --verbo=info lotsofargs --group-required-test=1 test '
          '--command-required-test=3 --command-not-required-test=4 6'.split())

  def testGoofyArgsNoAbbreviatedRequiredPrecedenceLeafAbbrev(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --command-not=4 (did you mean "
        "'--command-not-required-test'?)"):
      self.cli.Execute(
          'sdk2 --verbo=info lotsofargs --group-required=1 test '
          '--command-required-test=3 --command-not=4 6'.split())
    self.AssertErrContains("""\
(test.sdk2.lotsofargs.test) unrecognized arguments: --command-not=4 (did you mean '--command-not-required-test'?)
""")

  def testGoofyArgsNoAbbreviatedRequiredPrecedence(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --group-required=1 (did you mean "
        "'--group-required-test'?)"):
      self.cli.Execute(
          'sdk2 --verbo=info lotsofargs --group-required=1 test '
          '--command-required-test=3 --command-not-required-test=4 6'.split())

  def testGoofyArgsNoAbbreviatedRequiredPrecedenceRootAbbrev(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --verbo=info (did you mean '--verbosity'?"):
      self.cli.Execute(
          'sdk2 --verbo=info lotsofargs --group-required-test=1 test '
          '--command-required-test=3 --command-not-required-test=4 6'.split())
    self.AssertErrContains("""\
(test.sdk2) unrecognized arguments: --verbo=info (did you mean '--verbosity'?)
""")

  def testGoofyArgsRequiredPrecedenceNoPositional(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument POSITIONAL: Must be specified.'):
      self.cli.Execute(
          'sdk2 lotsofargs --group-required-test=1 test '
          '--command-required-test=3 --command-not-required-test=4'.split())

  def testGoofyArgsRequiredPrecedenceNoEqualsNoPositional(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument POSITIONAL: Must be specified.'):
      self.cli.Execute(
          'sdk2 lotsofargs --group-required-test 1 test '
          '--command-required-test 3 --command-not-required-test 4'.split())

  def testGoofyArgsRequiredPrecedenceUnknownNoEqualsNoPositional(self):
    with self.AssertRaisesArgumentErrorMatches("""\
unrecognized arguments:
  --unknown
  --foobar (did you mean '--format'?)"""):
      self.cli.Execute(
          'sdk2 lotsofargs --group-required-test 1 test '
          '--command-required-test 3 --unknown --foobar 4'.split())

  def testGoofyArgsUnknownKnownUnknown(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments:\n  --bar=foo\n  --zap=bar'):
      self.cli.Execute(
          'sdk2 lotsofargs --bar=foo --group-required-test=1 --zap=bar test '
          '--command-required-test=3 6'.split())

  def testGoofyArgsNoPositional(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument POSITIONAL --command-required-test --group-required-test: '
        'Must be specified.'):
      self.cli.Execute(
          'sdk2 lotsofargs test'.split())

  def testModalGroupOnlyOptional(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --optional-value: --required --required-as-well '
        'must be specified.'):
      self.cli.Execute(
          'sdk2 modal-group --optional-value=VAL'.split())

  def testModalGroupRequiredMissingWithOptional(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument [--required : --optional-value]: '
        '--required-as-well must be specified.'):
      self.cli.Execute(
          'sdk2 modal-group --required --optional-value=VAL'.split())

  def testModalGroupRequiredMissingNoOptional(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --required: --required-as-well must be specified.'):
      self.cli.Execute(
          'sdk2 modal-group --required'.split())

  def testModalGroupAllRequiredNoneSpecified(self):
    self.cli.Execute(
        'sdk2 modal-group'.split())

  def testModalGroupAllRequiredOneSpecified(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --required-two: Must be specified.'):
      self.cli.Execute(
          'sdk2 modal-group --required-one'.split())

  def testModalGroupAllRequiredAllSpecified(self):
    self.cli.Execute(
        'sdk2 modal-group --required-one --required-two'.split())

  def testNestedGroupsModalMissing(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --vpn-tunnel-region: --vpn-tunnel must be specified.'):
      self.cli.Execute(
          'sdk2 nested-groups --vpn-tunnel-region=VTR'.split())

  def testNestedGroupsModalNonModalMisMatch(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --vpn-tunnel-region: --vpn-tunnel must be specified.'):
      self.cli.Execute(
          'sdk2 nested-groups --interconnect-attachment=IA '
          '--vpn-tunnel-region=VTR'.split())

  def testNestedGroupsNonModalNonModalMisMatch(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --interconnect-attachment-region: --interconnect-attachment '
        'must be specified.'):
      self.cli.Execute(
          'sdk2 nested-groups --interconnect-attachment-region=IAR '
          '--vpn-tunnel-region=VTR'.split())

  def testNestedGroupsMutexConflict(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument [--interconnect-attachment : '
        '--interconnect-attachment-region]: At most one of '
        '[--interconnect-attachment : --interconnect-attachment-region] | '
        '[--vpn-tunnel : --vpn-tunnel-region] may be specified.'):
      self.cli.Execute(
          'sdk2 nested-groups --vpn-tunnel=VT '
          '--interconnect-attachment=IA'.split())

  def testNestedGroupsFlagsError(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --def --jkl (--pqr --pqr-sib) (--vwx --vwx-sib): '
        'Must be specified.'):
      self.cli.Execute('sdk2 nested-groups'.split())

  def testNestedGroupsFlags(self):
    self.cli.Execute(
        'sdk2 nested-groups --def=1 --pqr=2 --jkl=3 --vwx=4'.split())
    self.AssertOutputContains("""\
abc-00: false
abc-01: false
abc-10: true
abc-11: true
interconnect-attachment: null
interconnect-attachment-region: null
vpn-tunnel: null
vpn-tunnel-region: null
xyz-00: false
xyz-01: true
xyz-10: false
xyz-11: true
""")
    self.AssertErrContains("""\
Filter Sdk1
Filter Sdk2
""")

  def testNestedGroupsHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 nested-groups --help'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 nested-groups - a command with nested argument group combinations

SYNOPSIS
    test sdk2 nested-groups --def=DEF --jkl=JKL (--pqr=PQR --pqr-sib=PQR_SIB)
        (--vwx=VWX --vwx-sib=VWX_SIB) [--abc=ABC] [--ghi=GHI]
        [--abc-00 | --xyz-00] [--abc-01 | --no-xyz-01]
        [[--interconnect-attachment=INTERCONNECT_ATTACHMENT
          : --interconnect-attachment-region=INTERCONNECT_ATTACHMENT_REGION]
          | [--vpn-tunnel=VPN_TUNNEL : --vpn-tunnel-region=VPN_TUNNEL_REGION]]
        [--mno=MNO --mno-sib=MNO_SIB]
        [--mode : --meh=MEH --optional-value=OPTIONAL_VALUE]
        [--no-abc-10 | --xyz-10] [--no-abc-11 | --no-xyz-11]
        [--stu=STU | --stu-sib=STU_SIB] [TEST_WIDE_FLAG ...]

DESCRIPTION
    A command with nested argument group combinations.

REQUIRED FLAGS
     --def=DEF
        DEF help text.

     --jkl=JKL
        JKL help text.

     Test 012. At least one of these must be specified:

       --pqr=PQR
          PQR help text.

       --pqr-sib=PQR_SIB
          PQR sib help text.

     Test 112. At least one of these must be specified:

       --vwx=VWX
          VWX help text.

       --vwx-sib=VWX_SIB
          VWX sib help text.

OPTIONAL FLAGS
     --abc=ABC
        ABC help text.

     --ghi=GHI
        GHI help text.

     Group 00 flags. At most one of these may be specified:

       --abc-00
          ABC 00 help text.

       --xyz-00
          XYZ 00 help text.

     Group 01 flags. At most one of these may be specified:

       --abc-01
          ABC 01 help text.

       --xyz-01
          XYZ 01 help text. Enabled by default, use --no-xyz-01 to disable.

     Router interface flags. At most one of these may be specified:

       Interconnect attachment flags.

         --interconnect-attachment=INTERCONNECT_ATTACHMENT
            Interconnect attachment help. This flag must be specified if any of
            the other arguments in this group are specified.

         --interconnect-attachment-region=INTERCONNECT_ATTACHMENT_REGION
            Interconnect attachment region help.

       VPN tunnel flags.

         --vpn-tunnel=VPN_TUNNEL
            VPN tunnel help. This flag must be specified if any of the other
            arguments in this group are specified.

         --vpn-tunnel-region=VPN_TUNNEL_REGION
            VPN tunnel region help.

     Test 002.

       --mno=MNO
          MNO help text.

       --mno-sib=MNO_SIB
          MNO sib help text.

     Modal group test.

       --mode
          Set the mode. This flag must be specified if any of the other
          arguments in this group are specified.

       --meh=MEH
          Meh if you want.

       --optional-value=OPTIONAL_VALUE
          Optional mode value.

     Group 10 flags. At most one of these may be specified:

       --abc-10
          ABC 10 help text. Enabled by default, use --no-abc-10 to disable.

       --xyz-10
          XYZ 10 help text.

     Group 11 flags. At most one of these may be specified:

       --abc-11
          ABC 11 help text. Enabled by default, use --no-abc-11 to disable.

       --xyz-11
          XYZ 11 help text. Enabled by default, use --no-xyz-11 to disable.

     Test 102. At most one of these may be specified:

       --stu=STU
          STU help text.

       --stu-sib=STU_SIB
          STU sib help text.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity. Run $ test help for details.

NOTES
    This variant is also available:

        $ test beta sdk2 nested-groups
""")

  def testGroupButNoCommand(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'sdk2'.split())
    self.AssertErrContains("""\
(test.sdk2) Command name argument expected.
""")

  def testUseArgBeforeParserThatDefinesItWIthEquals(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --zone=foo'):
      self.cli.Execute(
          'sdk2 --zone=foo command2'.split())

  def testUseArgBeforeParserThatDefinesItWIthSpace(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --zone'):
      self.cli.Execute(
          'sdk2 --zone foo command2'.split())

  def testGlobalFlagShorterNotAbbreviation(self):
    self.cli.Execute('sdk2 lotsofargs --group-required-test=1 test '
                     '--command-required-test=3 '
                     '--config=5 6'.split())
    self.AssertOutputContains('warning\n1\nNone\n3\nNone\nNone\n5\n6',
                              normalize_space=True)

  def testUnderscores(self):
    self.cli.Execute('compound-group compound-command'.split())
    self.AssertOutputContains('Under!')

  def testNonExistingModules(self):
    with self.assertRaises(command_loading.LayoutException):
      loader = calliope.CLILoader(
          name='test',
          command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
      loader.AddModule('notthere', os.path.join(self.calliope_test_home,
                                                'notthere'))
      loader.Generate()

    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'),
        allow_non_existing_modules=True)
    loader.AddModule('notthere', os.path.join(self.calliope_test_home,
                                              'notthere'))
    loader.Generate()

  def testHooks(self):
    called = []
    def Func(called):
      def Inner(command_path, **unused_kwargs):
        called.append(command_path)
      return Inner
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.RegisterPreRunHook(Func(called))
    loader.RegisterPostRunHook(Func(called))
    loader.RegisterPreRunHook(Func(called), include_commands='nonsense')
    loader.RegisterPostRunHook(Func(called), include_commands='nonsense')
    loader.RegisterPreRunHook(Func(called),
                              exclude_commands='.*requiredargcommand.*')
    loader.RegisterPostRunHook(Func(called),
                               exclude_commands='.*requiredargcommand.*')
    loader.Generate().Execute(
        'requiredargcommand --some_required_arg=foo'.split())
    self.assertEqual(called, ['test.requiredargcommand',
                              'test.requiredargcommand'])

  def testNewStyle(self):
    self.assertEqual(self.cli.Execute('newstylecommand --flag=6'.split()), 5)
    self.cli.Execute('newstylecommand --flag=6'.split())
    self.cli.Execute('newstylegroup subcommand --flag=6'.split())

  def testSimilarToolsDirectory(self):
    self.assertEqual(self.cli.Execute(['sdk3', 'nested']), 'nested')
    self.assertEqual(self.cli.Execute(
        ['newstylegroup', 'subcommand', '--flag=6']), 5)
    self.assertEqual(
        self.cli.Execute(['sdk3', 'newstylegroup', 'subcommand', '--flag=6']),
        7)

  def testMutuallyExclusiveGroupCLI(self):
    self.cli.Execute('mutex-command --flag1a --flag2a'.split())
    self.AssertOutputContains('True\nFalse\nTrue\nFalse')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --flag1a: At most one of --flag1a | --flag1b may be '
        'specified.'):
      self.cli.Execute('mutex-command --flag1a --flag1b'.split())

  def testMutuallyExclusiveGroupAPI(self):
    self.cli.Execute(['mutex-command', '--flag1a', '--flag2a'])
    self.AssertOutputContains('True\nFalse\nTrue\nFalse')
    with self.AssertRaisesArgumentErrorMatches(
        'argument --flag2a: At most one of --flag2a | '
        '--flag2b may be specified.'):
      self.cli.Execute(['mutex-command', '--flag2a', '--flag2b'])

  def testExitCodes(self):
    try:
      self.cli.Execute(['exit2'])
    except calliope_exceptions.ToolException as e:
      self.assertEqual(str(e), 'Get outta here!')
      self.assertEqual(e.exit_code, 2)
    self.AssertErrContains('ERROR:')
    self.AssertOutputNotContains('EXIT2-DISPLAY')

  def testExitNoError(self):
    mocked_exit = self.StartObjectPatch(calliope_exceptions, '_Exit')

    self.cli.Execute(['exit2', '--no-error'])

    self.assertNotEqual(mocked_exit.call_args, None)
    self.assertEqual(mocked_exit.call_args[0][0].exit_code, 2)
    self.AssertErrNotContains('ERROR:')
    self.AssertOutputContains('EXIT2-DISPLAY')

  def testKnownErrorMessageSuffix(self):
    def RaiseSSLError(command_path):
      raise ssl.SSLError('SSL Err in {0}!'.format(command_path))

    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.RegisterPostRunHook(RaiseSSLError)
    cli = loader.Generate()

    self.StartObjectPatch(calliope_exceptions, '_Exit')

    # `help` and `--help` now hit the same code which bypasses cli.Execute().
    with self.assertRaisesRegexp(SystemExit, '0'):
      cli.Execute(['--help'])
    self.AssertErrNotContains(exceptions.NetworkIssueError('').message)
    with self.assertRaisesRegexp(SystemExit, '0'):
      cli.Execute(['help'])
    self.AssertErrNotContains(exceptions.NetworkIssueError('').message)

  def testUsage(self):
    with self.AssertRaisesArgumentErrorMatches(
        "Invalid choice: 'sdk1'. Did you mean 'sdk11'?"):
      self.cli.Execute('sdk1 cfg'.split())
    self.AssertErrContains("""\
ERROR: (test) Invalid choice: 'sdk1'. Did you mean 'sdk11'?
Usage: test [optional flags] <group | command>
  group may be           beta | broken-sdk | cfg | compound-group |
                         newstylegroup | sdk11 | sdk2 | sdk3 | sdk7
  command may be         command1 | dict-list | exceptioncommand | exit2 |
                         help | implementation-args | loggingcommand |
                         mutex-command | newstylecommand | recommand |
                         requiredargcommand | simple-command |
                         static-recommand | unsetprop

For detailed information on this command and its flags, run:
  test --help
""")

  def testNestingCommands(self):
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.AddModule('newstylegroup.sdk2',
                     os.path.join(self.calliope_test_home, 'sdk2'))
    cli = loader.Generate()
    cli.Execute('newstylegroup sdk2 command2'.split())

  def testParentFlags(self):
    with tempfile.NamedTemporaryFile() as f:
      f.write('{}')
      f.close()
      loader = calliope.CLILoader(
          name='test',
          command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
      cli = loader.Generate()
      # Flags trickle down
      cli.Execute('cfg set --key=john --value=fun'.split())
      cli.Execute('cfg get --key=john'.split())
      # But not up
      with self.AssertRaisesArgumentErrorMatches(
          'unrecognized arguments: --value=fun'):
        cli.Execute('cfg --value=fun set --key=john'.split())

  def testDeepNestingCommands(self):
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.AddModule('newstylegroup.anothergroup.sdk2',
                     os.path.join(self.calliope_test_home, 'sdk2'))
    cli = loader.Generate()
    cli.Execute('newstylegroup anothergroup sdk2 command2'.split())

  def testDeepNestingWithCommands(self):
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'))
    loader.AddModule('newstylegroup.anothergroup.sdk2',
                     os.path.join(self.calliope_test_home, 'sdk2'))
    loader.AddModule('newstylegroup.anothergroup.command2',
                     os.path.join(self.calliope_test_home,
                                  'sdk2', 'command2.py'))

    cli = loader.Generate()
    cli.Execute('newstylegroup anothergroup sdk2 command2'.split())
    cli.Execute('newstylegroup anothergroup command2'.split())
    cli.Execute('newstylegroup anothergroup subcommand'.split())

  def testStaticRedirectCommands(self):
    self.cli.Execute(['static-recommand'])
    self.AssertOutputContains("""\
        are we cool? True
        filtered context
        trace_email is None
        Done!""", normalize_space=True)

  def testRedirectCommands(self):
    self.cli.Execute(['recommand'])
    self.AssertOutputContains("""\
        are we cool? True
        filtered context
        trace_email is None
        Done!""", normalize_space=True)

  def testRemainder(self):
    self.cli.Execute('sdk2 remainder'.split())
    self.cli.Execute('sdk2 remainder -- 1 2 3'.split())
    self.cli.Execute('sdk2 remainder -- --flag1 1 2 3'.split())
    self.AssertOutputContains("""\
None
['1', '2', '3']
['--flag1', '1', '2', '3']
""")

  def testSuggest(self):
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    errors_mock = self.StartObjectPatch(metrics, 'Error')

    with self.AssertRaisesArgumentErrorMatches(
        "Invalid choice: 'mutex-commanda'. Did you mean 'mutex-command'?"):
      self.cli.Execute(['mutex-commanda'])

    self.assertEqual(2, commands_mock.call_count)
    self.assertEqual(2, errors_mock.call_count)
    _, commands_kwargs = commands_mock.call_args_list[0]
    self.assertIn('UnknownCommandError', str(commands_kwargs['error']))
    expected = ({'suggestions': ['mutex-command'], 'total_suggestions': 1,
                 'total_unrecognized': 1})
    self.assertEqual(expected, commands_kwargs['error_extra_info'])
    self.assertEqual(0, self.known_error_handler.call_count)

  def testSuggestSynonym(self):
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    errors_mock = self.StartObjectPatch(metrics, 'Error')

    with self.AssertRaisesArgumentErrorMatches(
        "Invalid choice: 'describe'. Did you mean 'get'?"):
      self.cli.Execute(['cfg', 'describe'])

    self.assertEqual(2, commands_mock.call_count)
    self.assertEqual(2, errors_mock.call_count)
    _, commands_kwargs = commands_mock.call_args_list[0]
    self.assertIn('UnknownCommandError', str(commands_kwargs['error']))
    expected = ({'suggestions': ['get'], 'total_suggestions': 1,
                 'total_unrecognized': 1})
    self.assertEqual(expected, commands_kwargs['error_extra_info'])
    self.assertEqual(0, self.known_error_handler.call_count)

  def testSuggestCommandAlias(self):
    with self.AssertRaisesArgumentErrorMatches(
        "Invalid choice: 'foo'. Did you mean 'test sdk2 somethingelse'?"):
      self.cli.Execute(['sdk7', 'foo'])
    with self.AssertRaisesArgumentErrorMatches(
        "Invalid choice: 'bar'. Did you mean 'test sdk7 somethingelse'?"):
      self.cli.Execute(['sdk7', 'bar'])

  def testSuggestAlternateTrack(self):
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    errors_mock = self.StartObjectPatch(metrics, 'Error')

    self._loader.AddReleaseTrack(
        calliope_base.ReleaseTrack.ALPHA,
        os.path.join(self.calliope_test_home, 'alpha'))
    self.cli = self._loader.Generate()
    with self.AssertRaisesArgumentErrorMatches("""\
Invalid choice: 'requiredargcommand'.
This command is available in one or more alternate release tracks.  Try:
  test sdk2 requiredargcommand"""):
      self.cli.Execute(['alpha', 'sdk2', 'requiredargcommand'])

    self.assertEqual(2, commands_mock.call_count)
    self.assertEqual(2, errors_mock.call_count)
    _, commands_kwargs = commands_mock.call_args_list[0]
    self.assertIn('WrongTrackError', str(commands_kwargs['error']))
    expected = {'suggestions': ['test sdk2 requiredargcommand']}
    self.assertEqual(expected, commands_kwargs['error_extra_info'])
    self.assertEqual(0, self.known_error_handler.call_count)

  def testSuggestAlternateTrackDoNotSuggestHidden(self):
    """Tests that hidden commands in alternate tracks aren't suggested."""
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    errors_mock = self.StartObjectPatch(metrics, 'Error')

    self._loader.AddReleaseTrack(
        calliope_base.ReleaseTrack.ALPHA,
        os.path.join(self.calliope_test_home, 'alpha'))
    self.cli = self._loader.Generate()
    with self.AssertRaisesArgumentErrorMatches("Invalid choice: 'hidden'"):
      self.cli.Execute(['alpha', 'sdk2', 'hidden'])

    self.AssertErrNotContains('This command is available in one or more '
                              'alternate release tracks.  Try:')
    self.assertEqual(2, commands_mock.call_count)
    self.assertEqual(2, errors_mock.call_count)
    _, commands_kwargs = commands_mock.call_args_list[0]
    self.assertNotIn('WrongTrackError', str(commands_kwargs['error']))
    self.assertEqual(0, self.known_error_handler.call_count)

  def testMissingComponent(self):
    update_mock = self.StartObjectPatch(update_manager.UpdateManager,
                                        'EnsureInstalledAndRestart')
    with self.AssertRaisesArgumentErrorMatches(
        "Invalid choice: 'does-not-exist'."):
      self.cli.Execute(['does-not-exist'])
    update_mock.assert_called_once_with(
        ['does_not_exist'],
        msg='You do not currently have this command group installed.  Using it '
        'requires the installation of components: [does_not_exist]')

  def testSuggestFlag(self):
    with self.AssertRaisesArgumentErrorMatches("""\
unrecognized arguments:
  --ky (did you mean '--key'?)
  --log-https (did you mean '--log-http'?)
  bar"""):
      self.cli.Execute(['cfg', 'set', '--ky', '--log-https', 'foo', 'bar'])
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: "
        "--ky (did you mean '--key'?)"):
      self.cli.Execute(['cfg', 'set', '--ky'])

  def testSuggestFlagWIthLongValue(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --verbo=some-really-long-gibberish (did you "
        "mean '--verbosity'?"):
      self.cli.Execute(['cfg', 'set', '--verbo=some-really-long-gibberish'])
    self.AssertErrContains(
        'ERROR: (test.cfg.set) unrecognized arguments: '
        "--verbo=some-really-long-gibberish (did you mean '--verbosity'?")

  def testSuggestFlagAlias(self):
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --another-value-altertive "
        "(did you mean '--value'?)"):
      self.cli.Execute(['cfg', 'set', '--another-value-altertive'])
    with self.AssertRaisesArgumentErrorMatches(
        "unrecognized arguments: --value-altertive "
        "(did you mean '--value'?)"):
      self.cli.Execute(['cfg', 'set', '--value-altertive'])

  def testErrorMetric(self):
    command_mock = self.StartObjectPatch(metrics, 'Commands')
    error_mock = self.StartObjectPatch(metrics, 'Error')
    with self.assertRaisesRegexp(
        calliope_exceptions.ToolException,
        r"\('noarg', 'no reason'\)"):
      self.cli.Execute(['exceptioncommand'])

    self.assertEqual(1, error_mock.call_count)
    error_mock.assert_called_with(
        'test.exceptioncommand', calliope_exceptions.ToolException,
        [], error_extra_info={'error_code': 2})

    self.assertEqual(1, command_mock.call_count)
    command_mock.assert_called_with(
        'test.exceptioncommand', config.CLOUD_SDK_VERSION, [],
        error=calliope_exceptions.ToolException,
        error_extra_info={'error_code': 2})
    self.assertEqual(1, self.known_error_handler.call_count)

  def testUnknownErrorMetric(self):
    error_mock = self.StartObjectPatch(metrics, 'Error')
    command_mock = self.StartObjectPatch(metrics, 'Commands')
    with self.assertRaises(ValueError):
      self.cli.Execute('exceptioncommand --unknown-error'.split())

    self.assertEqual(1, error_mock.call_count)
    error_mock.assert_called_with(
        'test.exceptioncommand', ValueError, ['--unknown-error'],
        error_extra_info={'error_code': 1})

    self.assertEqual(1, command_mock.call_count)
    command_mock.assert_called_with(
        'test.exceptioncommand', config.CLOUD_SDK_VERSION, ['--unknown-error'],
        error=ValueError, error_extra_info={'error_code': 1})
    self.assertEqual(0, self.known_error_handler.call_count)

  def testHttpErrorMetric(self):
    error_mock = self.StartObjectPatch(metrics, 'Error')
    command_mock = self.StartObjectPatch(metrics, 'Commands')
    with self.assertRaisesRegexp(
        calliope_exceptions.HttpException,
        'Resource not found API reason: some error'):
      self.cli.Execute('exceptioncommand --http-error'.split())

    self.assertEqual(1, error_mock.call_count)
    error_mock.assert_called_with(
        'test.exceptioncommand', calliope_exceptions.HttpException,
        ['--http-error'],
        error_extra_info={'error_code': 1, 'http_status_code': 404})

    self.assertEqual(1, command_mock.call_count)
    command_mock.assert_called_with(
        'test.exceptioncommand', config.CLOUD_SDK_VERSION, ['--http-error'],
        error=calliope_exceptions.HttpException,
        error_extra_info={'error_code': 1, 'http_status_code': 404})
    self.assertEqual(1, self.known_error_handler.call_count)

  def testFlagNameCollection(self):
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    self.cli.Execute('--top-flag foo cfg --key bar set --value baz positional'
                     .split())
    commands_mock.assert_called_with(
        'test.cfg.set', config.CLOUD_SDK_VERSION,
        ['--key', '--top-flag', '--value', 'NOT_USED'])
    self.assertEqual(0, self.known_error_handler.call_count)

  def testFlagNameCollectionMultiPositional(self):
    commands_mock = self.StartObjectPatch(metrics, 'Commands')
    self.cli.Execute(
        '--top-flag foo cfg --key bar set2 --value baz positional another'
        .split())
    commands_mock.assert_called_with(
        'test.cfg.set2', config.CLOUD_SDK_VERSION,
        ['--key', '--top-flag', '--value', 'NOT_USED:2'])

  def testCommandNameInUA(self):
    test_data_dir = self.Resource(
        'tests', 'unit', 'calliope', 'testdata', 'sdk9')
    pkg_root = os.path.join(test_data_dir, 'notice')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    cli = loader.Generate()
    request_mock = self.StartObjectPatch(httplib2.Http, 'request')
    cli.Execute(['http-command'])
    self.assertEqual(1, request_mock.call_count)
    calls = request_mock.call_args_list
    self.assertIn(' command/test.http-command ',
                  calls[0][1]['headers']['user-agent'])


class DisplayInfoTest(util.WithTestTool, sdk_test_base.WithOutputCapture):

  def SetUp(self):

    def _MockDisplayerInit(displayer, command, args, resources=None,
                           display_info=None):
      _ = displayer
      _ = command
      _ = args
      _ = resources
      self.display_info = display_info

    self.StartObjectPatch(display.Displayer, '__init__',
                          side_effect=_MockDisplayerInit)
    self.StartObjectPatch(display.Displayer, 'Display',
                          side_effect=lambda: None)
    self.display_info = None

  def testDisplayInfo(self):
    """Test parser.display_info.Add() precedence bottom > middle > top."""

    self.cli.Execute(['sdk2', 'lotsofargs', '--group-required-test=1',
                      'test', 'foo', '--command-required-test=3'])
    self.assertEqual('table(bot)', self.display_info.format)
    self.assertEqual('bot', self.display_info.aliases['ALL'])
    self.assertEqual('Top', self.display_info.aliases['TOP'])
    self.assertEqual('Mid', self.display_info.aliases['MID'])
    self.assertEqual('Bot', self.display_info.aliases['BOT'])

  def testDisplayInfoFlags(self):
    """Test with _Flags() and no Args()."""

    self.cli.Execute(['sdk2', 'lotsofargs', '--group-required-test=1',
                      'test-flags'])
    self.assertEqual('table(flags)', self.display_info.format)
    self.assertEqual('Flags', self.display_info.aliases['FLAGS'])
    self.assertEqual('flags', self.display_info.aliases['ALL'])
    self.assertEqual('Top', self.display_info.aliases['TOP'])
    self.assertEqual('Mid', self.display_info.aliases['MID'])

  def testDisplayInfoFlagsArgs(self):
    """Test with _Flags() and Args()."""

    self.cli.Execute(['sdk2', 'lotsofargs', '--group-required-test=1',
                      'test-flags-args'])
    self.assertEqual('table(bot)', self.display_info.format)
    self.assertEqual('Flags', self.display_info.aliases['FLAGS'])
    self.assertEqual('bot', self.display_info.aliases['ALL'])
    self.assertEqual('Top', self.display_info.aliases['TOP'])
    self.assertEqual('Mid', self.display_info.aliases['MID'])
    self.assertEqual('Bot', self.display_info.aliases['BOT'])

  def testSpecifiedArgs(self):
    self.cli.Execute(['sdk2', 'lotsofargs', '--group-required-test=1', 'test',
                      'foo', '--command-required-test=2', '--config=3'])
    self.AssertOutputContains("""\
=====
--command-required-test=2
--config=3
--group-required-test=1
POSITIONAL=foo
=====""")


class DescribeTest(util.WithTestTool, sdk_test_base.WithOutputCapture):

  def SetUp(self):
    test_data_dir = self.Resource(
        'tests', 'unit', 'calliope', 'testdata', 'sdk7')
    pkg_root = os.path.join(test_data_dir, 'describers')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    self.cli = loader.Generate()

  def testDescribeCommandDefaultFormat(self):
    """Test for default format of describe command."""

    self.cli.Execute(['describe', '--verbosity=info'])
    self.AssertErrContains('INFO: Display format "default".')

  def testLegacyDescribeCommandDefaultFormat(self):
    """Test for default format of describe command."""

    self.cli.Execute(['legacy-describe', '--verbosity=info'])
    self.AssertErrContains('INFO: Display format "default".')

  def testDescribeCommandUriFlag(self):
    """Test for describe --uri command."""

    self.cli.Execute(['describe', '--verbosity=info', '--uri'])
    self.AssertErrContains('INFO: Display format "value(.)".')
    self.AssertOutputContains('describers/group/uri')


class UnicodeSupportedTest(util.WithTestTool,
                           sdk_test_base.WithOutputCapture):

  def testUnicodeSupportedGroupSupportedCommand(self):
    expected = [u'Ṳᾔḯ¢◎ⅾℯ']
    actual = self.cli.Execute(
        ['sdk7', 'sdk', 'supported', 'certainly', u'--søɨŧɇnłɏ=Ṳᾔḯ¢◎ⅾℯ'])
    self.assertEqual(expected, actual)

  def testUnicodeUnsupportedGroupSupportedCommand(self):
    expected = [u'Ṳᾔḯ¢◎ⅾℯ']
    actual = self.cli.Execute(
        ['sdk7', 'sdk', 'unsupported', 'yes', u'--車=Ṳᾔḯ¢◎ⅾℯ'])
    self.assertEqual(expected, actual)

  def testUnicodeUnsupportedGroupUnsupportedCommand(self):
    with self.assertRaisesRegexp(SystemExit, '1'):
      self.cli.Execute(
          ['sdk7', 'sdk', 'unsupported', 'no', u'--never=Ṳᾔḯ¢◎ⅾℯ'])
    self.AssertErrContains("""\
ERROR: (test.sdk7.sdk.unsupported.no) Failed to read command line argument [--never=\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f] because it does not appear to be valid 7-bit ASCII.

test sdk7 sdk unsupported no --never=\\u1e72\\u1f94\\u1e2f\\xa2\\u25ce\\u217e\\u212f
                                     ^ invalid character
""")

  def testUnicodeSupportedGroupUnknownUnicodeCommand(self):
    self.SetEncoding('utf8')
    with self.assertRaisesRegexp(SystemExit, '2'):
      self.cli.Execute(['sdk7', u'Ṳᾔḯ¢◎ⅾℯ'])
    self.AssertErrContains(u"""\
ERROR: (test.sdk7) Invalid choice: 'Ṳᾔḯ¢◎ⅾℯ'.
Usage: test sdk7 [optional flags] <group>
  group may be           describers | sdk

For detailed information on this command and its flags, run:
  test sdk7 --help
""")


class AllowUnicodeTest(util.WithTestTool, cli_test_base.CliTestBase):

  def testUnicodeSupportedGroupSupportedCommandWithAllowUnicode(self):
    self.AllowUnicode()
    expected = [u'Ṳᾔḯ¢◎ⅾℯ']
    actual = self.cli.Execute(
        ['sdk7', 'sdk', 'supported', 'certainly', u'--søɨŧɇnłɏ=Ṳᾔḯ¢◎ⅾℯ'])
    self.assertEqual(expected, actual)
    self.assertNotEqual(self.enforce_ascii_args_mock, None)
    try:
      self.TearDown()
      self.fail('Delete self.AllowUnicode() assertion error should have '
                'been raised.')
    except AssertionError:
      self.enforce_ascii_args_mock.call_count = 1

  def testUnicodeUnsupportedGroupUnsupportedCommandWithAllowUnicode(self):
    self.AllowUnicode()
    expected = [u'Ṳᾔḯ¢◎ⅾℯ']
    actual = self.cli.Execute(['sdk7', 'sdk', 'unsupported', 'no',
                               u'--never=Ṳᾔḯ¢◎ⅾℯ'])
    self.assertEqual(expected, actual)
    self.assertNotEqual(self.enforce_ascii_args_mock, None)
    self.assertEqual(self.enforce_ascii_args_mock.call_count, 1)


class HelpCommandAndFlagTests(cli_test_base.CliTestBase):

  def testHelpCommandAndFlagEquiv(self):
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run(['help', 'help'])
    self.AssertOutputContains('NAME')
    self.AssertOutputContains('DESCRIPTION')
    self.AssertOutputContains('SYNOPSIS')
    help_command_out = self.GetOutput()

    self.ClearOutput()
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run(['help', '--help'])
    test_out = self.GetOutput()
    self.assertEquals(help_command_out, test_out)

    self.ClearOutput()
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run(['help', 'topic', '--help'])
    test_out = self.GetOutput()
    self.assertEquals(help_command_out, test_out)

    self.ClearOutput()
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run(['help', 'topic', '--help', '--help'])
    test_out = self.GetOutput()
    self.assertEquals(help_command_out, test_out)

  def testHelpTopicCommandAndFlagEquiv(self):
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run(['help', 'topic'])
    self.AssertOutputContains('NAME')
    self.AssertOutputContains('DESCRIPTION')
    self.AssertOutputContains('TOPICS')
    help_command_out = self.GetOutput()

    self.ClearOutput()
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run(['topic', '--help'])
    test_out = self.GetOutput()
    self.assertEquals(help_command_out, test_out)

    self.ClearOutput()
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.Run(['topic', '--help', '--help'])
    test_out = self.GetOutput()
    self.assertEquals(help_command_out, test_out)


class MarkdownTests(sdk_test_base.WithOutputCapture, sdk_test_base.SdkBase):

  def SetUp(self):
    calliope_test_home = self.Resource('tests', 'unit', 'calliope', 'testdata')
    loader = calliope.CLILoader(
        name='gcloud',
        command_root_directory=os.path.join(calliope_test_home, 'sdk3'))
    self.cli = loader.Generate()

  def Execute(self, path):
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.cli.Execute(path + ['--document=style=markdown'])
    self.AssertOutputIsGolden(
        __file__, 'markdown', '_'.join(['gcloud'] + path) + '.md')

  def testMarkdownTop(self):
    self.Execute([])

  def testMarkdownGroup(self):
    self.Execute(['markdown'])

  def testMarkdownCommand(self):
    self.Execute(['markdown', 'markdown-command'])

  def testHiddenGroup(self):
    self.Execute(['hidden-group'])

  def testHiddenCommand(self):
    self.Execute(['hidden-group', 'hidden-command'])

  def testShortHelpMarkdownSections(self):
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.cli.Execute(['markdown', 'markdown-command', '-h'])
    self.AssertOutputNotContains(' ## EXAMPLES ')


class StorePropertyMarkdownTests(sdk_test_base.WithOutputCapture,
                                 sdk_test_base.SdkBase):

  def SetUp(self):
    calliope_test_home = self.Resource('tests', 'unit', 'calliope', 'testdata')
    loader = calliope.CLILoader(
        name='gcloud',
        command_root_directory=os.path.join(calliope_test_home, 'sdk1'))
    self.cli = loader.Generate()

  def Execute(self, path):
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.cli.Execute(path + ['--document=style=markdown'])

  def testStorePropertyMarkdown(self):
    self.Execute(['command1'])
    self.AssertOutputEquals("""\
# GCLOUD_COMMAND1(1)


## NAME

gcloud command1 - test Boolean and StoreProperty flag combinations


## SYNOPSIS

`gcloud command1` [*--boolean-flag-false*] [*--boolean-flag-none*] [*--no-boolean-flag-true*] [*--boolean-property-false-flag-false*] [*--boolean-property-false-flag-none*] [*--boolean-property-false-flag-true*] [*--no-boolean-property-true-flag-false*] [*--no-boolean-property-true-flag-none*] [*--no-boolean-property-true-flag-true*] [*--coolstuff*] [*--trace-email*=_TRACE_EMAIL_] [_GCLOUD_WIDE_FLAG ..._]


## DESCRIPTION

Here are the details: there aren't any.


## FLAGS

*--boolean-flag-false*::

Boolean flag default=false.

*--boolean-flag-none*::

Boolean flag default=none.

*--boolean-flag-true*::

Boolean flag default=true. Enabled by default, use *--no-boolean-flag-true* to disable.

*--boolean-property-false-flag-false*::

Boolean property default=true and flag default=false. Overrides the default *core/log_http* property value for this command invocation.

*--boolean-property-false-flag-none*::

Boolean property default=true and flag default=none. Overrides the default *core/log_http* property value for this command invocation.

*--boolean-property-false-flag-true*::

Boolean property default=true and flag default=true. Overrides the default *core/log_http* property value for this command invocation.

*--boolean-property-true-flag-false*::

Boolean property default=true and flag default=false. Overrides the default *core/user_output_enabled* property value for this command invocation. Use *--no-boolean-property-true-flag-false* to disable.

*--boolean-property-true-flag-none*::

Boolean property default=true and flag default=none. Overrides the default *core/user_output_enabled* property value for this command invocation. Use *--no-boolean-property-true-flag-none* to disable.

*--boolean-property-true-flag-true*::

Boolean property default=true and flag default=true. Overrides the default *core/user_output_enabled* property value for this command invocation. Use *--no-boolean-property-true-flag-true* to disable.

*--coolstuff*::

is your stuff cool?

*--trace-email*=_TRACE_EMAIL_::

trace_email. Overrides the default *core/trace_email* property value for this command invocation.


## GCLOUD WIDE FLAGS

These flags are available to all commands: --configuration, --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled, --verbosity.
Run *$ link:gcloud/help[gcloud help]* for details.


## EXAMPLES

Don't use this example as an example for writing examples.
""")


class DocumentFlagTests(sdk_test_base.WithOutputCapture, sdk_test_base.SdkBase):

  def SetUp(self):
    calliope_test_home = self.Resource('tests', 'unit', 'calliope', 'testdata')
    loader = calliope.CLILoader(
        name='gcloud',
        command_root_directory=os.path.join(calliope_test_home, 'sdk1'))
    self.cli = loader.Generate()

  def Execute(self, path):
    self.cli.Execute(path)

  def testDocumentFlagUnknowdAttribute(self):
    with self.assertRaisesRegexp(SystemExit, '2'):
      self.Execute(['command1', '--document=unknownAttribute=foo'])
    self.AssertErrContains('ERROR: (gcloud.command1) Unknown document '
                           'attribute [unknownAttribute]')


class ReleaseTracksTest(cli_test_base.CliTestBase):

  def _CreateCLI(self):
    calliope_test_home = self.Resource('tests', 'unit', 'calliope', 'testdata')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(calliope_test_home, 'sdk1'),
        allow_non_existing_modules=False)
    loader.AddModule('sdk2', os.path.join(calliope_test_home, 'sdk2'))
    loader.AddModule('sdk3', os.path.join(calliope_test_home, 'sdk3'))
    loader.AddReleaseTrack(calliope_base.ReleaseTrack.ALPHA,
                           os.path.join(calliope_test_home, 'alpha'))
    return loader.Generate()

  def testCommand(self):
    self.cli.Execute(['simple-command'])
    self.AssertOutputContains('Simple Command')
    self.ClearOutput()
    self.cli.Execute(['alpha', 'simple-command'])
    self.AssertOutputContains('Alpha filter called')
    self.AssertOutputContains('Simple Command')

  def load(self, elements):
    return self.cli._TopElement().LoadSubElementByPath(elements.split('.'))

  def testElements(self):
    self.assertTrue(self.load('alpha') is not None)

    # Commands exist at the top level and were copied to alpha.
    simple = self.load('simple-command')
    self.assertTrue(simple is not None)
    self.assertEqual(calliope_base.ReleaseTrack.GA, simple.ReleaseTrack())
    simple = self.load('alpha.simple-command')
    self.assertTrue(simple is not None)
    # Ensure the release track of copied groups in the root gets updated
    # correctly.
    self.assertEqual(calliope_base.ReleaseTrack.ALPHA, simple.ReleaseTrack())

    # Group exists at the top level and was copied to alpha.
    self.assertTrue(self.load('sdk2') is not None)
    self.assertTrue(self.load('alpha.sdk2') is not None)
    # Group exists at the top level but was not copied because of release track
    # settings.
    self.assertTrue(self.load('sdk3') is not None)
    self.assertTrue(self.load('alpha.sdk3') is None)

    # Copied groups have all their sub groups and commands.
    self.assertTrue(self.load('alpha.sdk2.command2') is not None)
    # Command does not show up because it is not enabled for this release track.
    self.assertTrue(self.load('alpha.sdk2.requiredargcommand') is None)

  def testCompletion(self):
    # Both mounted sdk directories are in GA.
    self.RunCompletion('sdk', ['sdk2', 'sdk3'])
    # Only sdk2 is opted in for alpha.
    self.RunCompletion('alpha sdk', ['sdk2'])
    # This sub command is not enabled for alpha so it should not show up.
    self.RunCompletion('alpha sdk2 requiredargc', [''])


class DeprecateTests(cli_test_base.CliTestBase, sdk_test_base.WithLogCapture):

  def _CreateCLI(self):
    calliope_test_home = self.Resource(
        'tests', 'unit', 'calliope', 'testdata', 'sdk9')
    pkg_root = os.path.join(calliope_test_home, 'notice')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    loader.AddReleaseTrack(calliope_base.ReleaseTrack.ALPHA,
                           os.path.join(calliope_test_home, 'alpha'))
    return loader.Generate()

  def testDeprecateGroupWithWarning(self):
    self.cli.Execute(['deprecated-group', 'some-command'])
    self.AssertErrEquals('WARNING: group warning\n')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecated-group', 'some-command', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecated-group some-command - a dummy command

SYNOPSIS
    test deprecated-group some-command [TEST_WIDE_FLAG ...]

DESCRIPTION
    (DEPRECATED) A dummy command.

    group warning

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecated-group some-command

""")

    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecated-group', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecated-group - test commands for running calliope tests

SYNOPSIS
    test deprecated-group COMMAND [TEST_WIDE_FLAG ...]

DESCRIPTION
    (DEPRECATED) Test commands for running calliope tests.

    group warning

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

COMMANDS
    COMMAND is one of the following:

     another-command
        (DEPRECATED) A dummy command.

     some-command
        (DEPRECATED) A dummy command.

NOTES
    This variant is also available:

        $ test alpha deprecated-group

""")

  def testDeprecateGroupWithOverriddenWarning(self):
    # The more specific warning will be shown by itself in the help text,
    # but both warnings will be shown when executing the command.
    # This is because the warnings are shown by a decorator applied to two
    # different methods: Sdk.Filter and AnotherCommand.Run.
    self.cli.Execute(['deprecated-group', 'another-command'])
    self.AssertErrEquals('WARNING: group warning\nWARNING: My Custom Warning\n')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecated-group', 'another-command', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecated-group another-command - a dummy command

SYNOPSIS
    test deprecated-group another-command [TEST_WIDE_FLAG ...]

DESCRIPTION
    (DEPRECATED) A dummy command.

    My Custom Warning

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecated-group another-command

""")

  def testDeprecateWithWarning(self):
    self.cli.Execute(['deprecation-warning-command'])
    self.AssertLogContains('Deprecation Warning Command Complete\n')
    self.AssertErrEquals("""\
WARNING: This command is deprecated.
Deprecation Warning Command Complete
""")
    self.AssertOutputEquals('output\n', normalize_space=True)
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecation-warning-command', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-warning-command - a simple command to test deprecation

SYNOPSIS
    test deprecation-warning-command [TEST_WIDE_FLAG ...]

DESCRIPTION
    (DEPRECATED) A simple command to test deprecation.

    This command is deprecated.

    test deprecation-warning-command prints a test message. It also contains a
    much longer docstring to ensure the final output is preserved.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecation-warning-command

""")

  def testDeprecateWithError(self):
    with self.assertRaisesRegexp(calliope_base.DeprecationException,
                                 'This command has been removed.'):
      self.cli.Execute(['deprecation-error-command'])
    self.AssertLogNotContains('Deprecation Error Command Complete')
    self.AssertOutputEquals('')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecation-error-command', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-error-command - a simple command to test deprecation

SYNOPSIS
    test deprecation-error-command [TEST_WIDE_FLAG ...]

DESCRIPTION
    (REMOVED) A simple command to test deprecation.

    This command has been removed.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This command is an internal implementation detail and may change or
    disappear without notice.

""")

  def testDeprecateWithCustomWarning(self):
    self.cli.Execute(['deprecation-warning-command-custom-warning'])
    self.AssertLogContains('Deprecation Warning Command Complete\n')
    self.AssertErrEquals('WARNING: My Custom Warning\n')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecation-warning-command-custom-warning', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-warning-command-custom-warning - a simple command to test
        deprecation with custom messages

SYNOPSIS
    test deprecation-warning-command-custom-warning [TEST_WIDE_FLAG ...]

DESCRIPTION
    (DEPRECATED) A simple command to test deprecation with custom messages.

    My Custom Warning

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecation-warning-command-custom-warning

""")

  def testDeprecateWithCustomError(self):
    with self.assertRaisesRegexp(calliope_base.DeprecationException,
                                 'My Custom Error'):
      self.cli.Execute(['deprecation-error-command-custom-err'])
    self.AssertLogNotContains('Deprecation Error Command Complete')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecation-error-command-custom-err', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-error-command-custom-err - a simple command to test
        deprecation with custom messages

SYNOPSIS
    test deprecation-error-command-custom-err [TEST_WIDE_FLAG ...]

DESCRIPTION
    (REMOVED) A simple command to test deprecation with custom messages.

    My Custom Error

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This command is an internal implementation detail and may change or
    disappear without notice.

""")

  def testDeprecateWithCustomDetailedHelp(self):
    self.cli.Execute(['deprecation-warning-command-detailed-help'])
    self.AssertOutputEquals('Deprecation Warning Command Complete\n')
    self.AssertErrEquals('WARNING: My Custom Warning\n')
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecation-warning-command-detailed-help', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-warning-command-detailed-help - short help text

SYNOPSIS
    test deprecation-warning-command-detailed-help [TEST_WIDE_FLAG ...]

DESCRIPTION
    (DEPRECATED) My Custom Warning

        This is a much longer help text for the description that is actually
    passed in via the 'detailed_help' and not via the __doc__ string directly.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecation-warning-command-detailed-help

""")

  def testDeprecateWithReleaseTrack(self):
    self.cli.Execute(['alpha', 'deprecation-warning-command-withtag'])
    self.AssertOutputContains('Alpha filter called')
    self.AssertErrEquals("""\
WARNING: This command is deprecated.
Deprecation Warning Command Complete
""")
    self.ClearOutput()
    self.ClearErr()
    with self.assertRaises(SystemExit):
      self.Run(
          'alpha deprecation-warning-command-withtag --help')
    self.AssertOutputEquals("""\
NAME
    test alpha deprecation-warning-command-withtag - a simple command to test
        deprecation with release tracks

SYNOPSIS
    test alpha deprecation-warning-command-withtag [TEST_WIDE_FLAG ...]

DESCRIPTION
    (ALPHA) (DEPRECATED) A simple command to test deprecation with release
    tracks.

    This command is deprecated.

    test alpha deprecation-warning-command-withtag prints a test message. It
    also contains a much longer docstring to ensure the final output is
    preserved.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This command is currently in ALPHA and may change without notice. Usually,
    users of ALPHA commands and flags need to apply for access, agree to
    applicable terms, and have their projects whitelisted. Contact Google or
    sign up on a product's page for ALPHA access. Product pages can be found at
    https://cloud.google.com/products/.

""")

  def testDeprecateCommandWithWarningSharedDescription(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          ['alpha', 'deprecation-warning-command-shared-description', '--help'])
    self.AssertOutputEquals("""\
NAME
    test alpha deprecation-warning-command-shared-description - test
        deprecation with shared description and release tracks

SYNOPSIS
    test alpha deprecation-warning-command-shared-description
        [TEST_WIDE_FLAG ...]

DESCRIPTION
    (ALPHA) (DEPRECATED) This command is deprecated.

    Test deprecation with shared description and release tracks.

    test alpha deprecation-warning-command-shared-description also contains a
    shared docstring to see if auto-genrated deprecation warnings across
    multiple --help commands in the same session accumulate.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This command is currently in ALPHA and may change without notice. Usually,
    users of ALPHA commands and flags need to apply for access, agree to
    applicable terms, and have their projects whitelisted. Contact Google or
    sign up on a product's page for ALPHA access. Product pages can be found at
    https://cloud.google.com/products/. This variant is also available:

        $ test deprecation-warning-command-shared-description

""")

    self.ClearOutput()
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          ['deprecation-warning-command-shared-description', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-warning-command-shared-description - test deprecation with
        shared description and release tracks

SYNOPSIS
    test deprecation-warning-command-shared-description [TEST_WIDE_FLAG ...]

DESCRIPTION
    (DEPRECATED) This command is deprecated.

    Test deprecation with shared description and release tracks.

    test deprecation-warning-command-shared-description also contains a shared
    docstring to see if auto-genrated deprecation warnings across multiple
    --help commands in the same session accumulate.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecation-warning-command-shared-description

""")


class CommandFlagDeprecationTest(cli_test_base.CliTestBase,
                                 sdk_test_base.WithLogCapture):

  def _CreateCLI(self):
    calliope_test_home = self.Resource(
        'tests', 'unit', 'calliope', 'testdata', 'sdk9')
    pkg_root = os.path.join(calliope_test_home, 'notice')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    loader.AddReleaseTrack(calliope_base.ReleaseTrack.ALPHA,
                           os.path.join(calliope_test_home, 'alpha'))
    return loader.Generate()

  def testCommandFlagDeprecated(self):
    self.cli.Execute([
        'deprecation-flag-warning-command',
        '--testflag', 'foo',
        '--otherflag', 'bar'
    ])
    self.AssertLogContains('testflag=foo\n')
    self.AssertLogContains('otherflag=bar\n')
    self.AssertErrContains('WARNING: testflag is DEPRECATED.')
    self.AssertOutputEquals('Deprecation Flag Warning Command Complete\n',
                            normalize_space=True)

  def testCommandFlagRemoved(self):
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'testflag is REMOVED.'):
      self.cli.Execute([
          'deprecation-flag-error-command',
          '--testflag', 'foo',
          '--otherflag', 'bar'
      ])
    self.AssertLogNotContains('testflag=foo\n')
    self.AssertLogNotContains('otherflag=bar\n')
    self.AssertOutputNotContains('Command Complete\n', normalize_space=True)

  def testCommandFlagDeprecatedCustomFunction(self):
    self.cli.Execute([
        'deprecation-flag-custfunc-warning-command', '--testflag', 'foo',
        '--otherflag', 'bar'
    ])
    self.AssertLogContains('testflag=foo\n')
    self.AssertLogContains('otherflag=bar\n')
    self.AssertErrContains('WARNING: Flag testflag is deprecated.')
    self.AssertOutputEquals(
        'Deprecation Flag Custom Warning Command Complete\n',
        normalize_space=True)

    self.ClearOutput()
    self.ClearErr()
    self.cli.Execute([
        'deprecation-flag-custfunc-warning-command', '--testflag', 'bar',
        '--otherflag', 'foo'
    ])
    self.AssertLogContains('testflag=bar\n')
    self.AssertLogContains('otherflag=foo\n')
    self.AssertErrNotContains('WARNING: Flag testflag is deprecated.')
    self.AssertOutputEquals(
        'Deprecation Flag Custom Warning Command Complete\n',
        normalize_space=True)

  def testCommandFlagRemovedCustomFunction(self):
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Flag testflag has been removed.'):
      self.cli.Execute([
          'deprecation-flag-custfunc-error-command', '--testflag', 'foo',
          '--otherflag', 'bar'
      ])
    self.AssertLogNotContains('testflag=foo\n')
    self.AssertLogNotContains('otherflag=bar\n')
    self.AssertOutputNotContains('Command Complete\n', normalize_space=True)

    self.ClearOutput()
    self.ClearErr()
    self.cli.Execute([
        'deprecation-flag-custfunc-error-command', '--testflag', 'bar',
        '--otherflag', 'foo'
    ])
    self.AssertLogContains('testflag=bar\n')
    self.AssertLogContains('otherflag=foo\n')
    self.AssertErrNotContains('ERROR: Flag testflag is removed.')
    self.AssertOutputEquals('Deprecation Flag Custom Error Command Complete\n',
                            normalize_space=True)

  def testCommandFlagDeprecatedHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecation-flag-warning-command', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-flag-warning-command - a simple command to test flag
        deprecation

SYNOPSIS
    test deprecation-flag-warning-command [--otherflag[=OTHERFLAG]]
        [--testflag=TESTFLAG] [TEST_WIDE_FLAG ...]

DESCRIPTION
    test deprecation-flag-warning-command prints a test message.

FLAGS
     --otherflag[=OTHERFLAG]
        The Other Flag

     --testflag=TESTFLAG
        (DEPRECATED) Test flag for testing.

        testflag is DEPRECATED.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecation-flag-warning-command

""")

  def testCommandFlagRemovedHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(['deprecation-flag-error-command', '--help'])
    self.AssertOutputEquals("""\
NAME
    test deprecation-flag-error-command - a simple command to test flag removal

SYNOPSIS
    test deprecation-flag-error-command [--otherflag[=OTHERFLAG]]
        [--testflag=TESTFLAG] [TEST_WIDE_FLAG ...]

DESCRIPTION
    test deprecation-flag-error-command prints a test message.

FLAGS
     --otherflag[=OTHERFLAG]
        The Other Flag

     --testflag=TESTFLAG
        (REMOVED) Test flag for testing.

        testflag is REMOVED.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flatten,
    --format, --help, --log-http, --user-output-enabled, --verbosity. Run $
    test help for details.

NOTES
    This variant is also available:

        $ test alpha deprecation-flag-error-command

""")

  def testCommandAndFlagDeprecated(self):
    self.cli.Execute([
        'deprecation-flag-cmd-warning-command',
        '--testflag',
        '--otherflag', 'bar'
    ])
    self.AssertLogContains('testflag=True\n')
    self.AssertLogContains('otherflag=bar\n')
    self.AssertErrContains('WARNING: testflag is DEPRECATED.')
    self.AssertErrContains('WARNING: This command is deprecated.')
    self.AssertOutputEquals(('Deprecation Flag and Cmd Warning '
                             'Command Complete\n'),
                            normalize_space=True)

  def testCommandAndFlagRemoved(self):
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Flag testflag has been removed.'):
      self.cli.Execute([
          'deprecation-flag-cmd-error-command',
          '--testflag', 'foo',
          '--otherflag', 'bar'
      ])
    self.AssertLogNotContains('testflag=foo\n')
    self.AssertLogNotContains('otherflag=bar\n')
    self.AssertOutputNotContains('Command Complete\n', normalize_space=True)


class DynamicPositionalActionTests(util.WithTestTool,
                                   sdk_test_base.WithOutputCapture):

  def testDynamicArgsNoAdditionalRunOnce(self):
    self.cli.Execute('sdk2 dynamic-args --no-additional abc'.split())
    self.AssertOutputContains("""\
additional=False
flags=
name=abc
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,flags,h,help,name,verbosity
""")

  def testDynamicArgsNoAdditionalRunTwice(self):
    self.cli.Execute('sdk2 dynamic-args --no-additional abc'.split())
    self.AssertOutputContains("""\
additional=False
flags=
name=abc
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,flags,h,help,name,verbosity
""")

    self.ClearOutput()
    self.ClearErr()
    self.cli.Execute('sdk2 dynamic-args abc'.split())
    self.AssertOutputContains("""\
additional=True
flags=
name=abc
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,flags,h,help,name,verbosity
""")

  def testDynamicArgsRunOnce(self):
    self.cli.Execute('sdk2 dynamic-args abc'.split())
    self.AssertOutputContains("""\
additional=True
flags=
name=abc
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,flags,h,help,name,verbosity
""")

  def testDynamicArgsRunTwice(self):
    self.cli.Execute('sdk2 dynamic-args abc'.split())
    self.AssertOutputContains("""\
additional=True
flags=
name=abc
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,flags,h,help,name,verbosity
""")

    self.ClearOutput()
    self.ClearErr()
    self.cli.Execute('sdk2 dynamic-args abc'.split())
    self.AssertOutputContains("""\
additional=True
flags=
name=abc
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,flags,h,help,name,verbosity
""")

  def testDynamicArgsAddZoneFlagOnce(self):
    self.cli.Execute('sdk2 dynamic-args --flags=zone abc xyz'.split())
    self.AssertOutputContains("""\
additional=True
extra=xyz
flags=zone
name=abc
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,h,help,name,verbosity,zone
""")

  def testDynamicArgsUseZoneFlagOnce(self):
    self.cli.Execute('sdk2 dynamic-args --flags=zone abc --zone=ZONE'.split())
    self.AssertOutputContains("""\
additional=True
extra=None
flags=zone
name=abc
zone=ZONE
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,h,help,name,verbosity,zone
""")

  def testDynamicArgsAddZoneFlagTwice(self):
    self.cli.Execute('sdk2 dynamic-args --flags=zone abc --zone=ZONE'.split())
    self.AssertOutputContains("""\
additional=True
extra=None
flags=zone
name=abc
zone=ZONE
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,h,help,name,verbosity,zone
""")

    self.ClearOutput()
    self.ClearErr()
    self.cli.Execute('sdk2 dynamic-args --flags=zone abc --zone=ZONE'.split())
    self.AssertOutputContains("""\
additional=True
extra=None
flags=zone
name=abc
zone=ZONE
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,h,help,name,verbosity,zone
""")

  def testDynamicArgsUseZoneFlagTwice(self):
    self.cli.Execute('sdk2 dynamic-args --flags=zone abc --zone=ZONE'.split())
    self.AssertOutputContains("""\
additional=True
extra=None
flags=zone
name=abc
zone=ZONE
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,h,help,name,verbosity,zone
""")

    self.ClearOutput()
    self.ClearErr()
    self.cli.Execute('sdk2 dynamic-args --flags=zone abc --zone=ZONE'.split())
    self.AssertOutputContains("""\
additional=True
extra=None
flags=zone
name=abc
zone=ZONE
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,h,help,name,verbosity,zone
""")

  def testDynamicArgsRunTwiceDifferentFlags(self):
    self.cli.Execute('sdk2 dynamic-args --flags=zone abc --zone=ZONE'.split())
    self.AssertOutputContains("""\
additional=True
extra=None
flags=zone
name=abc
zone=ZONE
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,h,help,name,verbosity,zone
""")

    self.ClearOutput()
    self.ClearErr()
    self.cli.Execute('sdk2 dynamic-args --flags=foo abc --foo=BAR'.split())
    self.AssertOutputContains("""\
additional=True
extra=None
flags=foo
name=abc
foo=BAR
""")
    self.AssertErrContains("""\
additional,flags,h,help,name,verbosity
Filter Sdk1
Filter Sdk2
additional,extra,flags,foo,h,help,name,verbosity,zone
""")


class YamlTranslatorTest(sdk_test_base.WithOutputCapture):

  # Just a stub translator to make sure calliope is invoking it correctly.
  class Translator(command_loading.YamlCommandTranslator):

    def Translate(self, path, command_data):
      class Command(calliope_base.Command):

        @staticmethod
        def Args(parser):
          parser.add_argument('--foo', help='Auxilio aliis.')

        def Run(self, args):
          print command_data['description']
          print args.foo
      return Command

  def SetUp(self):
    self.calliope_test_home = self.Resource(
        'tests', 'unit', 'calliope', 'testdata')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk10'),
        yaml_command_translator=YamlTranslatorTest.Translator())
    loader.AddReleaseTrack(calliope_base.ReleaseTrack.ALPHA,
                           os.path.join(self.calliope_test_home, 'alpha'))
    self.cli = loader.Generate()

  def testYaml(self):
    self.cli.Execute(['test', '--foo', 'bar'])
    self.AssertOutputEquals(
        """This is the GA/BETA track\nbar\n""",
        normalize_space=True)
    self.ClearOutput()
    self.cli.Execute(['alpha', 'test', '--foo', 'bar'])
    self.AssertOutputEquals(
        """Alpha filter called\nThis is the ALPHA track\nbar\n""",
        normalize_space=True)

  def testDualImplementation(self):
    self.cli.Execute(['dual', '--foo', 'bar'])
    self.AssertOutputEquals(
        """This is the GA/BETA track\nbar\n""",
        normalize_space=True)
    self.ClearOutput()
    self.cli.Execute(['alpha', 'dual', '--foo', 'bar'])
    self.AssertOutputEquals(
        """Alpha filter called\nThis is the ALPHA track\nbar\n""",
        normalize_space=True)


class ChoiceArgumentTest(sdk_test_base.WithOutputCapture):
  """ChoiceArgument Tests."""

  def SetUp(self):
    self.parser = util.ArgumentParser()
    self.list_choices = ['one', 'two-the-second', '3.1-the-last']
    self.set_choices = set(['thing-one', 'thing-two'])
    self.dict_choices = {
        'dict-choice-one': 'First Dict Choice',
        'dict-choice-two': 'Second Dict Choice',
        'dict-choice-three': 'Third Dict Choice'
    }

  def testAllChoiceValueTypes(self):
    list_arg = calliope_base.ChoiceArgument(
        '--my-list-arg', choices=self.list_choices, help_str='List help.')
    dict_arg = calliope_base.ChoiceArgument(
        '--my-dict-arg', choices=self.dict_choices, help_str='Dict help.')
    set_arg = calliope_base.ChoiceArgument(
        '--my-set-arg', choices=self.set_choices, help_str='Set help.')
    tuple_arg = calliope_base.ChoiceArgument(
        '--my-tuple-arg',
        choices=tuple(self.list_choices),
        help_str='Set help.')
    list_arg.AddToParser(self.parser)
    dict_arg.AddToParser(self.parser)
    set_arg.AddToParser(self.parser)
    tuple_arg.AddToParser(self.parser)
    parse_result = self.parser.parse_args([
        '--my-set-arg', 'THING_ONE', '--my-dict-arg', 'diCT_CHoicE-THRee',
        '--my-list-arg', '3.1_THE-LAST', '--my-tuple-arg', 'ONE'
    ])
    self.assertEquals('thing-one', parse_result.my_set_arg)
    self.assertEquals('dict-choice-three', parse_result.my_dict_arg)
    self.assertEquals('3.1-the-last', parse_result.my_list_arg)
    self.assertEquals('one', parse_result.my_tuple_arg)

  def testBadChoicesType(self):
    with self.assertRaisesRegexp(TypeError, ('Choices must be an iterable '
                                             'container of options')):
      calliope_base.ChoiceArgument(
          '--my-arg', choices='NO GOOD', default='NONE', help_str='Test help.')

  def testBadChoicesValues(self):
    with self.assertRaisesRegexp(ValueError, ('Choices must be entirely in '
                                              'lowercase with words separated '
                                              'by hyphens')):
      calliope_base.ChoiceArgument(
          '--my-arg',
          choices={
              'NONE': 'Flag Help 1.',
              'BAD_VAL': 'Flag Help 2',
          },
          default='NONE',
          help_str='Test help.')

  def testMissingChoices(self):
    with self.assertRaisesRegexp(ValueError, 'Choices must not be empty'):
      calliope_base.ChoiceArgument(
          '--my-arg', choices=[], help_str='Test help.')

  def testBadChoiceSelection(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg',
        choices=self.dict_choices,
        help_str='My Help')
    choice_arg.AddToParser(self.parser)
    with self.assertRaisesRegexp(SystemExit, '2'):
      self.parser.parse_args(['--my-arg', 'DICT_CHOICE_FOUR'])
    self.AssertErrContains(
        "argument --my-arg: Invalid choice: 'dict-choice-four'. "
        "Did you mean 'dict-choice-two'?")

  def testRequiredSet(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg',
        choices=self.set_choices,
        help_str='My Help',
        required=True)
    choice_arg.AddToParser(self.parser)
    self.parser.add_argument(
        '--other-arg', required=False, help='Auxilio aliis.')
    with self.assertRaisesRegexp(SystemExit, '2'):
      self.parser.parse_args(['--other-arg', 'foo'])
    self.AssertErrContains('argument --my-arg: Must be specified.')

  def testActionSet(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg',
        choices=self.dict_choices,
        help_str='My Help',
        action='append')
    choice_arg.AddToParser(self.parser)
    parse_result = self.parser.parse_args(['--my-arg', 'DICT_CHOICE_ONE',
                                           '--my-arg', 'DICT_CHOICE_TWO'])
    self.assertEquals(['dict-choice-one', 'dict-choice-two'],
                      parse_result.my_arg)

  def testMetavarSet(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg',
        choices=self.list_choices,
        help_str='My Help',
        metavar='MY_CHOICE')
    choice_arg.AddToParser(self.parser)
    with self.assertRaisesRegexp(SystemExit, '0'):
      self.parser.parse_args(['-h'])
    self.AssertOutputContains('--my-arg MY_CHOICE  My Help')

  def testDestSet(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg',
        choices=self.list_choices,
        help_str='My Help',
        dest='MY_CHOICE')
    choice_arg.AddToParser(self.parser)
    parse_result = self.parser.parse_args(['--my-arg', 'one'])
    self.assertFalse(hasattr(parse_result, 'my_arg'))
    self.assertEqual(parse_result.MY_CHOICE, 'one')

  def testDefaultSet(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg',
        choices=self.list_choices,
        help_str='My Help',
        default='one')
    choice_arg.AddToParser(self.parser)
    self.parser.add_argument(
        '--other-arg', required=True, help='Auxilio aliis.')
    parse_result = self.parser.parse_args(['--other-arg', 'VALUE'])
    self.assertEqual(parse_result.my_arg, 'one')

  def testWithMinArgs(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg', choices=self.list_choices, help_str='Test help.')
    choice_arg.AddToParser(self.parser)
    parse_result = self.parser.parse_args(['--my-arg', 'tWO_ThE-seConD'])
    self.assertEquals('two-the-second', parse_result.my_arg)

  def testWithDeprecation(self):
    choice_arg = calliope_base.ChoiceArgument(
        '--my-arg',
        choices=self.list_choices,
        action=actions.DeprecationAction(
            'my-arg', show_message=bool, warn='my-arg is being deprecated.'),
        help_str='Test help.')
    choice_arg.AddToParser(self.parser)
    parse_result = self.parser.parse_args(['--my-arg', 'tWO_ThE-seConD'])
    self.assertEquals('two-the-second', parse_result.my_arg)


if __name__ == '__main__':
  test_case.main()