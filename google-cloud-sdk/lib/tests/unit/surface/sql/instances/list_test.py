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
import datetime

from apitools.base.protorpclite import util as protorpc_util
from googlecloudsdk.api_lib.sql import instances
from tests.lib import test_case
from tests.lib.surface.sql import base
from tests.lib.surface.sql import data


class ListsTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testInstancesListNoLists(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            maxResults=100, project=self.Project()),
        self.messages.InstancesListResponse(
            kind=u'sql#instancesList',
            items=[],))
    self.Run('sql instances list')
    self.AssertErrContains("""Listed 0 items.""", normalize_space=True)

  def testInstancesList(self):
    instances_list = data.GetDatabaseInstancesListOfTwo(
    ) + data.GetDatabaseInstancesListOfOne()
    mocked_database_instances = self.StartObjectPatch(instances._BaseInstances,
                                                      'GetDatabaseInstances')
    mocked_database_instances.return_value = instances_list

    self.Run('sql instances list')

    mocked_database_instances.assert_called_once()

    self.AssertOutputContains(
        """\
NAME                 DATABASE_VERSION LOCATION      TIER ADDRESS STATUS
testinstance         MYSQL_5_5        us-central    D0   -       RUNNABLE
backupless-instance1 MYSQL_5_5        us-central1-a D1   -       RUNNABLE
backupless-instance2 MYSQL_5_5        us-central    D1   -       RUNNABLE
""",
        normalize_space=True)

  def testInstancesListWithLimit(self):
    instances_list = data.GetDatabaseInstancesListOfTwo(
    ) + data.GetDatabaseInstancesListOfOne()
    mocked_database_instances = self.StartObjectPatch(instances._BaseInstances,
                                                      'GetDatabaseInstances')
    mocked_database_instances.return_value = instances_list

    self.Run('sql instances list --limit=2')

    mocked_database_instances.assert_called_once()
    mocked_database_instances.assert_called_with(limit=2, batch_size=None)

    self.AssertOutputContains(
        """\
NAME                 DATABASE_VERSION LOCATION      TIER ADDRESS STATUS
testinstance         MYSQL_5_5        us-central    D0   -       RUNNABLE
backupless-instance1 MYSQL_5_5        us-central1-a D1   -       RUNNABLE
""",
        normalize_space=True)
    self.AssertOutputNotContains('backupless-instance2')

  def testInstancesListWithPageSize(self):
    instances_list = data.GetDatabaseInstancesListOfTwo(
    ) + data.GetDatabaseInstancesListOfOne()
    mocked_database_instances = self.StartObjectPatch(instances._BaseInstances,
                                                      'GetDatabaseInstances')
    mocked_database_instances.return_value = instances_list

    self.Run('sql instances list --page-size=1')

    mocked_database_instances.assert_called_once()
    mocked_database_instances.assert_called_with(limit=None, batch_size=1)

    self.AssertOutputContains(
        """\
NAME                 DATABASE_VERSION LOCATION   TIER ADDRESS STATUS
testinstance         MYSQL_5_5        us-central D0   -       RUNNABLE

NAME                 DATABASE_VERSION LOCATION      TIER ADDRESS STATUS
backupless-instance1 MYSQL_5_5        us-central1-a D1   -       RUNNABLE

NAME                 DATABASE_VERSION LOCATION   TIER ADDRESS STATUS
backupless-instance2 MYSQL_5_5        us-central D1   -       RUNNABLE
""",
        normalize_space=True)

  def testInstancesListWithLabels(self):
    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            maxResults=100,
            project=self.Project(),),
        self.messages.InstancesListResponse(
            # pylint:disable=line-too-long
            items=[
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
                    instanceType=u'CLOUD_SQL_INSTANCE',),
                self.messages.DatabaseInstance(
                    currentDiskSize=287571860,
                    databaseVersion=u'MYSQL_5_5',
                    etag=u'"yGhHGJDUk5hWK-gppo_8C-KD7iU/QWyUhySo75iWP2WEOzCGc"',
                    name=u'backupless-instance1',
                    ipAddresses=[],
                    ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:aaaa',
                    kind=u'sql#instance',
                    maxDiskSize=268435456000,
                    project=self.Project(),
                    region=u'us-central',
                    serverCaCert=self.messages.SslCert(
                        cert=u'-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAg',
                        certSerialNumber=u'0',
                        commonName=u'C=US,O=Google\\, Inc,CN=Google Cloud SQL ',
                        createTime=datetime.datetime(
                            2014,
                            8,
                            12,
                            19,
                            43,
                            9,
                            329000,
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))),
                        expirationTime=datetime.datetime(
                            2024,
                            8,
                            9,
                            19,
                            43,
                            9,
                            329000,
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))),
                        instance=u'backupless-instance1',
                        kind=u'sql#sslCert',
                        sha1Fingerprint=u'70bd50bd905e822ce428b8a1345ffc68d5aa',
                    ),
                    settings=self.messages.Settings(
                        activationPolicy=u'ON_DEMAND',
                        authorizedGaeApplications=[],
                        backupConfiguration=self.messages.BackupConfiguration(
                            binaryLogEnabled=True,
                            enabled=True,
                            kind=u'sql#backupConfiguration',
                            startTime=u'12:00'),
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
                                    value='another',),
                                self.messages.Settings.UserLabelsValue.
                                AdditionalProperty(
                                    key='foo',
                                    value='bar',),
                            ],),
                        locationPreference=None,
                        pricingPlan=u'PER_USE',
                        replicationType=u'SYNCHRONOUS',
                        settingsVersion=1,
                        tier=u'D1',),
                    state=u'RUNNABLE',
                    instanceType=u'CLOUD_SQL_INSTANCE',),
            ],
            kind=u'sql#instancesList',
            nextPageToken='100',))

    self.mocked_client.instances.List.Expect(
        self.messages.SqlInstancesListRequest(
            pageToken=u'100',
            project=self.Project(),
            maxResults=100,),
        self.messages.InstancesListResponse(
            # pylint:disable=line-too-long
            items=[
                self.messages.DatabaseInstance(
                    currentDiskSize=287571860,
                    databaseVersion=u'MYSQL_5_5',
                    etag=u'"yGhHGJDUk5hWK-gppo_8C-KD7iU/nbMj8WWUtdJPpSjOHUxEh"',
                    name=u'backupless-instance2',
                    ipAddresses=[],
                    ipv6Address=u'2001:4860:4864:1:df7c:6a7a:d107:aaaa',
                    kind=u'sql#instance',
                    maxDiskSize=268435456000,
                    project=self.Project(),
                    region=u'us-central',
                    serverCaCert=self.messages.SslCert(
                        cert=u'-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAg',
                        certSerialNumber=u'0',
                        commonName=u'C=US,O=Google\\, Inc,CN=Google Cloud SQL ',
                        createTime=datetime.datetime(
                            2014,
                            8,
                            11,
                            21,
                            47,
                            10,
                            788000,
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))),
                        expirationTime=datetime.datetime(
                            2024,
                            8,
                            8,
                            21,
                            47,
                            10,
                            788000,
                            tzinfo=protorpc_util.TimeZoneOffset(
                                datetime.timedelta(0))),
                        instance=u'backupless-instance',
                        kind=u'sql#sslCert',
                        sha1Fingerprint=u'a691db45f7dee0827650fd2eb277d2ca81b9',
                    ),
                    settings=self.messages.Settings(
                        activationPolicy=u'ON_DEMAND',
                        authorizedGaeApplications=[],
                        backupConfiguration=self.messages.BackupConfiguration(
                            binaryLogEnabled=False,
                            enabled=False,
                            kind=u'sql#backupConfiguration',
                            startTime=u'00:00'),
                        databaseFlags=[],
                        databaseReplicationEnabled=None,
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
                                    value='athird',),
                                self.messages.Settings.UserLabelsValue.
                                AdditionalProperty(
                                    key='baz',
                                    value='qux',),
                            ],),
                        locationPreference=self.messages.LocationPreference(
                            followGaeApplication=None,
                            kind=u'sql#locationPreference',
                            zone=None,),
                        pricingPlan=u'PER_USE',
                        replicationType=u'SYNCHRONOUS',
                        settingsVersion=1,
                        tier=u'D1',),
                    state=u'RUNNABLE',
                    instanceType=u'CLOUD_SQL_INSTANCE',),
            ],
            kind=u'sql#instancesList',
            nextPageToken=None,))

    self.Run('sql instances list --format="table(name,labels.bar)"')
    self.AssertOutputContains(
        """\
NAME                  BAR
testinstance          value
backupless-instance1  another
backupless-instance2  athird
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()