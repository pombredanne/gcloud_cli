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
"""Tests for `gcloud iot devices credentials delete`."""
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CredentialsDeleteTest(base.CloudIotBase):

  def testDelete(self, track):
    self.track = track
    self.WriteInput('y')
    device_credentials = [
        self.messages.DeviceCredential(expirationTime='2016-01-01T00:00Z'),
        self.messages.DeviceCredential(expirationTime='2017-01-01T00:00Z'),
    ]
    self._ExpectGet(device_credentials)
    self._ExpectPatch(device_credentials[1:])

    results = self.Run(
        'iot devices credentials delete 0'
        '    --format disable '
        '    --device my-device '
        '    --registry my-registry '
        '    --region us-central1')

    expected_device = self.messages.Device(id='my-device',
                                           credentials=device_credentials[1:])
    self.assertEqual(results, expected_device)
    self.AssertErrContains('This will delete the following credential:')
    self.AssertErrContains('2016')
    self.AssertLogContains('Deleted credentials for device [my-device].')

  def testDelete_BadIndex(self, track):
    self.track = track
    device_credentials = [
        self.messages.DeviceCredential(expirationTime='2016-01-01T00:00Z'),
        self.messages.DeviceCredential(expirationTime='2017-01-01T00:00Z'),
    ]
    self._ExpectGet(device_credentials)

    with self.AssertRaisesExceptionMatches(
        util.BadCredentialIndexError,
        'Invalid credential index [2]; device [my-device] has 2 credentials'):
      self.Run(
          'iot devices credentials delete 2'
          '    --format disable '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1')

  def testDelete_Cancel(self, track):
    self.track = track
    self.WriteInput('n')
    credential = self.messages.DeviceCredential()
    self._ExpectGet([credential])

    with self.assertRaises(console_io.OperationCancelledError):
      self.Run(
          'iot devices credentials delete 0'
          '    --format disable '
          '    --device my-device '
          '    --registry my-registry '
          '    --region us-central1')
    self.AssertErrContains('This will delete the following credential:')

  def testDelete_RelativeName(self, track):
    self.track = track
    self.WriteInput('y')
    device_credentials = [
        self.messages.DeviceCredential(expirationTime='2016-01-01T00:00Z'),
        self.messages.DeviceCredential(expirationTime='2017-01-01T00:00Z'),
    ]
    self._ExpectGet(device_credentials)
    self._ExpectPatch(device_credentials[1:])

    device_name = ('projects/{}/'
                   'locations/us-central1/'
                   'registries/my-registry/'
                   'devices/my-device').format(self.Project())
    results = self.Run(
        'iot devices credentials delete 0'
        '    --format disable '
        '    --device {}'.format(device_name))

    expected_device = self.messages.Device(id='my-device',
                                           credentials=device_credentials[1:])
    self.assertEqual(results, expected_device)
    self.AssertErrContains('This will delete the following credential:')
    self.AssertErrContains('2016')


if __name__ == '__main__':
  test_case.main()