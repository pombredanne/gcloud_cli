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
"""Tests for gcloud preview app gen-repo-info-file."""

import json
import os

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from googlecloudsdk.third_party.appengine.tools import context_util


class GenRepoInfoFileTest(sdk_test_base.WithTempCWD, cli_test_base.CliTestBase):

  def SetUp(self):
    self.cloud_repo_ctx = {
        'context': {
            'cloudRepo': {
                'repoId': {
                    'projectRepoId': {
                        'projectId': 'test_proj',
                        'repoName': 'default'}},
                'revisionId': '12345abcde'}},
        'labels': {'category': 'remote_repo'}}
    self.calculate_mock = self.StartObjectPatch(
        context_util, 'CalculateExtendedSourceContexts',
        return_value=[self.cloud_repo_ctx])
    self.ctx_json = json.dumps(self.cloud_repo_ctx['context'], indent=2,
                               sort_keys=True)
    self.ext_ctx_json = json.dumps([self.cloud_repo_ctx], indent=2,
                                   sort_keys=True)
    self.track = calliope_base.ReleaseTrack.BETA

  def testDefaults(self):
    self.Run('app gen-repo-info-file')
    self.calculate_mock.assert_called_with('.')
    with open(context_util.CONTEXT_FILENAME, 'r') as f:
      self.assertEqual(f.read(), self.ctx_json)

  def testSourceDirectoryChanged(self):
    self.Run('app gen-repo-info-file --source-directory="src"')
    self.calculate_mock.assert_called_with('src')

  def testOutputFileChanged(self):
    self.Run('app gen-repo-info-file --output-file="{0}"'.format(
        os.path.join('a', 'my-file.txt')))
    self.calculate_mock.assert_called_with('.')
    with open(os.path.join('a', 'my-file.txt'), 'r') as f:
      self.assertEqual(f.read(), self.ctx_json)

  def testContextFileDirectoryChanged(self):
    self.Run('app gen-repo-info-file --output-directory="{0}"'.format(
        os.path.join('a', 'b', 'c')))
    self.calculate_mock.assert_called_with('.')
    with open(
        os.path.join('a', 'b', 'c', context_util.CONTEXT_FILENAME), 'r') as f:
      self.assertEqual(f.read(), self.ctx_json)

if __name__ == '__main__':
  test_case.main()