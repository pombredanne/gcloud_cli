# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Test base for the backend services update subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_services import test_resources


class UpdateTestBase(test_base.BaseTest):
  """Test base for the backend services update subcommand."""

  def SetUp(self):
    self.SelectApi(self.api_version)

    self._backend_services = test_resources.BACKEND_SERVICES_V1

    self._http_backend_services_with_legacy_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1)
    self._https_backend_services_with_legacy_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_LEGACY_HEALTH_CHECK_V1)

    self._http_backend_services_with_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1)
    self._https_backend_services_with_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_V1)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)


class BetaUpdateTestBase(test_base.BaseTest):
  """Test base for the beta backend services update subcommand."""

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

    self._backend_services = test_resources.BACKEND_SERVICES_BETA
    self._http_backend_services_with_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_BETA)
    self._https_backend_services_with_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_BETA)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)


class AlphaUpdateTestBase(test_base.BaseTest):
  """Test base for the alpha backend services update subcommand."""

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

    self._backend_services = test_resources.BACKEND_SERVICES_ALPHA
    self._http_backend_services_with_health_check = (
        test_resources.HTTP_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA)
    self._https_backend_services_with_health_check = (
        test_resources.HTTPS_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA)
    self._tcp_backend_services_with_health_check = (
        test_resources.TCP_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA)
    self._ssl_backend_services_with_health_check = (
        test_resources.SSL_BACKEND_SERVICES_WITH_HEALTH_CHECK_ALPHA)

  def RunUpdate(self, command, use_global=True):
    suffix = ' --global' if use_global else ''
    self.Run('compute backend-services update ' + command + suffix)

