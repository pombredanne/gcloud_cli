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
"""Tests that exercise operations listing and executing."""

from googlecloudsdk.api_lib.sql import exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.sql import base


class InstancesDescribeTest(base.SqlMockTestBeta):

  def testSimpleDescribe(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='testinstance',
            project=self.Project(),),
        self.messages.DatabaseInstance(
            currentDiskSize=52690837,
            databaseVersion=u'MYSQL_5_5',
            etag=u'"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"',
            name=u'testinstance',
            ipAddresses=[],
            ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:ab9d',
            kind=u'sql#instance',
            maxDiskSize=268435456000,
            project=self.Project(),
            region=u'us-central',
            serverCaCert=None,
            settings=self.messages.Settings(
                activationPolicy=u'ON_DEMAND',
                authorizedGaeApplications=[],
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=False,
                    enabled=True,
                    kind=u'sql#backupConfiguration',
                    startTime=u'11:54'),
                databaseFlags=[],
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=False,
                    requireSsl=None,),
                kind=u'sql#settings',
                locationPreference=None,
                pricingPlan=u'PER_USE',
                replicationType=u'SYNCHRONOUS',
                settingsVersion=1,
                tier=u'D0',),
            state=u'RUNNABLE',
            instanceType=u'CLOUD_SQL_INSTANCE',))

    self.Run('sql instances describe testinstance')
    self.AssertOutputContains(
        """\
currentDiskSize: '52690837'
databaseVersion: MYSQL_5_5
etag: '"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"'
instanceType: CLOUD_SQL_INSTANCE
ipv6Address: 2001:4860:4864:1:df7c:6a7a:d107:ab9d
kind: sql#instance
maxDiskSize: '268435456000'
name: testinstance
project: {0}
region: us-central
settings:
  activationPolicy: ON_DEMAND
  backupConfiguration:
    binaryLogEnabled: false
    enabled: true
    kind: sql#backupConfiguration
    startTime: '11:54'
  ipConfiguration:
    ipv4Enabled: false
  kind: sql#settings
  pricingPlan: PER_USE
  replicationType: SYNCHRONOUS
  settingsVersion: '1'
  tier: D0
state: RUNNABLE
""".format(self.Project()),
        normalize_space=True)

  def testDescribeLabels(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='testinstance',
            project=self.Project(),),
        self.messages.DatabaseInstance(
            currentDiskSize=52690837,
            databaseVersion=u'MYSQL_5_5',
            etag=u'"DExdZ69FktjWMJ-ohD1vLZW9pnk/MQ"',
            name=u'testinstance',
            ipAddresses=[],
            ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:ab9d',
            kind=u'sql#instance',
            maxDiskSize=268435456000,
            project=self.Project(),
            region=u'us-central',
            serverCaCert=None,
            settings=self.messages.Settings(
                activationPolicy=u'ON_DEMAND',
                authorizedGaeApplications=[],
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=False,
                    enabled=True,
                    kind=u'sql#backupConfiguration',
                    startTime=u'11:54'),
                databaseFlags=[],
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=False,
                    requireSsl=None,),
                kind=u'sql#settings',
                userLabels=self.messages.Settings.UserLabelsValue(
                    additionalProperties=[
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='bar',
                            value='value',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='baz',
                            value='qux',),
                        self.messages.Settings.UserLabelsValue.
                        AdditionalProperty(
                            key='foo',
                            value='bar',),
                    ],),
                locationPreference=None,
                pricingPlan=u'PER_USE',
                replicationType=u'SYNCHRONOUS',
                settingsVersion=1,
                tier=u'D0',),
            state=u'RUNNABLE',
            instanceType=u'CLOUD_SQL_INSTANCE',))

    self.Run('sql instances describe testinstance --format="default(labels)"')
    self.AssertOutputContains(
        """\
settings:
  userLabels:
    bar: value
    baz: qux
    foo: bar
""",
        normalize_space=True)

  def testInstanceNotFound(self):
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='nosuchinstance',
            project=self.Project(),),
        exception=http_error.MakeHttpError(
            403,
            'The client is not authorized to make this request.',
            url=('https://www.googleapis.com/sql/v1beta4/projects'
                 '/google.com%3Acloudsdktest/instances/noinstance?alt=json')))

    with self.assertRaises(exceptions.ResourceNotFoundError):
      self.Run('sql instances describe nosuchinstance')


if __name__ == '__main__':
  test_case.main()