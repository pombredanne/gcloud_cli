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
"""tpus delete tests."""
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute.tpus import base


@parameterized.parameters([calliope_base.ReleaseTrack.ALPHA,
                           calliope_base.ReleaseTrack.BETA])
class DeleteTest(base.TpuUnitTestBase):

  def SetUp(self):
    self.zone = 'us-central1-c'
    self.track = calliope_base.ReleaseTrack.ALPHA
    properties.VALUES.compute.zone.Set(self.zone)
    self.StartPatch('time.sleep')

  def testDelete(self, track):
    self._SetTrack(track)
    delete_response = self.GetOperationResponse('delete')
    self.mock_client.projects_locations_nodes.Delete.Expect(
        self.messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        delete_response
    )
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/delete'.format(
                self.Project(),
                self.zone)),
        delete_response
    )
    self.WriteInput('Y\n')
    self.assertEqual(
        self.Run('compute tpus delete mytpu'),
        delete_response
    )

  def testDeleteWithZone(self, track):
    self._SetTrack(track)
    delete_response = self.GetOperationResponse('delete')
    self.mock_client.projects_locations_nodes.Delete.Expect(
        self.messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        delete_response
    )
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/delete'.format(
                self.Project(),
                self.zone)),
        delete_response
    )
    self.WriteInput('Y\n')
    self.assertEqual(
        self.Run('compute tpus delete mytpu --zone {}'.format(self.zone)),
        delete_response)

  def testDeleteCancelled(self, track):
    self._SetTrack(track)
    self.WriteInput('N\n')
    with self.AssertRaisesExceptionMatches(
        console_io.OperationCancelledError,
        'Deletion aborted by user.'):
      self.Run('compute tpus delete mytpu')

  def testDeleteLongRunningOperation(self, track):
    self._SetTrack(track)
    # Delete Request
    delete_response = self.GetOperationResponse('delete')
    self.mock_client.projects_locations_nodes.Delete.Expect(
        self.messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        delete_response
    )

    # Operation Polling Interval
    for _ in xrange(3):
      op_polling_response = self.GetOperationResponse('delete', is_done=False)
      self.mock_client.projects_locations_operations.Get.Expect(
          self.messages.TpuProjectsLocationsOperationsGetRequest(
              name='projects/{0}/locations/{1}/operations/delete'.format(
                  self.Project(),
                  self.zone)),
          op_polling_response
      )

    # Operation Complete
    op_done_response = self.GetOperationResponse('delete', is_done=True)
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/delete'.format(
                self.Project(),
                self.zone)),
        op_done_response
    )

    self.WriteInput('Y\n')
    self.assertEqual(
        self.Run('compute tpus delete mytpu'),
        op_done_response
    )

  def testDeleteLongRunningOperationError(self, track):
    self._SetTrack(track)
    # Delete Request
    delete_response = self.GetOperationResponse('delete')
    self.mock_client.projects_locations_nodes.Delete.Expect(
        self.messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        delete_response
    )

    # Operation Polling Interval
    for _ in xrange(3):
      op_polling_response = self.GetOperationResponse('delete', is_done=False)
      self.mock_client.projects_locations_operations.Get.Expect(
          self.messages.TpuProjectsLocationsOperationsGetRequest(
              name='projects/{0}/locations/{1}/operations/delete'.format(
                  self.Project(),
                  self.zone)),
          op_polling_response
      )

    # Operation Error on Complete
    op_done_response = self.GetOperationResponse(
        'delete',
        error_json={'code': 400, 'message': 'Delete Failed.'}
    )

    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/delete'.format(
                self.Project(),
                self.zone)),
        op_done_response
    )

    self.WriteInput('Y\n')
    with self.assertRaisesRegexp(waiter.OperationError, r'Delete Failed.'):
      self.Run('compute tpus delete mytpu')

  def testDeleteOutput(self, track):
    self._SetTrack(track)
    properties.VALUES.core.user_output_enabled.Set(True)
    delete_response = self.GetOperationResponse('delete')
    self.mock_client.projects_locations_nodes.Delete.Expect(
        self.messages.TpuProjectsLocationsNodesDeleteRequest(
            name='projects/{0}/locations/{1}/nodes/mytpu'.format(
                self.Project(),
                self.zone)),
        delete_response
    )
    self.mock_client.projects_locations_operations.Get.Expect(
        self.messages.TpuProjectsLocationsOperationsGetRequest(
            name='projects/{0}/locations/{1}/operations/delete'.format(
                self.Project(),
                self.zone)),
        delete_response
    )
    self.WriteInput('Y\n')
    self.Run('compute tpus delete mytpu')
    self.AssertErrContains("""\
Your TPU [mytpu] will be deleted.

Do you want to continue (Y/n)?
""", normalize_space=True)
    self.AssertErrContains('Waiting for [delete] to finish')
    self.AssertErrContains('Deleted [mytpu].', normalize_space=True)


if __name__ == '__main__':
  test_case.main()