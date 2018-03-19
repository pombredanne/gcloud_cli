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

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import command_loading
from tests.lib import sdk_test_base
from tests.lib import test_case


def _FromModule(mod_file, module_attributes, release_track, is_command):
  implementations = command_loading._ImplementationsFromModule(
      mod_file, module_attributes, is_command)
  return command_loading._ExtractReleaseTrackImplementation(
      mod_file, release_track, implementations)()


def _FromYaml(impl_file, path, data, release_track,
              yaml_command_translator):
  implementations = command_loading._ImplementationsFromYaml(
      path, data, yaml_command_translator)
  return command_loading._ExtractReleaseTrackImplementation(
      impl_file, release_track, implementations)()


class BaseTest(sdk_test_base.SdkBase):
  """Test the command and group blase class in calliope."""

  FORMAT_ALPHA = 'alpha'
  FORMAT_BETA = 'beta'
  FORMAT = 'ga'

  class NoTracks(base.Group):
    pass

  @base.ReleaseTracks(base.ReleaseTrack.GA)
  class GA(base.Group):
    pass

  @base.ReleaseTracks(base.ReleaseTrack.GA)
  class GACommand(base.Command):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @base.ReleaseTracks(base.ReleaseTrack.ALPHA)
  class Alpha(base.Group):
    pass

  @base.ReleaseTracks(base.ReleaseTrack.ALPHA)
  class AlphaCommand(base.Command):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @base.ReleaseTracks(base.ReleaseTrack.BETA)
  class Beta(base.Group):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
  class AlphaBeta(base.Group):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @base.ReleaseTracks(*base.ReleaseTrack.AllValues())
  class All(base.Group):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  def testEmpty(self):
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'No commands defined in file: \[file\]'):
      _FromModule('file', [], base.ReleaseTrack.GA, is_command=True)
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'No command groups defined in file: \[file\]'):
      _FromModule('file', [], base.ReleaseTrack.GA, is_command=False)

  def testMultipleDefs(self):
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[ALPHA\] for element: '
        r'\[file\]'):
      _FromModule(
          'file', [BaseTest.Alpha, BaseTest.AlphaBeta],
          base.ReleaseTrack.GA, is_command=False)
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[.+, .+\] for element: '
        r'\[file\]'):
      _FromModule(
          'file', [BaseTest.Alpha, BaseTest.Beta, BaseTest.AlphaBeta],
          base.ReleaseTrack.GA, is_command=False)
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'Multiple implementations defined for element: \[file\]. Each must '
        r'explicitly declare valid release tracks.'):
      _FromModule(
          'file', [BaseTest.Alpha, BaseTest.NoTracks],
          base.ReleaseTrack.GA, is_command=False)

  def testGroup(self):
    items = [base.Group]
    # A single group can be found.
    self.assertEquals(
        base.Group,
        _FromModule('file', items, base.ReleaseTrack.GA, is_command=False))
    # Allow a group to not define tracks and still work.
    self.assertEquals(
        base.Group,
        _FromModule('file', items, base.ReleaseTrack.ALPHA, is_command=False))
    # A group is registered but there should be a command.
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'You cannot define groups \[Group\] in a command file: \[file\]'):
      _FromModule(
          'file', items, base.ReleaseTrack.GA, is_command=True)
    # No matches for the release track.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GA], base.ReleaseTrack.ALPHA, is_command=False)
    # Explicitly tracked group can be found.
    self.assertEquals(
        BaseTest.GA,
        _FromModule(
            'file', [BaseTest.GA], base.ReleaseTrack.GA, is_command=False))
    # Make sure we pick the right one.
    self.assertEquals(
        BaseTest.GA,
        _FromModule(
            'file', [BaseTest.GA, BaseTest.Alpha], base.ReleaseTrack.GA,
            is_command=False))
    # No matches with multiple choices.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GA, BaseTest.Alpha], base.ReleaseTrack.BETA,
          is_command=False)

  def testCommand(self):
    items = [base.Command]
    # A single command can be found.
    self.assertEquals(
        base.Command,
        _FromModule('file', items, base.ReleaseTrack.GA, is_command=True))
    # Allow a command to not define tracks and still work.
    self.assertEquals(
        base.Command,
        _FromModule(
            'file', items, base.ReleaseTrack.ALPHA, is_command=True))
    # A command is registered but there should be a group.
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'You cannot define commands \[Command\] in a command group file: '
        r'\[file\]'):
      _FromModule(
          'file', items, base.ReleaseTrack.GA, is_command=False)
    # No matches for the release track.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GACommand], base.ReleaseTrack.ALPHA,
          is_command=True)
    # Explicitly tracked command can be found.
    self.assertEquals(
        BaseTest.GACommand,
        _FromModule('file', [BaseTest.GACommand], base.ReleaseTrack.GA,
                    is_command=True))
    # Make sure we pick the right one.
    self.assertEquals(
        BaseTest.GACommand,
        _FromModule(
            'file', [BaseTest.GACommand, BaseTest.AlphaCommand],
            base.ReleaseTrack.GA, is_command=True))
    # No matches with multiple choices.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GACommand, BaseTest.AlphaCommand],
          base.ReleaseTrack.BETA, is_command=True)

  def testGetTrackedAttribute(self):
    self.assertEqual(BaseTest.FORMAT, BaseTest.GACommand().Run())
    self.assertEqual(BaseTest.FORMAT_ALPHA, BaseTest.AlphaCommand().Run())
    self.assertEqual(BaseTest.FORMAT_BETA, BaseTest.Beta().Run())
    self.assertEqual(BaseTest.FORMAT_BETA, BaseTest.AlphaBeta().Run())
    self.assertEqual(BaseTest.FORMAT_BETA, BaseTest.All().Run())


