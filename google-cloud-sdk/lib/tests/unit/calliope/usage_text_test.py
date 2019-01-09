# -*- coding: utf-8 -*- #
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

"""Unit tests for the usage_text module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.command_lib.util.apis import yaml_command_translator
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.calliope import util

import mock


class UsageTextTest(util.WithTestTool):

  def testExtractHelpStrings(self):
    # pylint: disable=g-continuation-misaligned
    # pylint: disable=g-continuation-in-dict-misaligned
    test_cases = (
        {'input': None, 'expected_short': '', 'expected_long': ''},
        {'input': 'short\n',
         'expected_short': 'short', 'expected_long': 'short'},
        {'input': 'short 1\nshort 2\n',
         'expected_short': 'short 1 short 2',
         'expected_long': 'short 1 short 2'},
        {'input': 'short\n\nlong',
         'expected_short': 'short', 'expected_long': 'long'},
        {'input': 'short 1\nshort 2\n\n   long\n     long indented',
         'expected_short': 'short 1 short 2',
         'expected_long': 'long\n  long indented'},
        {'input': 'short\n\n  long para 1\n\n  long para 2\n',
         'expected_short': 'short',
         'expected_long': 'long para 1\n\nlong para 2'},
        {'input': '\nline 1 after blank line\n line 2 after blank line',
         'expected_short':
                 'line 1 after blank line line 2 after blank line',
         'expected_long':
                 'line 1 after blank line\n line 2 after blank line'},
        {'input': '', 'expected_short': '', 'expected_long': ''},
        {'input': ' ', 'expected_short': '', 'expected_long': ''},
        {'input': '\tshort\t\n\n long \n',
         'expected_short': 'short', 'expected_long': 'long'},
        # In the following corner cases, there are two blank lines. The first is
        # taken as the divider between the (nonexistant) short help and the long
        # help, both of which are stripped to '' and replaced by None.
        {'input': '\n', 'expected_short': '', 'expected_long': ''},
        {'input': '\n ', 'expected_short': '', 'expected_long': ''},
        {'input': ' \n', 'expected_short': '', 'expected_long': ''},
        {'input': ' \n ', 'expected_short': '', 'expected_long': ''},
        # In the following case, there are three blank lines, the last two of
        # which are interpreted as long help. The long help is transformed from
        # ' \n  ' to '\n ' by dedenting, and then to '' by stripping, and then
        # replaced by None.
        {'input': ' \n \n  \n', 'expected_short': '', 'expected_long': ''},
        # In the following case, there is a line consisting of a space, followed
        # by two lines taken as the long help. The long help is dedented to
        # '\n x\n' and then stripped to 'x'. Since there is no short help but
        # nonempty long help, we flow the words of the long help together to
        # form the short help.
        {'input': ' \n \n  x\n', 'expected_short': 'x', 'expected_long': 'x'},
    )
    for testcase in test_cases:
      input_string = testcase['input']
      (short_help, long_help) = usage_text.ExtractHelpStrings(input_string)
      self.assertEqual(
          testcase['expected_short'], short_help,
          'short help for input<%s>' % (input_string,))
      self.assertEqual(
          testcase['expected_long'], long_help,
          'long help for input<%s>' % (input_string,))

  def testArgOrder(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 remainder-with-flags'.split())
    self.AssertErrContains(
        'remainder-with-flags SINGLE_POSITIONAL --foo=FOO [optional flags] '
        '[-- PASSTHROUGH_ARGS ...]')

  def testRemainderExtraArgs(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 extra-args -- foo --bar'.split())
    self.AssertErrContains(
        'extra-args POSITIONAL [optional flags] [-- EXTRA_ARGS ...]')

  def testSuppressedPositionalUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 suppressed-positional -h'.split())
    self.AssertOutputNotContains('SUPPRESSED')
    self.AssertOutputNotContains('positional arguments')
    self.AssertOutputNotContains('--hidden')

  def testSuppressedPositionalHelp(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 suppressed-positional --help'.split())
    self.AssertOutputNotContains('SUPPRESSED')
    self.AssertOutputNotContains('POSITIONAL ARGUMENTS')
    self.AssertOutputNotContains('==SUPPRESS==')
    self.AssertOutputNotContains('--hidden')

  def testUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 [optional flags] <group | command>
  group may be           lotsofargs
  command may be         arg-groups | bool-mutex | combinations | command2 |
                         common-flags | common-other-flags | deprecated-args |
                         dynamic-args | extra-args | list-command-flags |
                         modal-group | multiple-positional | nested-groups |
                         ordered-choices | other-flags | remainder |
                         remainder-with-flags | required-common-flags |
                         required-common-other-flags | required-flags |
                         required-other-flags | required-vs-optional |
                         requiredargcommand | suppressed-positional

For detailed information on this command and its flags, run:
  test sdk2 --help
""")

  def testUsageTop(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('-h'.split())
    self.AssertOutputEquals("""\
Usage: test [optional flags] <group | command>
  group may be           beta | broken-sdk | cfg | compound-group |
                         newstylegroup | sdk11 | sdk2 | sdk3 | sdk7
  command may be         command1 | dict-list | exceptioncommand | exit2 |
                         help | implementation-args | loggingcommand |
                         mutex-command | newstylecommand | recommand |
                         requiredargcommand | simple-command | unsetprop

For detailed information on this command and its flags, run:
  test --help
""")

  def testUsageCommon(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 common-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 common-flags [optional flags]
  optional flags may be  --common | --help

For detailed information on this command and its flags, run:
  test sdk2 common-flags --help
""")

  def testUsageCommonOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 common-other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 common-other-flags [optional flags]
  optional flags may be  --common | --help | --other

For detailed information on this command and its flags, run:
  test sdk2 common-other-flags --help
""")

  def testUsageOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 other-flags [optional flags]
  optional flags may be  --help | --other

For detailed information on this command and its flags, run:
  test sdk2 other-flags --help
""")

  def testUsageRequiredCommonOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-common-other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-common-other-flags --required=REQUIRED [optional flags]
  optional flags may be  --common | --help | --other

For detailed information on this command and its flags, run:
  test sdk2 required-common-other-flags --help
""")

  def testUsageRequiredCommon(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-common-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-common-flags --required=REQUIRED [optional flags]
  optional flags may be  --common | --help

For detailed information on this command and its flags, run:
  test sdk2 required-common-flags --help
""")

  def testUsageRequiredOther(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-other-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-other-flags --required=REQUIRED [optional flags]
  optional flags may be  --help | --other

For detailed information on this command and its flags, run:
  test sdk2 required-other-flags --help
""")

  def testUsageRequired(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 required-flags --required=REQUIRED [optional flags]
  optional flags may be  --help

For detailed information on this command and its flags, run:
  test sdk2 required-flags --help
""")

  def testUsageListCommand(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 list-command-flags -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 list-command-flags [optional flags]
  optional flags may be  --filter | --help | --limit | --page-size | --sort-by |
                         --uri

For detailed information on this command and its flags, run:
  test sdk2 list-command-flags --help
""")

  def testUsagePositionalsStableSort(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 multiple-positional -h'.split())
    self.AssertOutputEquals("""\
Usage: test sdk2 multiple-positional [USER@]ZZZ [[USER@]ZZZ ...] [USER@]AAA [[USER@]AAA ...] [optional flags]
  optional flags may be  --help

For detailed information on this command and its flags, run:
  test sdk2 multiple-positional --help
""")

  def testCategoricalUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2'.split())
    self.AssertErrContains("""\
ERROR: (test.sdk2) Command name argument expected.

Available commands for test sdk2:

  Category 1
      arg-groups              Argument groups test command.
      combinations            A command to test generator / exception
                              combinations.

  Category 2
      bool-mutex              A command with a Boolean flag in a mutex group.
""")

  def testCategoricalUsageNoCategories(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk3'.split())
    self.AssertErrEquals("""\
ERROR: (test.sdk3) Command name argument expected.

Available groups for test sdk3:

      newstylegroup           Group short help.

Available commands for test sdk3:

      nested                  A nested command.

For detailed information on this command and its flags, run:
  test sdk3 --help
""")

  def testHelpBoolMutex(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 bool-mutex --help'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 bool-mutex - a command with a Boolean flag in a mutex group

SYNOPSIS
    test sdk2 bool-mutex [--no-bool-independent] [--bool-mutex | --value=VALUE]
        [TEST_WIDE_FLAG ...]

DESCRIPTION
    A command with a Boolean flag in a mutex group.

FLAGS
     --bool-independent
        Independent Boolean flag on by default. Enabled by default, use
        --no-bool-independent to disable.

     At most one of these may be specified:

       --bool-mutex
          Boolean flag in mutex group.

       --value=VALUE
          Value flag.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity. Run $ test help for details.

NOTES
    This variant is also available:

        $ test beta sdk2 bool-mutex
""")

  def testHelpRequiredVsOptional(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 required-vs-optional --help'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 required-vs-optional - a command with required vs optional flag
        combinations

SYNOPSIS
    test sdk2 required-vs-optional EPISODE
        --required-singleton=REQUIRED_SINGLETON
        (--that-one=THAT_ONE | --this-one=THIS_ONE)
        [--optional-singleton=OPTIONAL_SINGLETON]
        [--half-dozen-of-the-other=HALF_DOZEN_OF_THE_OTHER
          | --six-of-one=SIX_OF_ONE] [--larry=QUOTE --moe=QUOTE --shemp=QUOTE]
        [TEST_WIDE_FLAG ...]

DESCRIPTION
    A command with required vs optional flag combinations.

POSITIONAL ARGUMENTS
     EPISODE
        your favorite eposide.

REQUIRED FLAGS
     --required-singleton=REQUIRED_SINGLETON
        Required singleton flag.

     Exactly one of these must be specified:

       --that-one=THAT_ONE
          That one.

       --this-one=THIS_ONE
          This one.

OPTIONAL FLAGS
     --optional-singleton=OPTIONAL_SINGLETON
        Optional singleton flag.

     At most one of these may be specified:

       --half-dozen-of-the-other=HALF_DOZEN_OF_THE_OTHER
          Half dozen of the other.

       --six-of-one=SIX_OF_ONE
          Six of one.

     These are the stooge related flags:

       --larry=QUOTE
          I didn't wanna say yes but I couldn't say no.

       --moe=QUOTE
          Why you.

       --shemp=QUOTE
          Hey Moe! Hey Larry!

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity. Run $ test help for details.

NOTES
    This variant is also available:

        $ test beta sdk2 required-vs-optional
""")

  def testHelpEmptyDocstringDescription(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('beta sdk2 command2 --help'.split())
    self.AssertOutputContains("""\
NAME
    test beta sdk2 command2 - test empty DESCRIPTION followed by EXAMPLES

SYNOPSIS
    test beta sdk2 command2 [TEST_WIDE_FLAG ...]

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity. Run $ test help for details.

EXAMPLES
    Don't use this example as an example for writing examples.

NOTES
    This command is currently in BETA and may change without notice. This
    variant is also available:

        $ test sdk2 command2
""")

  def testHelpMarkdownDeprecatedAction(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 deprecated-args --document=style=markdown'.split())
    self.AssertOutputContains("""\
# TEST_SDK2_DEPRECATED-ARGS(1)


## NAME

test sdk2 deprecated-args - actions.DeprecationAction test command


## SYNOPSIS

`test sdk2 deprecated-args` [*--begin*=_BEGIN_] [*--deprecated-arg*=_DEPRECATED_ARG_] [*--end*=_END_] [*--removed-arg*=_REMOVED_ARG_] [_TEST_WIDE_FLAG ..._]


## DESCRIPTION

actions.DeprecationAction test command.


## FLAGS

*--begin*=_BEGIN_::

Begin flag help.

*--deprecated-arg*=_DEPRECATED_ARG_::

(DEPRECATED) Deprecated flag help.
+
Note we have more to say about this. Run:
+
  $ gcloud alpha container clusters update example-cluster \\
      --zone us-central1-a --additional-zones ""
+
This flag is messed up.

*--end*=_END_::

End flag help.

*--removed-arg*=_REMOVED_ARG_::

(REMOVED) Removed flag help. Run:
+
  gcloud bar --removed-arg=foo
+
Flag removed_arg has been removed.


## TEST WIDE FLAGS

These flags are available to all commands: --configuration, --flags-file, --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled, --verbosity.
Run *$ link:test/help[test help]* for details.


## NOTES

This variant is also available:

  $ link:test/beta/sdk2/deprecated-args[test beta sdk2 deprecated-args]
""")

  def testHelpDeprecatedAction(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 deprecated-args --help'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 deprecated-args - actions.DeprecationAction test command

SYNOPSIS
    test sdk2 deprecated-args [--begin=BEGIN] [--deprecated-arg=DEPRECATED_ARG]
        [--end=END] [--removed-arg=REMOVED_ARG] [TEST_WIDE_FLAG ...]

DESCRIPTION
    actions.DeprecationAction test command.

FLAGS
     --begin=BEGIN
        Begin flag help.

     --deprecated-arg=DEPRECATED_ARG
        (DEPRECATED) Deprecated flag help.

        Note we have more to say about this. Run:

            $ gcloud alpha container clusters update example-cluster \\
                --zone us-central1-a --additional-zones ""

        This flag is messed up.

     --end=END
        End flag help.

     --removed-arg=REMOVED_ARG
        (REMOVED) Removed flag help. Run:

            gcloud bar --removed-arg=foo

        Flag removed_arg has been removed.

TEST WIDE FLAGS
    These flags are available to all commands: --configuration, --flags-file,
    --flatten, --format, --help, --log-http, --top-flag, --user-output-enabled,
    --verbosity. Run $ test help for details.

NOTES
    This variant is also available:

        $ test beta sdk2 deprecated-args
""")

  def testHelpExplicitNotes(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 common-flags --document=style=markdown'.split())
    self.AssertOutputContains("""\
## NOTES

Move along, no autogenerated notes to see here.
""")

  def testHelpUnicodeChoices(self):
    self.SetEncoding('utf8')
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk11 sdk optional-flags --help'.split())
    self.AssertOutputContains('☠123')

  def testMarkdownExplicitAndAutogeneratedNotes(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'beta sdk2 common-flags --document=style=markdown'.split())
    self.AssertOutputContains("""\
## NOTES

Explicit notes should appear along with BETA autogenerated notes.

This command is currently in BETA and may change without notice.
This variant is also available:

  $ link:test/sdk2/common-flags[test sdk2 common-flags]

""")

  def testArgumentGroupsMarkdown(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'sdk2 arg-groups --document=style=markdown'.split())
    self.AssertOutputContains("""\
# TEST_SDK2_ARG-GROUPS(1)


## NAME

test sdk2 arg-groups - argument groups test command


## SYNOPSIS

`test sdk2 arg-groups` (_REQUIRED_MODAL_POSITIONAL_ : *--abc*) [[_OPTIONAL_MODAL_POSITIONAL_ ...] *--def*] (*--required-modal-flag* : *--ghi*) [*--optional-modal-flag* : *--jkl*] [_TEST_WIDE_FLAG ..._]


## DESCRIPTION

Argument groups test command.


## POSITIONAL ARGUMENTS

:: Required positional group. This must be specified.


_REQUIRED_MODAL_POSITIONAL_:::

Required modal positional.
This positional must be specified if any of the other arguments in this group are specified.

*--abc*:::

Optional flag.

:: Optional positional group.


[_OPTIONAL_MODAL_POSITIONAL_ ...]:::

Optional modal positional.

*--def*:::

Optional flag.


## REQUIRED FLAGS

:: Required flag group. This must be specified.


*--required-modal-flag*:::

Required modal flag.
This flag must be specified if any of the other arguments in this group are specified.

*--ghi*:::

Optional flag.


## OPTIONAL FLAGS

:: Optional flag group.


*--optional-modal-flag*:::

Optional modal flag.
This flag must be specified if any of the other arguments in this group are specified.

*--jkl*:::

Optional flag.
""")

  def testArgumentGroupsText(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'sdk2 arg-groups --document=style=text'.split())
    self.AssertOutputContains("""\
NAME
    test sdk2 arg-groups - argument groups test command

SYNOPSIS
    test sdk2 arg-groups (REQUIRED_MODAL_POSITIONAL : --abc)
        [[OPTIONAL_MODAL_POSITIONAL ...] --def] (--required-modal-flag : --ghi)
        [--optional-modal-flag : --jkl] [TEST_WIDE_FLAG ...]

DESCRIPTION
    Argument groups test command.

POSITIONAL ARGUMENTS
     Required positional group. This must be specified.

       REQUIRED_MODAL_POSITIONAL
          Required modal positional. This positional must be specified if any
          of the other arguments in this group are specified.

       --abc
          Optional flag.

     Optional positional group.

       [OPTIONAL_MODAL_POSITIONAL ...]
          Optional modal positional.

       --def
          Optional flag.

REQUIRED FLAGS
     Required flag group. This must be specified.

       --required-modal-flag
          Required modal flag. This flag must be specified if any of the other
          arguments in this group are specified.

       --ghi
          Optional flag.

OPTIONAL FLAGS
     Optional flag group.

       --optional-modal-flag
          Optional modal flag. This flag must be specified if any of the other
          arguments in this group are specified.

       --jkl
          Optional flag.
""")

  def testArgumentGroupsShort(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute(
          'sdk2 arg-groups -h'.split())
    self.AssertOutputContains("""\
Usage: test sdk2 arg-groups (REQUIRED_MODAL_POSITIONAL : --abc) [[OPTIONAL_MODAL_POSITIONAL ...] --def] (--required-modal-flag : --ghi) [optional flags]
  optional flags may be  --abc | --def | --ghi | --help | --jkl |
                         --optional-modal-flag
""")

  def testOrderedChoicesText(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('sdk2 ordered-choices --help'.split())
    self.AssertOutputContains("""\
     --foo=FOO
        Ordered Choices. FOO must be one of:

         a-1g
            first
         a-10g
            second
         a-100g
            third
""")


class UsageTextTestWithIOCapture(util.WithTestTool,
                                 test_case.WithInput,
                                 test_case.WithOutputCapture):

  def testPromptSuggester(self):
    properties.VALUES.core.disable_prompts.Set(False)
    properties.VALUES.core.interactive_ux_style.Set(
        properties.VALUES.core.InteractiveUXStyles.NORMAL)

    self.WriteInput('hez', 'yoy', 'ovre', 'their')
    options = ['hey', 'you', 'over', 'there']

    suggester = usage_text.TextChoiceSuggester(choices=options)
    result = console_io.PromptChoice(options, allow_freeform=True,
                                     freeform_suggester=suggester)

    self.AssertErrContains('[hez] not in list. Did you mean [hey]?')
    self.AssertErrContains('[yoy] not in list. Did you mean [you]?')
    self.AssertErrContains('[ovre] not in list. Did you mean [over]?')
    self.AssertErrContains('[their] not in list. Did you mean [there]?')

    self.assertEqual(result, None)


class UsageUtilTest(test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()

  def testGetFlagUsageDefaultString(self):
    arg = self.parser.add_argument(
        '--flag', default='default', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default="default"',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultString(self):
    arg = self.parser.add_argument(
        '--flag', default='default', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultStringWithDoubleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR "b"', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default=\'"a" OR "b"\'',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultStringWithDoubleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR "b"', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultStringWithSingleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default="'a' OR 'b'", help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default="\'a\' OR \'b\'"',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultStringWithSingleQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default="'a' OR 'b'", help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultStringWithMixedQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR \'b\'', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default=\'"a" OR \\\'b\\\'\'',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultStringWithMixedQuotes(self):
    arg = self.parser.add_argument(
        '--flag', default='"a" OR \'b\'', help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultInt(self):
    arg = self.parser.add_argument(
        '--flag', default=123, help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG; default=123',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageBriefDefaultInt(self):
    arg = self.parser.add_argument(
        '--flag', default=123, help='Auxilio aliis.')
    self.assertEqual('--flag=FLAG',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultFalse(self):
    arg = self.parser.add_argument(
        '--bool', default=False, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageDefaultFalseInverted(self):
    arg = self.parser.add_argument(
        '--bool', default=False, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--no-bool',
                     usage_text.GetFlagUsage(
                         arg, inverted=usage_text.InvertedValue.INVERTED))

  def testGetFlagUsageBriefDefaultFalse(self):
    arg = self.parser.add_argument(
        '--bool', default=False, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg, brief=True))

  def testGetFlagUsageDefaultTrue(self):
    arg = self.parser.add_argument(
        '--bool', default=True, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg))

  def testGetFlagUsageDefaultTrueInverted(self):
    arg = self.parser.add_argument(
        '--bool', default=True, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--no-bool',
                     usage_text.GetFlagUsage(
                         arg, inverted=usage_text.InvertedValue.INVERTED))

  def testGetFlagUsageBriefDefaultTrue(self):
    arg = self.parser.add_argument(
        '--bool', default=True, action='store_true', help='Auxilio aliis.')
    self.assertEqual('--bool',
                     usage_text.GetFlagUsage(arg, brief=True))


class GcloudUsageTextTest(util.WithTestTool):

  def SetUp(self):
    self.known_error_handler = mock.MagicMock()
    self._loader = calliope.CLILoader(
        name='gcloud',
        command_root_directory=self.Resource('surface'),
        allow_non_existing_modules=True,
        known_error_handler=self.known_error_handler,
        yaml_command_translator=yaml_command_translator.Translator())

    self.cli = self._loader.Generate()

  def testGcloudUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute([])
    self.AssertErrContains("""\
ERROR: (gcloud) Command name argument expected.

Available commands for gcloud:

  AI and Machine Learning
      ml                      Use Google Cloud machine learning capabilities.
      ml-engine               Manage Cloud ML Engine jobs and models.

  API Platform and Ecosystems
      endpoints               Create, enable and manage API services.
      service-management      Create, enable and manage API services.
      services                List, enable and disable APIs and services.

  Compute
      app                     Manage your App Engine deployments.
      container               Deploy and manage clusters of machines for running
                              containers.
      functions               Manage Google Cloud Functions.

  Data Analytics
      composer                Create and manage Cloud Composer Environments.
      dataflow                Manage Google Cloud Dataflow jobs.
      dataproc                Create and manage Google Cloud Dataproc clusters
                              and jobs.
      pubsub                  Manage Cloud Pub/Sub topics and subscriptions.

  Databases
      datastore               Manage your Cloud Datastore indexes.
      spanner                 Command groups for Cloud Spanner.
      sql                     Create and manage Google Cloud SQL databases.

  Identity and Security
      auth                    Manage oauth2 credentials for the Google Cloud
                              SDK.
      iam                     Manage IAM service accounts and keys.
      kms                     Manage cryptographic keys in the cloud.

  Internet of Things
      iot                     Manage Cloud IoT resources.

  Management Tools
      builds                  Create and manage builds for Google Cloud Build.
      debug                   Commands for interacting with the Cloud Debugger.
      deployment-manager      Manage deployments of cloud resources.
      logging                 Manage Stackdriver Logging.
      organizations           Create and manage Google Cloud Platform
                              Organizations.
      projects                Create and manage project access policies.

  Mobile
      firebase                Work with Google Firebase.

  Networking
      dns                     Manage your Cloud DNS managed-zones and
                              record-sets.
      domains                 Manage domains for your Google Cloud projects.

  SDK Tools
      components              List, install, update, or remove Google Cloud SDK
                              components.
      config                  View and edit Cloud SDK properties.
      feedback                Provide feedback to the Google Cloud SDK team.
      help                    Search gcloud help text.
      info                    Display information about the current gcloud
                              environment.
      init                    Initialize or reinitialize gcloud.
      meta                    Cloud meta introspection commands.
      source                  Cloud git repository commands.
      topic                   gcloud supplementary help.
      version                 Print version information for Cloud SDK
                              components.
""")

  def testGcloudComputeUsage(self):
    with self.assertRaises(SystemExit):
      self.cli.Execute('compute'.split())
    self.AssertErrContains("""\
ERROR: (gcloud.compute) Command name argument expected.

Available commands for gcloud compute:

  Disks
      disk-types              Read Google Compute Engine virtual disk types.
      disks                   Read and manipulate Google Compute Engine disks.

  Info
      accelerator-types       Read Google Compute Engine accelerator types.
      machine-types           Read Google Compute Engine virtual machine types.
      operations              Read and manipulate Google Compute Engine
                              operations.
      regions                 List Google Compute Engine regions.
      zones                   List Google Compute Engine zones.

  Instances
      commitments             Manage Google Compute Engine commitments.
      diagnose                Debugging tools for Google Compute Engine virtual
                              machine instances.
      images                  List, create, and delete Google Compute Engine
                              images.
      instance-groups         Read and manipulate Google Compute Engine instance
                              groups.
      instance-templates      Read and manipulate Google Compute Engine
                              instances templates.
      instances               Read and manipulate Google Compute Engine virtual
                              machine instances.
      snapshots               List, describe, and delete Google Compute Engine
                              snapshots.
      sole-tenancy            Read and manage Google Compute Engine sole-tenancy
                              resources.
      target-instances        Read and manipulate Google Compute Engine virtual
                              target instances.
      tpus                    List, create, and delete Cloud TPUs.

  Load Balancing
      backend-buckets         Read and manipulate backend buckets.
      backend-services        List, create, and delete backend services.
      forwarding-rules        Read and manipulate traffic forwarding rules to
                              network load balancers.
      health-checks           Read and manipulate health checks for load
                              balanced instances.
      http-health-checks      Read and manipulate HTTP health checks for load
                              balanced instances.
      https-health-checks     Read and manipulate HTTPS health checks for load
                              balanced instances.
      ssl-certificates        List, create, and delete Google Compute Engine SSL
                              certificates.
      ssl-policies            List, create, delete and update Google Compute
                              Engine SSL policies.
      target-pools            Control Compute Engine target pools for network
                              load balancing.

  Networking
      addresses               Read and manipulate Google Compute Engine
                              addresses.
      firewall-rules          List, create, update, and delete Google Compute
                              Engine firewall rules.
      interconnects           Read and manipulate  Google Compute Engine
                              interconnects.
      networks                List, create, and delete Google Compute Engine
                              networks.
      routers                 List, create, and delete Google Compute Engine
                              routers.
      routes                  Read and manipulate routes.
      shared-vpc              Configure shared VPC.
      target-http-proxies     List, create, and delete target HTTP proxies.
      target-https-proxies    List, create, and delete target HTTPS proxies.
      target-ssl-proxies      List, create, and delete target SSL proxies.
      target-tcp-proxies      List, create, and delete target TCP proxies.
      target-vpn-gateways     Read and manipulate Google Compute Engine VPN
                              Gateways.
      url-maps                List, create, and delete URL maps.
      vpn-tunnels             Read and manipulate Google Compute Engine VPN
                              Tunnels.

  Tools
      config-ssh              Populate SSH config files with Host entries from
                              each instance.
      connect-to-serial-port  Connect to the serial port of an instance.
      os-login                Create and manipulate Google Compute Engine OS
                              Login resources.
      project-info            Read and manipulate project-level data like quotas
                              and metadata.
      reset-windows-password  Reset and return a password for a Windows machine
                              instance.
      scp                     Copy files to and from Google Compute Engine
                              virtual machines via scp.
      sign-url                Sign specified URL for use with Cloud CDN Signed
                              URLs.
      ssh                     SSH into a virtual machine instance.
""")

  def testGcloudComputeUsagePager(self):
    self.StartObjectPatch(console_io, 'IsInteractive', return_value=True)
    mock_more = self.StartObjectPatch(console_io, 'More')
    with self.assertRaises(SystemExit):
      self.cli.Execute('compute'.split())
    self.AssertErrEquals(
        'ERROR: (gcloud.compute) Command name argument expected.\n')
    contents = """\
Command name argument expected.

Available commands for gcloud compute:

  Disks
      disk-types              Read Google Compute Engine virtual disk types.
      disks                   Read and manipulate Google Compute Engine disks.

  Info
      accelerator-types       Read Google Compute Engine accelerator types.
      machine-types           Read Google Compute Engine virtual machine types.
      operations              Read and manipulate Google Compute Engine
                              operations.
      regions                 List Google Compute Engine regions.
      zones                   List Google Compute Engine zones.

  Instances
      commitments             Manage Google Compute Engine commitments.
      diagnose                Debugging tools for Google Compute Engine virtual
                              machine instances.
      images                  List, create, and delete Google Compute Engine
                              images.
      instance-groups         Read and manipulate Google Compute Engine instance
                              groups.
      instance-templates      Read and manipulate Google Compute Engine
                              instances templates.
      instances               Read and manipulate Google Compute Engine virtual
                              machine instances.
      snapshots               List, describe, and delete Google Compute Engine
                              snapshots.
      sole-tenancy            Read and manage Google Compute Engine sole-tenancy
                              resources.
      target-instances        Read and manipulate Google Compute Engine virtual
                              target instances.
      tpus                    List, create, and delete Cloud TPUs.

  Load Balancing
      backend-buckets         Read and manipulate backend buckets.
      backend-services        List, create, and delete backend services.
      forwarding-rules        Read and manipulate traffic forwarding rules to
                              network load balancers.
      health-checks           Read and manipulate health checks for load
                              balanced instances.
      http-health-checks      Read and manipulate HTTP health checks for load
                              balanced instances.
      https-health-checks     Read and manipulate HTTPS health checks for load
                              balanced instances.
      ssl-certificates        List, create, and delete Google Compute Engine SSL
                              certificates.
      ssl-policies            List, create, delete and update Google Compute
                              Engine SSL policies.
      target-pools            Control Compute Engine target pools for network
                              load balancing.

  Networking
      addresses               Read and manipulate Google Compute Engine
                              addresses.
      firewall-rules          List, create, update, and delete Google Compute
                              Engine firewall rules.
      interconnects           Read and manipulate  Google Compute Engine
                              interconnects.
      networks                List, create, and delete Google Compute Engine
                              networks.
      routers                 List, create, and delete Google Compute Engine
                              routers.
      routes                  Read and manipulate routes.
      shared-vpc              Configure shared VPC.
      target-http-proxies     List, create, and delete target HTTP proxies.
      target-https-proxies    List, create, and delete target HTTPS proxies.
      target-ssl-proxies      List, create, and delete target SSL proxies.
      target-tcp-proxies      List, create, and delete target TCP proxies.
      target-vpn-gateways     Read and manipulate Google Compute Engine VPN
                              Gateways.
      url-maps                List, create, and delete URL maps.
      vpn-tunnels             Read and manipulate Google Compute Engine VPN
                              Tunnels.

  Tools
      config-ssh              Populate SSH config files with Host entries from
                              each instance.
      connect-to-serial-port  Connect to the serial port of an instance.
      os-login                Create and manipulate Google Compute Engine OS
                              Login resources.
      project-info            Read and manipulate project-level data like quotas
                              and metadata.
      reset-windows-password  Reset and return a password for a Windows machine
                              instance.
      scp                     Copy files to and from Google Compute Engine
                              virtual machines via scp.
      sign-url                Sign specified URL for use with Cloud CDN Signed
                              URLs.
      ssh                     SSH into a virtual machine instance.

"""
    mock_more.assert_called_with(contents, out=mock.ANY)

  def testGcloudComputeInstancesUsage(self):
    # Expect to see regular usage text since no categories are defined.
    with self.assertRaises(SystemExit):
      self.cli.Execute('compute instances'.split())
    self.AssertErrEquals("""\
ERROR: (gcloud.compute.instances) Command name argument expected.

Available groups for gcloud compute instances:

      network-interfaces      Read and manipulate Google Compute Engine instance
                              network interfaces.

Available commands for gcloud compute instances:

      add-access-config           Create a Google Compute Engine virtual machine
                                  access configuration.
      add-labels                  Add labels to Google Compute Engine virtual
                                  machine instances.
      add-metadata                Add or update instance metadata.
      add-tags                    Add tags to Google Compute Engine virtual
                                  machine instances.
      attach-disk                 Attach a disk to an instance.
      create                      Create Google Compute Engine virtual machine
                                  instances.
      create-with-container       Creates Google Compute engine virtual machine
                                  instances running     container images.
      delete                      Delete Google Compute Engine virtual machine
                                  instances.
      delete-access-config        Delete an access configuration from a virtual
                                  machine network interface.
      describe                    Describe a virtual machine instance.
      detach-disk                 Detach disks from Compute Engine virtual
                                  machine instances.
      get-serial-port-output      Read output from a virtual machine instance's
                                  serial port.
      list                        List Google Compute Engine instances.
      move                        Move an instance and its attached persistent
                                  disks between zones.
      remove-labels               Remove labels from Google Compute Engine
                                  virtual machine instances.
      remove-metadata             Remove instance metadata.
      remove-tags                 Remove tags from Google Compute Engine virtual
                                  machine instances.
      reset                       Reset a virtual machine instance.
      set-disk-auto-delete        Set auto-delete behavior for disks.
      set-machine-type            Set machine type for Google Compute Engine
                                  virtual machines.
      set-scheduling              Set scheduling options for Google Compute
                                  Engine virtual machines.
      set-service-account         Set service account and scopes for a Google
                                  Compute Engine instance.
      simulate-maintenance-event  Simulate maintenance of virtual machine
                                  instances.
      start                       Start a stopped virtual machine instance.
      stop                        Stop a virtual machine instance.
      tail-serial-port-output     Periodically fetch new output from a virtual
                                  machine instance's serial port and display it
                                  as it becomes available.
      update                      Update a Google Compute Engine virtual
                                  machine.
      update-access-config        Update a Google Compute Engine virtual machine
                                  access configuration.
      update-container            Updates Google Compute engine virtual machine
                                  instances running container     images.

For detailed information on this command and its flags, run:
  gcloud compute instances --help
""")

if __name__ == '__main__':
  test_case.main()
