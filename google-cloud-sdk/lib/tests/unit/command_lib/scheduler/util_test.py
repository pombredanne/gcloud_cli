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
"""Tests for Cloud Scheduler Utilities."""

from apitools.base.py import encoding
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.app.api import appengine_api_client_base
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.app import create_util
from googlecloudsdk.command_lib.scheduler import util as util
from googlecloudsdk.command_lib.tasks import app as tasks_app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.apitools import retry
from tests.lib.surface.app import api_test_util as app_api_test_util


class ResolveAppLocationTestBase(sdk_test_base.WithFakeAuth,
                                 test_case.WithOutputCapture):

  def SetUp(self):
    app_engine_api_version = (
        appengine_api_client_base.AppengineApiClientBase.ApiVersion())
    self.app_engine_client = mock.Client(
        apis.GetClientClass('appengine', app_engine_api_version))
    self.app_engine_client.Mock()
    self.addCleanup(self.app_engine_client.Unmock)
    self.app_engine_messages = apis.GetMessagesModule('appengine',
                                                      app_engine_api_version)
    self.app_id = 'fake-project'
    self.addCleanup(properties.VALUES.core.project.Set,
                    properties.VALUES.core.project.Get())
    properties.VALUES.core.project.Set(self.app_id)
    self.app_name = 'apps/{0}'.format(self.app_id)
    self.StartPatch('time.sleep')
    self.app_location_resolver = util.AppLocationResolver()


class ResolveExistingAppLocationTests(ResolveAppLocationTestBase):

  def testResolveLocation(self):
    self.app_engine_client.apps.Get.Expect(
        self.app_engine_messages.AppengineAppsGetRequest(name=self.app_name),
        self.app_engine_messages.Application(name=self.app_name,
                                             locationId='us-central1'))

    actual_location = self.app_location_resolver()
    expected_location = 'us-central1'
    self.assertEqual(actual_location, expected_location)
    # Call it again to make sure no more API calls are made
    actual_location = self.app_location_resolver()
    self.assertEqual(actual_location, expected_location)
    self.AssertErrEquals('')

  def testResolveLocation_MultiRegional(self):
    self.app_engine_client.apps.Get.Expect(
        self.app_engine_messages.AppengineAppsGetRequest(name=self.app_name),
        self.app_engine_messages.Application(name=self.app_name,
                                             locationId='us-central'))

    actual_location = self.app_location_resolver()
    expected_location = constants.CLOUD_MULTIREGION_TO_REGION_MAP['us-central']
    self.assertEqual(actual_location, expected_location)
    self.AssertErrEquals('')


class ResolveNonExistingAppLocationTests(ResolveAppLocationTestBase,
                                         test_case.WithInput):

  def SetUp(self):
    self.app_engine_client.apps.Get.Expect(
        self.app_engine_messages.AppengineAppsGetRequest(name=self.app_name),
        exception=http_error.MakeHttpError(code=404))
    self.StartObjectPatch(console_io, 'CanPrompt', return_value=True)

  def _ExpectCreateAppRequest(self):
    app_msg = self.app_engine_messages.Application(id=self.app_id,
                                                   locationId='us-central')
    op_name = app_api_test_util.AppOperationName(self.app_id)
    intermediate_response = self.app_engine_messages.Operation(name=op_name)
    final_response = self.app_engine_messages.Operation(
        name=op_name,
        done=True,
        response=encoding.JsonToMessage(
            self.app_engine_messages.Operation.ResponseValue,
            encoding.MessageToJson(app_msg)))
    op_get_request = self.app_engine_messages.AppengineAppsOperationsGetRequest
    retry.ExpectWithRetries(
        method=self.app_engine_client.apps.Create,
        polling_method=self.app_engine_client.apps_operations.Get,
        request=app_msg, polling_request=op_get_request(name=op_name),
        response=intermediate_response, final_response=final_response,
        num_retries=2)

  def testResolveLocation_CreateApp(self):
    self.WriteInput('y')  # Would you like to create one (Y/n)?
    self.WriteInput('1')  # [1] us-central   (supports standard and flexible)
    self._ExpectCreateAppRequest()
    self.app_engine_client.apps.Get.Expect(
        self.app_engine_messages.AppengineAppsGetRequest(name=self.app_name),
        self.app_engine_messages.Application(name=self.app_name,
                                             locationId='us-central1'))

    actual_location = self.app_location_resolver()
    expected_location = 'us-central1'
    self.assertEqual(actual_location, expected_location)
    self.AssertErrContains('You are creating an app for project [fake-project]')
    self.AssertErrContains(
        'Creating an App Engine application for a project is irreversible')
    self.AssertErrContains('only those in which the Cloud Scheduler API')

  def testResolveLocation_CreateApp_Cancel(self):
    self.WriteInput('n')  # Would you like to create one (Y/n)?

    with self.assertRaises(tasks_app.RegionResolvingError):
      self.app_location_resolver()
    self.AssertErrContains(
        'There is no App Engine app in project [fake-project]')
    self.AssertErrContains('Would you like to create one')

  def testResolveLocation_CreateApp_RaceCollision(self):
    self.WriteInput('y')  # Would you like to create one (Y/n)?
    self.WriteInput('1')  # [1] us-central   (supports standard and flexible)
    self.app_engine_client.apps.Create.Expect(
        self.app_engine_messages.Application(id=self.app_id,
                                             locationId='us-central'),
        exception=http_error.MakeHttpError(code=409))

    with self.assertRaises(create_util.AppAlreadyExistsError):
      self.app_location_resolver()


if __name__ == '__main__':
  test_case.main()
