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

from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.core.util import retry
from tests.lib import test_case
from tests.lib.surface.sql import base


class OperationsWaitTest(base.SqlMockTestBeta):
  # pylint:disable=g-tzinfo-datetime

  def testOperationsWait(self):
    # pylint: disable=line-too-long
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='1cb8a924-898d-41ec-b695-39a6dc018d16',
            project=self.Project(),),
        self.messages.Operation(
            insertTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                12,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                13,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                16,
                342000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId=u'integration-test',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'1cb8a924-898d-41ec-b695-39a6dc018d16',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/1cb8a924-898d-41ec-b695-39a6dc018d16'.
            format(self.Project()),
            operationType=u'CREATE_USER',
            status=u'DONE',
            user=u'170350250316@developer.gserviceaccount.com',))
    # pylint: disable=line-too-long
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='1cb8a924-898d-41ec-b695-39a6dc018d16',
            project=self.Project(),),
        self.messages.Operation(
            insertTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                12,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                13,
                672000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                16,
                342000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId=u'integration-test',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'1cb8a924-898d-41ec-b695-39a6dc018d16',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/1cb8a924-898d-41ec-b695-39a6dc018d16'.
            format(self.Project()),
            operationType=u'CREATE_USER',
            status=u'DONE',
            user=u'170350250316@developer.gserviceaccount.com',))

    # pylint: disable=line-too-long
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            project=self.Project(),),
        self.messages.Operation(
            insertTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                1,
                104000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                2,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                3,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId=u'integration-test',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/27e060bf-4e4b-4fbb-b451-a9ee6c8a433a'.
            format(self.Project()),
            operationType=u'RESTART',
            status=u'DONE',
            user=u'1@developer.gserviceaccount.com',))
    # pylint: disable=line-too-long
    self.mocked_client.operations.Get.Expect(
        self.messages.SqlOperationsGetRequest(
            operation='27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            project=self.Project(),),
        self.messages.Operation(
            insertTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                1,
                104000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            startTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                2,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            endTime=datetime.datetime(
                2014,
                7,
                10,
                17,
                23,
                3,
                165000,
                tzinfo=protorpc_util.TimeZoneOffset(datetime.timedelta(0))),
            error=None,
            exportContext=None,
            importContext=None,
            targetId=u'integration-test',
            targetLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/instances/integration-test'.
            format(self.Project()),
            targetProject=self.Project(),
            kind=u'sql#operation',
            name=u'27e060bf-4e4b-4fbb-b451-a9ee6c8a433a',
            selfLink=
            u'https://www.googleapis.com/sql/v1beta4/projects/{0}/operations/27e060bf-4e4b-4fbb-b451-a9ee6c8a433a'.
            format(self.Project()),
            operationType=u'RESTART',
            status=u'DONE',
            user=u'1@developer.gserviceaccount.com',))

    self.Run('sql operations wait 1cb8a924-898d-41ec-b695-39a6dc018d16 '
             '27e060bf-4e4b-4fbb-b451-a9ee6c8a433a')
    # pylint: disable=line-too-long
    self.AssertOutputContains("""\
NAME                                  TYPE         START                          END                               ERROR  STATUS
1cb8a924-898d-41ec-b695-39a6dc018d16  CREATE_USER  2014-07-10T17:23:13.672+00:00  2014-07-10T17:23:16.342+00:00  -      DONE
27e060bf-4e4b-4fbb-b451-a9ee6c8a433a  RESTART      2014-07-10T17:23:02.165+00:00  2014-07-10T17:23:03.165+00:00  -      DONE
""", normalize_space=True)

  def testOperationsWaitExceptionMessage(self):
    self.StartPatch('googlecloudsdk.core.util.retry.Retryer.RetryOnResult',
                    side_effect=retry.WaitException('forced timeout',
                                                    False, None))
    with self.assertRaisesRegexp(
        exceptions.OperationError,
        'Operation .* is taking longer than expected. You can continue waiting '
        'for the operation by running `gcloud beta sql operations wait .*`'):
      self.Run('sql operations wait 1cb8a924-898d-41ec-b695-39a6dc018d16')

if __name__ == '__main__':
  test_case.main()