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
"""Tests that exercise CryptoKeyVersion-state-changing commands."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope.base import DeprecationException
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysVersionsStateTest(base.KmsMockTest):

  def SetUp(self):
    self.version_name = self.project_name.Descendant('global/my_kr/my_key/3')

  def testEnable(self):
    # pylint: disable=line-too-long
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys versions enable '
               '--location={0} --keyring={1} --key={2} {3}'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, self.version_name.version_id))

  def testDisable(self):
    # pylint: disable=line-too-long
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys versions disable '
               '--location={0} --keyring={1} --key={2} {3}'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, self.version_name.version_id))

  def testDestroy(self):
    # pylint: disable=line-too-long
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys versions destroy '
               '--location={0} --keyring={1} --key={2} {3}'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, self.version_name.version_id))

  def testRestore(self):
    # pylint: disable=line-too-long
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys versions restore '
               '--location={0} --keyring={1} --key={2} {3}'.format(
                   self.version_name.location_id, self.version_name.key_ring_id,
                   self.version_name.crypto_key_id, self.version_name.version_id))


if __name__ == '__main__':
  test_case.main()
