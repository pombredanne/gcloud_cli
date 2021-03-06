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
"""Tests that exercise the 'gcloud kms keyrings create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.kms import base


class KeyringsCreateTestGA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.kr_name = self.project_name.KeyRing('global/my_kr')
    self.kms.projects_locations_keyRings.Create.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsCreateRequest(
            parent=self.kr_name.Parent().RelativeName(),
            keyRingId=self.kr_name.key_ring_id,
            keyRing=self.messages.KeyRing()),
        self.messages.KeyRing(name=self.kr_name.RelativeName()))

  def testCreate(self):
    self.Run('kms keyrings create --location={0} {1}'.format(
        self.kr_name.location_id, self.kr_name.key_ring_id))

  def testCreateFullName(self):
    self.Run('kms keyrings create {0}'.format(self.kr_name.RelativeName()))


class KeyringsCreateTestBeta(KeyringsCreateTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class KeyringsCreateTestAlpha(KeyringsCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
