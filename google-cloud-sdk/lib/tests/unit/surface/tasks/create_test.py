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
"""Tests for `gcloud tasks create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.command_lib.util import time_util
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.tasks import test_base


class CreatePullTaskTest(test_base.CloudTasksAlphaTestBase):

  def SetUp(self):
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue')
    self.queue_name = self.queue_ref.RelativeName()
    self.task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue', tasksId='my-task')
    self.task_name = self.task_ref.RelativeName()

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    self.schedule_time = time_util.CalculateExpiration(20)

  def testCreate_NoOptions(self):
    expected_task = self.messages.Task(pullMessage=self.messages.PullMessage())
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-pull-task --queue my-queue')

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_Payload_Content(self):
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        pullMessage=self.messages.PullMessage(tag='tag', payload=b'payload'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-pull-task --queue my-queue '
                           'my-task --schedule-time={} --tag=tag '
                           '--payload-content=payload'.format(
                               self.schedule_time))

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_Payload_Content_Location(self):
    queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central2',
        projectsId=self.Project(), queuesId='my-queue')
    queue_name = queue_ref.RelativeName()
    task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks', locationsId='us-central2',
        projectsId=self.Project(), queuesId='my-queue', tasksId='my-task')
    task_name = task_ref.RelativeName()

    expected_task = self.messages.Task(
        name=task_name, scheduleTime=self.schedule_time,
        pullMessage=self.messages.PullMessage(tag='tag', payload=b'payload'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-pull-task --queue my-queue '
                           'my-task --schedule-time={} --tag=tag '
                           '--payload-content=payload '
                           '--location=us-central2'.format(self.schedule_time))

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_Payload_File(self):
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        pullMessage=self.messages.PullMessage(tag='tag', payload=b'payload'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    with files.TemporaryDirectory() as tmp_dir:
      self.Touch(tmp_dir, 'payload.txt', contents='payload')
      payload_file = os.path.join(tmp_dir, 'payload.txt')
      actual_task = self.Run('tasks create-pull-task --queue my-queue '
                             'my-task --schedule-time={} --tag=tag '
                             '--payload-file={}'.format(self.schedule_time,
                                                        payload_file))

      self.assertEqual(actual_task, expected_task)


class CreateAppEngineTaskTest(test_base.CloudTasksTestBase):

  def SetUp(self):
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue')
    self.queue_name = self.queue_ref.RelativeName()
    self.task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue', tasksId='my-task')
    self.task_name = self.task_ref.RelativeName()

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    self.schedule_time = time_util.CalculateExpiration(20)

  def testCreate_NoOptions(self):
    expected_task = self.messages.Task(
        appEngineHttpRequest=self.messages.AppEngineHttpRequest())
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-app-engine-task --queue my-queue')

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_Payload_Content_Location(self):
    http_method = self.messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
        'POST')
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        appEngineHttpRequest=self.messages.AppEngineHttpRequest(
            appEngineRouting=self.messages.AppEngineRouting(service='abc'),
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header1': 'value1', 'header2': 'value2'},
                self.messages.AppEngineHttpRequest.HeadersValue),
            httpMethod=http_method, body=b'body',
            relativeUri='/paths/a/'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-app-engine-task --queue my-queue '
                           'my-task --schedule-time={} '
                           '--body-content=body --method=POST '
                           '--relative-uri=/paths/a/ --header=header1:value1 '
                           '--header=header2:value2 --routing=service:abc'
                           .format(self.schedule_time))

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_Payload_Content(self):
    http_method = self.messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
        'POST')
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        appEngineHttpRequest=self.messages.AppEngineHttpRequest(
            appEngineRouting=self.messages.AppEngineRouting(service='abc'),
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header1': 'value1', 'header2': 'value2'},
                self.messages.AppEngineHttpRequest.HeadersValue),
            httpMethod=http_method, body=b'body',
            relativeUri='/paths/a/'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-app-engine-task --queue my-queue '
                           'my-task --schedule-time={} '
                           '--body-content=body --method=POST '
                           '--relative-uri=/paths/a/ --header=header1:value1 '
                           '--header=header2:value2 --routing=service:abc'
                           .format(self.schedule_time))

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_Payload_File(self):
    http_method = self.messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
        'POST')
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        appEngineHttpRequest=self.messages.AppEngineHttpRequest(
            appEngineRouting=self.messages.AppEngineRouting(service='abc'),
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header1': 'value1', 'header2': 'value2'},
                self.messages.AppEngineHttpRequest.HeadersValue),
            httpMethod=http_method, body=b'body',
            relativeUri='/paths/a/'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    with files.TemporaryDirectory() as tmp_dir:
      self.Touch(tmp_dir, 'body.txt', contents='body')
      body = os.path.join(tmp_dir, 'body.txt')
      actual_task = self.Run('tasks create-app-engine-task --queue my-queue '
                             'my-task --schedule-time={} '
                             '--body-file={} --method=POST '
                             '--relative-uri=/paths/a/ --header=header1:value1 '
                             '--header=header2:value2 --routing=service:abc'
                             .format(self.schedule_time, body))

      self.assertEqual(actual_task, expected_task)

  def testCreate__RepeatedHeadersKey(self):
    expected_task = self.messages.Task(
        appEngineHttpRequest=self.messages.AppEngineHttpRequest(
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header': 'value2'},
                self.messages.AppEngineHttpRequest.HeadersValue)))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-app-engine-task --queue my-queue '
                           '--header=header:value1 --header=header:value2')

    self.assertEqual(actual_task, expected_task)


class CreateAppEngineTaskTestBeta(CreateAppEngineTaskTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CreateHttpTaskTest(test_base.CloudTasksTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.queue_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue')
    self.queue_name = self.queue_ref.RelativeName()
    self.task_ref = resources.REGISTRY.Create(
        'cloudtasks.projects.locations.queues.tasks', locationsId='us-central1',
        projectsId=self.Project(), queuesId='my-queue', tasksId='my-task')
    self.task_name = self.task_ref.RelativeName()

    resolve_loc_mock = self.StartObjectPatch(app, 'ResolveAppLocation')
    resolve_loc_mock.return_value = (
        parsers.ParseLocation('us-central1').SelfLink())

    self.schedule_time = time_util.CalculateExpiration(20)

  def testCreate_BaseOptions(self):
    expected_task = self.messages.Task(
        httpRequest=self.messages.HttpRequest(
            url='http://somehost.com/paths/a/'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-http-task --queue my-queue '
                           '--url=http://somehost.com/paths/a/')

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_BodyContent_NoAuth(self):
    http_method = self.messages.HttpRequest.HttpMethodValueValuesEnum('POST')
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        httpRequest=self.messages.HttpRequest(
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header1': 'value1', 'header2': 'value2'},
                self.messages.HttpRequest.HeadersValue),
            httpMethod=http_method, body=b'body',
            url='http://somehost.com/paths/a/'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-http-task --queue my-queue '
                           'my-task --schedule-time={} '
                           '--body-content=body --method=POST '
                           '--url=http://somehost.com/paths/a/ '
                           '--header=header1:value1 '
                           '--header=header2:value2'
                           .format(self.schedule_time))

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_BodyFile_NoAuth(self):
    http_method = self.messages.HttpRequest.HttpMethodValueValuesEnum('POST')
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        httpRequest=self.messages.HttpRequest(
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header1': 'value1', 'header2': 'value2'},
                self.messages.HttpRequest.HeadersValue),
            httpMethod=http_method, body=b'body',
            url='http://somehost.com/paths/a/'))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    with files.TemporaryDirectory() as tmp_dir:
      self.Touch(tmp_dir, 'body.txt', contents='body')
      body = os.path.join(tmp_dir, 'body.txt')
      actual_task = self.Run('tasks create-http-task --queue my-queue '
                             'my-task --schedule-time={} '
                             '--body-file={} --method=POST '
                             '--url=http://somehost.com/paths/a/ '
                             '--header=header1:value1 '
                             '--header=header2:value2'
                             .format(self.schedule_time, body))

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_Oidc(self):
    http_method = self.messages.HttpRequest.HttpMethodValueValuesEnum('POST')
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        httpRequest=self.messages.HttpRequest(
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header1': 'value1', 'header2': 'value2'},
                self.messages.HttpRequest.HeadersValue),
            httpMethod=http_method, body=b'body',
            url='http://somehost.com/paths/a/',
            oidcToken=self.messages.OidcToken(
                serviceAccountEmail='some.email@org.com',
                audience='some-audience')))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-http-task --queue my-queue '
                           'my-task --schedule-time={} '
                           '--body-content=body --method=POST '
                           '--url=http://somehost.com/paths/a/ '
                           '--header=header1:value1 '
                           '--header=header2:value2 '
                           '--oidc-service-account-email=some.email@org.com '
                           '--oidc-token-audience=some-audience'
                           .format(self.schedule_time))

    self.assertEqual(actual_task, expected_task)

  def testCreate_AllOptions_OAuth(self):
    http_method = self.messages.HttpRequest.HttpMethodValueValuesEnum('POST')
    expected_task = self.messages.Task(
        name=self.task_name, scheduleTime=self.schedule_time,
        httpRequest=self.messages.HttpRequest(
            headers=encoding.DictToAdditionalPropertyMessage(
                {'header1': 'value1', 'header2': 'value2'},
                self.messages.HttpRequest.HeadersValue),
            httpMethod=http_method, body=b'body',
            url='http://somehost.com/paths/a/',
            oauthToken=self.messages.OAuthToken(
                serviceAccountEmail='some.email@org.com',
                scope='some-scope')))
    self.tasks_service.Create.Expect(
        self.messages.CloudtasksProjectsLocationsQueuesTasksCreateRequest(
            parent=self.queue_name,
            createTaskRequest=self.messages.CreateTaskRequest(
                task=expected_task)),
        response=expected_task)

    actual_task = self.Run('tasks create-http-task --queue my-queue '
                           'my-task --schedule-time={} '
                           '--body-content=body --method=POST '
                           '--url=http://somehost.com/paths/a/ '
                           '--header=header1:value1 '
                           '--header=header2:value2 '
                           '--oauth-service-account-email=some.email@org.com '
                           '--oauth-token-scope=some-scope'
                           .format(self.schedule_time))

    self.assertEqual(actual_task, expected_task)


class CreateHttpTaskTestAlpha(CreateHttpTaskTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_track = calliope_base.ReleaseTrack.BETA


class CreateHttpTaskTestBeta(CreateHttpTaskTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


if __name__ == '__main__':
  test_case.main()