class YamlTests(sdk_test_base.SdkBase):

  def testNoTranslator(self):
    with self.assertRaisesRegexp(
        command_loading.CommandLoadFailure,
        r'Problem loading foo.bar: No yaml command translator has been '
        r'registered.'):
      _FromYaml(
          'file', ['foo', 'bar'], [], base.ReleaseTrack.GA, None)

  def testNoGroups(self):
    with self.assertRaisesRegexp(
        command_loading.CommandLoadFailure,
        r'Problem loading foo.bar: Command groups cannot be implemented in '
        r'yaml.'):
      command_loading.LoadCommonType(
          ['dir/foo/bar.yaml'], ['foo', 'bar'], base.ReleaseTrack.GA,
          'id', is_command=False)
    with self.assertRaisesRegexp(
        command_loading.CommandLoadFailure,
        r'Problem loading foo.bar: Command groups cannot be implemented in '
        r'yaml.'):
      command_loading.FindSubElements(
          ['dir/foo/bar.py', 'dir/foo/bar.yaml'],
          ['foo', 'bar'])

  def testNoMatchingTrack(self):
    with self.assertRaisesRegexp(
        command_loading.ReleaseTrackNotImplementedException,
        r'No implementation for release track \[GA\] for element: \[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'], [], base.ReleaseTrack.GA, object())
    with self.assertRaisesRegexp(
        command_loading.ReleaseTrackNotImplementedException,
        r'No implementation for release track \[GA\] for element: \[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'], [{'release_tracks': ['ALPHA']}],
          base.ReleaseTrack.GA, object())
    with self.assertRaisesRegexp(
        command_loading.ReleaseTrackNotImplementedException,
        r'No implementation for release track \[GA\] for element: \[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {'release_tracks': ['BETA']}],
          base.ReleaseTrack.GA, object())

  def testMultipleDefs(self):
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[ALPHA\] for element: '
        r'\[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {'release_tracks': ['ALPHA']}],
          base.ReleaseTrack.ALPHA, object())
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[.+, .+\] for element: '
        r'\[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {'release_tracks': ['BETA']},
           {'release_tracks': ['ALPHA', 'BETA']}],
          base.ReleaseTrack.ALPHA, object())
    with self.assertRaisesRegexp(
        command_loading.LayoutException,
        r'Multiple implementations defined for element: \[file\]. Each must '
        r'explicitly declare valid release tracks.'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {},],
          base.ReleaseTrack.ALPHA, object())

  def testCommand(self):
    # A stub translator.
    sentinel = object()

    class Translator(command_loading.YamlCommandTranslator):

      def Translate(self, path, command_data):
        return sentinel, command_data.get('release_tracks')

    t = Translator()

    # A single command can be found.
    self.assertEquals(
        (sentinel, None),
        _FromYaml(
            'file', ['foo', 'bar'], [{}], base.ReleaseTrack.GA, t))
    # Explicitly tracked command can be found.
    self.assertEquals(
        (sentinel, ['GA']),
        _FromYaml(
            'file', ['foo', 'bar'], [{'release_tracks': ['GA']}],
            base.ReleaseTrack.GA, t))
    # Make sure we pick the right one.
    self.assertEquals(
        (sentinel, ['GA']),
        _FromYaml(
            'file', ['foo', 'bar'],
            [{'release_tracks': ['GA']}, {'release_tracks': ['ALPHA']}],
            base.ReleaseTrack.GA, t))
    # No matches with multiple choices.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GACommand, BaseTest.AlphaCommand],
          base.ReleaseTrack.BETA, is_command=True)

    # Check loading from file.
    self.Touch(self.temp_path, 'bar.yaml', """
- release_tracks: [GA, BETA]
- release_tracks: [ALPHA]""")
    self.assertEquals(
        (sentinel, ['GA', 'BETA']),
        command_loading.LoadCommonType(
            [os.path.join(self.temp_path, 'bar.yaml')], ['bar'],
            base.ReleaseTrack.GA, 'id', is_command=True,
            yaml_command_translator=t))


if __name__ == '__main__':
  test_case.main()