# -*- coding: utf-8 -*- #
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite import util as protorpc_util

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseInstancesCloneTest(object):
  # pylint:disable=g-tzinfo-datetime

  messages = core_apis.GetMessagesModule('sqladmin', 'v1beta4')

  def testSimpleClone(self):
    self.mocked_client.instances.Clone.Expect(
        self.messages.SqlInstancesCloneRequest(
            instancesCloneRequest=self.messages.InstancesCloneRequest(
                cloneContext=self.messages.CloneContext(
                    binLogCoordinates=None,
                    destinationInstanceName='clone-instance-7a',
                    kind='sql#cloneContext',
                ),),
            instance='clone-instance-7',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55aa250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55aa250'.
            format(self.Project()),
            operationType='CLONE',
            status='RUNNING',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='d930826e-80a5-4477-8218-fb7fb55aa250',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55aa250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55aa250'.
            format(self.Project()),
            operationType='CLONE',
            status='RUNNING',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='d930826e-80a5-4477-8218-fb7fb55aa250',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55aa250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55aa250'.
            format(self.Project()),
            operationType='CLONE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='clone-instance-7a',
            project=self.Project(),
        ),
        self.messages.DatabaseInstance(
            currentDiskSize=287592789,
            databaseVersion='MYSQL_5_5',
            etag='"DExdZ69FktjWMJ-ohD1vLZW9pnk/Mw"',
            name='clone-instance-7a',
            ipAddresses=[],
            ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:ab9d',
            kind='sql#instance',
            maxDiskSize=268435456000,
            project=self.Project(),
            region='us-central',
            serverCaCert=self.messages.SslCert(
                cert='-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAgIBADANBg',
                certSerialNumber='0',
                commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL Server C',
                createTime=datetime.datetime(
                    2014,
                    8,
                    13,
                    21,
                    47,
                    29,
                    512000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                expirationTime=datetime.datetime(
                    2024,
                    8,
                    10,
                    21,
                    47,
                    29,
                    512000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                instance='clone-instance-7a',
                kind='sql#sslCert',
                sha1Fingerprint='2dbfcefd3c962a284035ffb06dccdd2055d32b46',
            ),
            settings=self.messages.Settings(
                activationPolicy='ON_DEMAND',
                authorizedGaeApplications=[],
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=True,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='23:00'),
                databaseFlags=[],
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=False,
                    requireSsl=None,
                ),
                kind='sql#settings',
                locationPreference=None,
                pricingPlan='PER_USE',
                replicationType='SYNCHRONOUS',
                settingsVersion=3,
                tier='D1',
            ),
            state='RUNNABLE',
            instanceType='CLOUD_SQL_INSTANCE',
        ))

    self.Run('sql instances clone clone-instance-7 clone-instance-7a')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME               DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS  STATUS
clone-instance-7a  MYSQL_5_5         us-central  D1    -               -                RUNNABLE
""",
        normalize_space=True)

  def testSimpleAsyncClone(self):
    self.mocked_client.instances.Clone.Expect(
        self.messages.SqlInstancesCloneRequest(
            instancesCloneRequest=self.messages.InstancesCloneRequest(
                cloneContext=self.messages.CloneContext(
                    binLogCoordinates=None,
                    destinationInstanceName='clone-instance-7a',
                    kind='sql#cloneContext',
                ),),
            instance='clone-instance-7',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55cc250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55cc250'.
            format(self.Project()),
            operationType='CLONE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='d930826e-80a5-4477-8218-fb7fb55cc250',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55cc250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55cc250'.
            format(self.Project()),
            operationType='CLONE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.Run('sql instances clone clone-instance-7 clone-instance-7a --async')
    self.AssertOutputEquals("""\
