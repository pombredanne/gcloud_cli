# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for `gcloud tasks run`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.tasks import test_base


class TasksRunTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.location_id = 'us-central1'
    self.location_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations', locationsId=self.location_id,
        projectsId=self.Project())
    self.queue_id = 'my-queue'
    self.task_id = 'my-task'
    self.task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks',
        locationsId=self.location_id,
        projectsId=self.Project(),
        queuesId=self.queue_id, tasksId=self.task_id)

    self.resolve_loc_mock = self.StartObjectPatch(
        app, 'ResolveAppLocation',
        return_value=parsers.ParseLocation('us-central1').SelfLink())

    properties.VALUES.core.user_output_enabled.Set(False)

  def testRun(self):
    expected = self.messages.Task(name=self.task_ref.RelativeName())
    self.tasks_service.Run.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRunRequest(
            name=self.task_ref.RelativeName()),
        response=expected)

    actual = self.Run('tasks run {} --queue {}'.format(self.task_id,
                                                       self.queue_id))

    self.assertEqual(expected, actual)
    self.resolve_loc_mock.assert_called_once_with(parsers.ParseProject())

  def testRun_RelativeName(self):
    task_name = ('projects/other-project/locations/us-central1/queues/my-queue'
                 '/tasks/my-task')
    expected = self.messages.Task(name=task_name)
    self.tasks_service.Run.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRunRequest(
            name=task_name),
        response=expected)

    actual = self.Run('tasks run {}'.format(task_name))

    self.assertEqual(actual, expected)
    self.resolve_loc_mock.assert_not_called()

  def testRun_Location(self):
    location_id = 'us-central2'
    task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks',
        locationsId=location_id,
        projectsId=self.Project(),
        queuesId=self.queue_id, tasksId=self.task_id)

    expected = self.messages.Task(name=task_ref.RelativeName())
    self.tasks_service.Run.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRunRequest(
            name=task_ref.RelativeName()),
        response=expected)

    actual = self.Run('tasks run {} --queue {} --location=us-central2'.format(
        self.task_id, self.queue_id))

    self.assertEqual(expected, actual)

  def testRun_NonExistentTask(self):
    self.tasks_service.Run.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRunRequest(
            name='projects/{}/locations/us-central1/queues/my-queue/'
            'tasks/my-task'.format(self.Project())),
        exception=http_error.MakeDetailedHttpError(
            code=404,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks run {} --queue {}'.format(self.task_id, self.queue_id))

    self.AssertErrContains('Requested entity was not found.')

  def testRun_CompletedTask(self):
    self.tasks_service.Run.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRunRequest(
            name='projects/{}/locations/us-central1/queues/my-queue/'
            'tasks/my-task'.format(self.Project())),
        exception=http_error.MakeDetailedHttpError(
            code=404,
            message='Requested entity was not found.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks run {} --queue {}'.format(self.task_id, self.queue_id))

    self.AssertErrContains('Requested entity was not found.')

  def testRun_RunningTask(self):
    self.tasks_service.Run.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksRunRequest(
            name='projects/{}/locations/us-central1/queues/my-queue/'
            'tasks/my-task'.format(self.Project())),
        exception=http_error.MakeDetailedHttpError(
            code=400,
            message='RunTask cannot be called on an already running task.'))

    with self.assertRaises(exceptions.HttpException):
      self.Run('tasks run {} --queue {}'.format(self.task_id, self.queue_id))

    self.AssertErrContains(
        'RunTask cannot be called on an already running task.')


class TasksRunTestBeta(TasksRunTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
