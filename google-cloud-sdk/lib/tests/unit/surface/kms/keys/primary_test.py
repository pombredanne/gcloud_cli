# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests that exercise 'gcloud kms keys set-primary-version'."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysPrimaryTestGA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.version_name = self.project_name.Version('global/my_kr/my_key/3')
    self.key_name = self.project_name.CryptoKey('global/my_kr/my_key')

  def testSet(self):
    self.kms.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
            name=self.key_name.RelativeName(),
            updateCryptoKeyPrimaryVersionRequest=(
                self.messages.UpdateCryptoKeyPrimaryVersionRequest(
                    cryptoKeyVersionId=self.version_name.version_id))),
        self.messages.CryptoKey(name=self.version_name.Parent().RelativeName()))

    self.Run('kms keys set-primary-version '
             '--location={0} --keyring={1} {2} --version={3}'.format(
                 self.version_name.location_id, self.version_name.key_ring_id,
                 self.version_name.crypto_key_id, self.version_name.version_id))


class CryptokeysPrimaryTestBeta(CryptokeysPrimaryTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class CryptokeysPrimaryTestAlpha(CryptokeysPrimaryTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
