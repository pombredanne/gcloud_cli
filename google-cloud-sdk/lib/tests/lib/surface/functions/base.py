# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Base class for all Functions commands tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.util import gcloudignore
from googlecloudsdk.core.util import archive
from googlecloudsdk.core.util import files as file_utils
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base

import mock

NO_PROJECT_REGEXP = r'The required property \[project\] is not currently set'
NO_PROJECT_RESOURCE_ARG_REGEXP = r'Failed to find attribute \[project\]'
NO_AUTH_REGEXP = (r'Your current active account \[.*\] does not have any valid '
                  'credentials')
OP_FAILED_REGEXP = r'OperationError: code=13, message=Operation has failed.'
STACKDRIVER_LOG_STDERR_TEMPLATE = """\
For Cloud Build Stackdriver Logs, visit: https://console.cloud.google.com/logs/\
viewer?project={project}&advancedFilter=resource.type%3Dbuild%0A\
resource.labels.build_id%3D{build_id}%0A\
logName%3Dprojects%2F{project}%2Flogs%2Fcloudbuild
"""


class FunctionsTestBase(sdk_test_base.WithFakeAuth,
                        cli_test_base.CliTestBase,
                        parameterized.TestCase):
  """Base class for tests in functions package. Project is not set here."""

  def SetUp(self):
    # TODO(b/36553351): Untangle tests.
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudfunctions', 'v1'),
        real_client=core_apis.GetClientInstance('cloudfunctions', 'v1',
                                                no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = core_apis.GetMessagesModule('cloudfunctions', 'v1')
    self.track = calliope_base.ReleaseTrack.GA
    self._region = 'us-central1'
    self._operation_name = 'operations/operation'
    self._build_id = 'build-123'
    self.StartPatch('time.sleep')
    self.mock_resource_manager_client = apitools_mock.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'),
        real_client=core_apis.GetClientInstance(
            'cloudresourcemanager', 'v1', no_http=True))
    self.mock_resource_manager_client.Mock()
    self.addCleanup(self.mock_resource_manager_client.Unmock)
    self.resource_manager_messages = core_apis.GetMessagesModule(
        'cloudresourcemanager', 'v1')

  def ReturnUnderMaxSize(self, *unused_args, **unused_kwargs):
    return 50 * 2**20 + 1

  def ReturnLargeFileSize(self, *unused_args, **unused_kwargs):
    return 512 * 2**20 + 1

  def MockUnpackedSourcesDirSize(self):
    self.StartObjectPatch(
        file_utils, 'GetTreeSizeBytes', self.ReturnUnderMaxSize)

  def MockChooserAndMakeZipFromFileList(self):
    mock_chooser = mock.MagicMock(gcloudignore.FileChooser)
    mock_chooser.GetIncludedFiles.return_value = []
    self.StartObjectPatch(
        gcloudignore, 'GetFileChooserForDir', return_value=mock_chooser)
    self.StartObjectPatch(archive, 'MakeZipFromDir')

  def GetRegion(self):
    return self._region

  def SetRegion(self, region):
    self._region = region

  def GetOperationName(self):
    return self._operation_name

  def GetBuildId(self):
    return self._build_id

  def _GenerateFailedStatus(self):
    failed_status = self.messages.Status()
    failed_status.code = 13
    failed_status.message = 'Operation has failed.'
    return failed_status

  def _GenerateMetadata(self):
    operation_metadata = self.messages.OperationMetadataV1()
    operation_metadata.buildId = self.GetBuildId()

    return encoding.PyValueToMessage(
        self.messages.Operation.MetadataValue,
        encoding.MessageToPyValue(operation_metadata))

  def _GenerateActiveOperation(self, name):
    operation = self.messages.Operation()
    operation.name = name
    operation.metadata = self._GenerateMetadata()
    return operation

  def _GenerateFailedOperation(self, name):
    operation = self.messages.Operation()
    operation.name = name
    operation.done = True
    operation.error = self._GenerateFailedStatus()
    operation.metadata = self._GenerateMetadata()
    return operation

  def _GenerateSuccessfulOperation(self, name):
    operation = self.messages.Operation()
    operation.name = name
    operation.done = True
    operation.metadata = self._GenerateMetadata()
    return operation

  def MockRemoveIamPolicy(self, function_name, region=None):
    initial_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:existinguser@google.com', 'allUsers'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    updated_policy = self.messages.Policy(
        bindings=[
            self.messages.Binding(
                role='roles/cloudfunctions.invoker',
                members=['user:existinguser@google.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    function_path = 'projects/{}/locations/{}/functions/{}'.format(
        self.Project(), region or self.GetRegion(), function_name)
    self.mock_client.projects_locations_functions.GetIamPolicy.Expect(
        self.messages.
        CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
            resource=function_path),
        response=initial_policy)
    set_request = \
      self.messages.CloudfunctionsProjectsLocationsFunctionsSetIamPolicyRequest(
          resource=function_path,
          setIamPolicyRequest=self.messages.SetIamPolicyRequest(
              policy=updated_policy))
    self.mock_client.projects_locations_functions.SetIamPolicy.Expect(
        set_request,
        response=updated_policy)

  def ExpectResourceManagerTestIamPolicyBinding(self, can_set, project=None):
    my_project = self.Project() if project is None else project
    needed_permissions = [
        'resourcemanager.projects.getIamPolicy',
        'resourcemanager.projects.setIamPolicy']

    messages = self.resource_manager_messages
    request = messages.CloudresourcemanagerProjectsTestIamPermissionsRequest(
        resource=my_project,
        testIamPermissionsRequest=messages.TestIamPermissionsRequest(
            permissions=needed_permissions))

    permissions = needed_permissions if can_set else []
    response = messages.TestIamPermissionsResponse(permissions=permissions)

    self.mock_resource_manager_client.projects.TestIamPermissions.Expect(
        request, response=response)
