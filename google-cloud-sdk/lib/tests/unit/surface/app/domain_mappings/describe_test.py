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
"""Tests for gcloud app domain-mappings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib.surface.app import domain_mappings_base


class DomainMappingsCommandTest(domain_mappings_base.DomainMappingsBase):

  def testDescribeDomainMapping(self):
    self.ExpectGetDomainMapping('*.example.com', '1234', 'MANUAL')
    result = self.Run('app domain-mappings describe *.example.com')
    self.assertEqual('*.example.com', result.id)
    self.assertEqual('1234', result.sslSettings.certificateId)
    self.assertEqual(
        self._ManagementTypeFromString('MANUAL'),
        result.sslSettings.sslManagementType)


class DomainMappingsCommandBetaTest(domain_mappings_base.DomainMappingsBase):
  APPENGINE_API_VERSION = 'v1beta'

  def testDescribeDomainMapping(self):
    self.ExpectGetDomainMapping('*.example.com', '1234', 'MANUAL')
    result = self.Run('beta app domain-mappings describe *.example.com')
    self.assertEqual('*.example.com', result.id)
    self.assertEqual('1234', result.sslSettings.certificateId)
    self.assertEqual(
        self._ManagementTypeFromString('MANUAL'),
        result.sslSettings.sslManagementType)
