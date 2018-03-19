# Copyright 2014 Google Inc. All Rights Reserved.
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

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.logging import base


class SinksUpdateTest(base.LoggingTestBase):

  def testUpdateSuccess(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination='dest', filter='bar')
    self.mock_client_v2.projects_sinks.Update.Expect(
        self.msgs.LoggingProjectsSinksUpdateRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=updated_sink, uniqueWriterIdentity=True),
        updated_sink)
    self.RunLogging(
        'sinks update my-sink dest --log-filter=bar --format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputContains('dest')
    self.AssertOutputContains('bar')
    self.AssertOutputNotContains(test_sink.destination)

  def testUpdateSuccessOtherFieldsPreserved(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='foo@bar.com', includeChildren=True,
        startTime='start_time')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination='dest', filter='foo',
        includeChildren=True, startTime='start_time')
    self.mock_client_v2.projects_sinks.Update.Expect(
        self.msgs.LoggingProjectsSinksUpdateRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=updated_sink, uniqueWriterIdentity=True),
        updated_sink)
    self.RunLogging('sinks update my-sink dest --format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputContains('destination: dest')
    self.AssertOutputContains('filter: foo')
    self.AssertOutputContains('includeChildren: true')
    self.AssertOutputContains('startTime: start_time')
    self.AssertOutputNotContains(test_sink.destination)

  def testUpdateSuccessToEmptyFilter(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='foo@bar.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination=test_sink.destination, filter='')
    self.mock_client_v2.projects_sinks.Update.Expect(
        self.msgs.LoggingProjectsSinksUpdateRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=updated_sink, uniqueWriterIdentity=True),
        updated_sink)
    self.RunLogging('sinks update my-sink --log-filter="" --format=default')
    self.AssertErrContains('Updated')
    self.AssertOutputContains('base')
    self.AssertOutputNotContains(test_sink.filter)

  def testUpdatePrompt(self):
    test_sink = self.msgs.LogSink(
        name='my-sink', destination='base', filter='foo',
        writerIdentity='cloud-logs@google.com')
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    with self.AssertRaisesExceptionMatches(console_io.OperationCancelledError,
                                           'Aborted by user.'):
      self.RunLogging('sinks update my-sink --log-filter=new')

    # Now answer Yes.
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        test_sink)
    updated_sink = self.msgs.LogSink(
        name=test_sink.name, destination=test_sink.destination, filter='new')
    self.mock_client_v2.projects_sinks.Update.Expect(
        self.msgs.LoggingProjectsSinksUpdateRequest(
            sinkName='projects/my-project/sinks/my-sink',
            logSink=updated_sink, uniqueWriterIdentity=True),
        updated_sink)
    self.WriteInput('Y')
    self.RunLogging('sinks update my-sink --log-filter=new')
    self.AssertErrContains('Updated')

  def testUpdateMissingSink(self):
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        exception=http_error.MakeHttpError(404))
    with self.AssertRaisesHttpExceptionMatches('not found'):
      self.RunLogging('sinks update my-sink new-dest')
    self.AssertErrContains('not found')

  def testUpdateMissingRequiredFlag(self):
    with self.AssertRaisesExceptionRegexp(exceptions.MinimumArgumentException,
                                          r'Please specify.*'):
      self.RunLogging('sinks update my-sink')

  def testListNoPerms(self):
    self.mock_client_v2.projects_sinks.Get.Expect(
        self.msgs.LoggingProjectsSinksGetRequest(
            sinkName='projects/my-project/sinks/my-sink'),
        exception=http_error.MakeHttpError(403))
    self.RunWithoutPerms('sinks update my-sink dest')

  def testListNoProject(self):
    self.RunWithoutProject('sinks update my-sink dest')

  def testListNoAuth(self):
    self.RunWithoutAuth('sinks update my-sink dest')


if __name__ == '__main__':
  test_case.main()