endTime: '2014-08-07T15:00:01.142000+00:00'
insertTime: '2014-08-07T15:00:01.081000+00:00'
kind: sql#operation
name: d930826e-80a5-4477-8218-fb7fb55cc250
operationType: CLONE
selfLink: https://www.googleapis.com/sql/v1beta4/projects/fake-project/operations/d930826e-80a5-4477-8218-fb7fb55cc250
startTime: '2014-08-07T15:00:01.142000+00:00'
status: DONE
targetId: clone-instance-7a
targetLink: https://www.googleapis.com/sql/v1beta4/projects/fake-project/instances/clone-instance-7a
targetProject: fake-project
user: 170350250316@developer.gserviceaccount.com
""")

  def testCloneBinLog(self):
    self.mocked_client.instances.Clone.Expect(
        self.messages.SqlInstancesCloneRequest(
            instancesCloneRequest=self.messages.InstancesCloneRequest(
                cloneContext=self.messages.CloneContext(
                    binLogCoordinates=self.messages.BinLogCoordinates(
                        binLogFileName='bin.log', binLogPosition=1111),
                    destinationInstanceName='clone-instance-7a',
                    kind='sql#cloneContext',
                ),),
            instance='clone-instance-7',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55aa250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55aa250'.
            format(self.Project()),
            operationType='CLONE',
            status='RUNNING',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='d930826e-80a5-4477-8218-fb7fb55aa250',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55aa250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55aa250'.
            format(self.Project()),
            operationType='CLONE',
            status='RUNNING',
            user='170350250316@developer.gserviceaccount.com',
        ))

    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='d930826e-80a5-4477-8218-fb7fb55aa250',
            project=self.Project(),
        ),
        self.messages.Operation(
            # pylint:disable=line-too-long
            insertTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                81000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                8,
                7,
                15,
                0,
                1,
                142000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId='clone-instance-7a',
            targetLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/clone-instance-7a'.
            format(self.Project()),
            targetProject=self.Project(),
            kind='sql#operation',
            name='d930826e-80a5-4477-8218-fb7fb55aa250',
            selfLink=
            'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/d930826e-80a5-4477-8218-fb7fb55aa250'.
            format(self.Project()),
            operationType='CLONE',
            status='DONE',
            user='170350250316@developer.gserviceaccount.com',
        ))
    self.mocked_client.instances.Get.Expect(
        self.messages.SqlInstancesGetRequest(
            instance='clone-instance-7a',
            project=self.Project(),
        ),
        self.messages.DatabaseInstance(
            currentDiskSize=287592789,
            databaseVersion='MYSQL_5_5',
            etag='"DExdZ69FktjWMJ-ohD1vLZW9pnk/Mw"',
            name='clone-instance-7a',
            ipAddresses=[],
            ipv6Address='2001:4860:4864:1:df7c:6a7a:d107:ab9d',
            kind='sql#instance',
            maxDiskSize=268435456000,
            project=self.Project(),
            region='us-central',
            serverCaCert=self.messages.SslCert(
                cert='-----BEGIN CERTIFICATE-----\nMIIDITCCAgmgAwIBAgIBADANBg',
                certSerialNumber='0',
                commonName='C=US,O=Google\\, Inc,CN=Google Cloud SQL Server C',
                createTime=datetime.datetime(
                    2014,
                    8,
                    13,
                    21,
                    47,
                    29,
                    512000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                expirationTime=datetime.datetime(
                    2024,
                    8,
                    10,
                    21,
                    47,
                    29,
                    512000,
                    tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
                instance='clone-instance-7a',
                kind='sql#sslCert',
                sha1Fingerprint='2dbfcefd3c962a284035ffb06dccdd2055d32b46',
            ),
            settings=self.messages.Settings(
                activationPolicy='ON_DEMAND',
                authorizedGaeApplications=[],
                backupConfiguration=self.messages.BackupConfiguration(
                    binaryLogEnabled=True,
                    enabled=True,
                    kind='sql#backupConfiguration',
                    startTime='23:00'),
                databaseFlags=[],
                ipConfiguration=self.messages.IpConfiguration(
                    authorizedNetworks=[],
                    ipv4Enabled=False,
                    requireSsl=None,
                ),
                kind='sql#settings',
                locationPreference=None,
                pricingPlan='PER_USE',
                replicationType='SYNCHRONOUS',
                settingsVersion=3,
                tier='D1',
            ),
            state='RUNNABLE',
            instanceType='CLOUD_SQL_INSTANCE',
        ))

    self.Run('sql instances clone --bin-log-file-name bin.log '
             '--bin-log-position 1111 clone-instance-7 clone-instance-7a')
    # pylint:disable=line-too-long
    self.AssertOutputContains(
        """\
NAME               DATABASE_VERSION  LOCATION    TIER  PRIMARY_ADDRESS PRIVATE_ADDRESS STATUS
clone-instance-7a  MYSQL_5_5         us-central  D1    -               -               RUNNABLE
""",
        normalize_space=True)

  def testCloneBinLogInvalidArgs(self):
    with self.assertRaisesRegex(
        exceptions.ArgumentError,
        'Both --bin-log-file-name and --bin-log-position must be specified'):
      self.Run("""
               sql instances clone
               --bin-log-file-name bin.log
               clone-instance-7 clone-instance-7a
               """)
    with self.assertRaisesRegex(
        exceptions.ArgumentError,
        'Both --bin-log-file-name and --bin-log-position must be specified'):
      self.Run("""
               sql instances clone
               --bin-log-position 1111
               clone-instance-7 clone-instance-7a
               """)


class InstancesCloneGATest(_BaseInstancesCloneTest, base.SqlMockTestGA):
  pass


class InstancesCloneBetaTest(_BaseInstancesCloneTest, base.SqlMockTestBeta):
  pass


class InstancesCloneAlphaTest(_BaseInstancesCloneTest, base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
