# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests that exercise client cert describing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite import util as protorpc_util

from tests.lib import test_case
from tests.lib.surface.sql import base


class _BaseClientCertsDescribeTest(object):
  # pylint:disable=g-tzinfo-datetime

  def testClientCertsDescribe(self):
    self.mocked_client.sslCerts.List.Expect(
        self.messages.SqlSslCertsListRequest(
            instance='integration-test',
            project=self.Project(),
        ),
        self.messages.SslCertsListResponse(
            items=[
                self.messages.SslCert(
                    cert='-----BEGIN CERTIFICATE-----\nMIIC/zCCAeegAwIBAgIES2',
                    certSerialNumber='1264712781',
                    commonName='cert',
                    createTime=datetime.datetime(
                        2014,
                        2,
                        4,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))).isoformat(),
                    expirationTime=datetime.datetime(
                        2024,
                        2,
                        2,
                        21,
                        10,
                        29,
                        402000,
                        tzinfo=protorpc_util.TimeZoneOffset(
                            datetime.timedelta(0))).isoformat(),
                    instance='integration-test',
                    kind='sql#sslCert',
                    sha1Fingerprint='77299aad4c8136911c1f0b07dd9802a9a72124e8',
                ),
            ],
            kind='sql#sslCertsList',
        ))

    self.Run('sql ssl client-certs describe cert --instance=integration-test')
    self.AssertOutputContains("""\
cert: |-
  -----BEGIN CERTIFICATE-----
  MIIC/zCCAeegAwIBAgIES2
certSerialNumber: '1264712781'
commonName: cert
createTime: '2014-02-04T21:10:29.402000+00:00'
expirationTime: '2024-02-02T21:10:29.402000+00:00'
instance: integration-test
kind: sql#sslCert
sha1Fingerprint: 77299aad4c8136911c1f0b07dd9802a9a72124e8
""", normalize_space=True)


class ClientCertsDescribeGATest(_BaseClientCertsDescribeTest,
                                base.SqlMockTestGA):
  pass


class ClientCertsDescribeBetaTest(_BaseClientCertsDescribeTest,
                                  base.SqlMockTestBeta):
  pass


class ClientCertsDescribeAlphaTest(_BaseClientCertsDescribeTest,
                                   base.SqlMockTestAlpha):
  pass


if __name__ == '__main__':
  test_case.main()
