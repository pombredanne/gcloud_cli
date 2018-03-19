# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud tasks queues` create commands."""

from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.tasks import test_base


class CreateTestBase(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.location_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations', locationsId='us-central1',
        projectsId=self.Project())
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue')
    self.queue_name = self.queue_ref.RelativeName()

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())


class CreatePullQueueTest(CreateTestBase):

  def testCreate_NoOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name, pullTarget=self.messages.PullTarget())
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        response=expected_queue)

    actual_queue = self.Run('tasks queues create-pull-queue my-queue')

    self.assertEqual(actual_queue, expected_queue)
    self.AssertErrContains(constants.QUEUE_MANAGEMENT_WARNING)

  def testCreate_AllOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name, pullTarget=self.messages.PullTarget(),
        retryConfig=self.messages.RetryConfig(maxAttempts=10,
                                              maxRetryDuration='5s'))
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        response=expected_queue)

    actual_queue = self.Run('tasks queues create-pull-queue my-queue '
                            '--max-attempts=10 --max-retry-duration=5s')

    self.assertEqual(actual_queue, expected_queue)
    self.AssertErrContains(constants.QUEUE_MANAGEMENT_WARNING)

  def testCreate_AllOptions_MaxAttemptsUnlimited(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name, pullTarget=self.messages.PullTarget(),
        retryConfig=self.messages.RetryConfig(unlimitedAttempts=True,
                                              maxRetryDuration='5s'))
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        response=expected_queue)

    actual_queue = self.Run('tasks queues create-pull-queue my-queue '
                            '--max-attempts=unlimited --max-retry-duration=5s')

    self.assertEqual(actual_queue, expected_queue)
    self.AssertErrContains(constants.QUEUE_MANAGEMENT_WARNING)

  def testCreate_IncludeAppEngineArgs(self):
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('tasks queues create-pull-queue my-queue --max-attempts=10 '
               '--max-retry-duration=5s --max-doublings=4 --min-backoff=1s '
               '--max-backoff=10s --max-tasks-dispatched-per-second=100 '
               '--max-concurrent-tasks=10')

  def testCreate_AllOptions_Location(self):
    location_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations', locationsId='us-central2',
        projectsId=self.Project())
    queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central2',
        projectsId=self.Project(), queuesId='my-queue')
    queue_name = queue_ref.RelativeName()

    expected_queue = self.messages.Queue(
        name=queue_name, pullTarget=self.messages.PullTarget(),
        retryConfig=self.messages.RetryConfig(maxAttempts=10,
                                              maxRetryDuration='5s'))
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=location_ref.RelativeName(), queue=expected_queue),
        response=expected_queue)

    actual_queue = self.Run('tasks queues create-pull-queue my-queue '
                            '--max-attempts=10 --max-retry-duration=5s '
                            '--location=us-central2')

    self.assertEqual(actual_queue, expected_queue)
    self.AssertErrContains(constants.QUEUE_MANAGEMENT_WARNING)


class CreateAppEngineQueueTest(CreateTestBase):

  def testCreate_NoOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpTarget=self.messages.AppEngineHttpTarget())
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        response=expected_queue)

    actual_queue = self.Run('tasks queues create-app-engine-queue my-queue')

    self.assertEqual(actual_queue, expected_queue)
    self.AssertErrContains(constants.QUEUE_MANAGEMENT_WARNING)

  def testCreate_AllOptions(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpTarget=self.messages.AppEngineHttpTarget(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='abc')),
        retryConfig=self.messages.RetryConfig(maxAttempts=10,
                                              maxRetryDuration='5s',
                                              maxDoublings=4, minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxTasksDispatchedPerSecond=100, maxConcurrentTasks=10))
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        response=expected_queue)

    actual_queue = self.Run('tasks queues create-app-engine-queue my-queue '
                            '--max-attempts=10 --max-retry-duration=5s '
                            '--max-doublings=4 --min-backoff=1s '
                            '--max-backoff=10s '
                            '--max-tasks-dispatched-per-second=100 '
                            '--max-concurrent-tasks=10 '
                            '--routing-override=service:abc')

    self.assertEqual(actual_queue, expected_queue)
    self.AssertErrContains(constants.QUEUE_MANAGEMENT_WARNING)

  def testCreate_AllOptions_MaxAttemptsUnlimited(self):
    expected_queue = self.messages.Queue(
        name=self.queue_name,
        appEngineHttpTarget=self.messages.AppEngineHttpTarget(
            appEngineRoutingOverride=self.messages.AppEngineRouting(
                service='abc')),
        retryConfig=self.messages.RetryConfig(unlimitedAttempts=True,
                                              maxRetryDuration='5s',
                                              maxDoublings=4,
                                              minBackoff='1s',
                                              maxBackoff='10s'),
        rateLimits=self.messages.RateLimits(
            maxTasksDispatchedPerSecond=100, maxConcurrentTasks=10))
    self.queues_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
            parent=self.location_ref.RelativeName(), queue=expected_queue),
        response=expected_queue)

    actual_queue = self.Run('tasks queues create-app-engine-queue my-queue '
                            '--max-attempts=unlimited --max-retry-duration=5s '
                            '--max-doublings=4 --min-backoff=1s '
                            '--max-backoff=10s '
                            '--max-tasks-dispatched-per-second=100 '
                            '--max-concurrent-tasks=10 '
                            '--routing-override=service:abc')

    self.assertEqual(actual_queue, expected_queue)
    self.AssertErrContains(constants.QUEUE_MANAGEMENT_WARNING)


if __name__ == '__main__':
  test_case.main()