# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Tests of the 'sinks' subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class LogsDeleteTest(base.LoggingTestBase):

  def testDeletePromptNo(self):
    self.WriteInput('n')
    with self.assertRaisesRegex(
        console_io.OperationCancelledError, 'Aborted by user.'):
      self.RunLogging('logs delete my-log')

  def testDeletePromptYes(self):
    self.WriteInput('Y')
    self.mock_client_v2.projects_logs.Delete.Expect(
        self.msgs.LoggingProjectsLogsDeleteRequest(
            logName='projects/my-project/logs/my%2Flog'),
        self.msgs.Empty())
    self.RunLogging('logs delete my/log')
    self.AssertErrContains('Deleted [my/log]')

  def testDeleteNoPerms(self):
    self.mock_client_v2.projects_logs.Delete.Expect(
        self.msgs.LoggingProjectsLogsDeleteRequest(
            logName='projects/my-project/logs/my-log'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('logs delete my-log')

  def testDeleteNoProject(self):
    self.RunWithoutProject('logs delete my-log')

  def testDeleteNoAuth(self):
    self.RunWithoutAuth('logs delete my-log')


if __name__ == '__main__':
  test_case.main()
