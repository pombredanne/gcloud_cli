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
"""Tests for Spanner instances set-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class SetIamPolicyTestGA(base.SpannerTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.database_ref = resources.REGISTRY.Parse(
        'dbId',
        params={
            'projectsId': self.Project(),
            'instancesId': 'insId',
        },
        collection='spanner.projects.instances.databases')
    self.policy = self.msgs.Policy(
        bindings=[
            self.msgs.Binding(
                role='roles/spanner.databaseAdmin', members=['domain:foo.com']),
            self.msgs.Binding(
                role='roles/spanner.viewer', members=['user:admin@foo.com'])
        ],
        etag=b'someUniqueEtag',
        version=1)
    json = encoding.MessageToJson(self.policy)
    self.temp_file = self.Touch(self.temp_path, contents=json)

  def testSetIamPolicy(self):
    set_request = self.msgs.SetIamPolicyRequest(policy=self.policy)
    set_request.policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
    self.client.projects_instances_databases.SetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSetIamPolicyRequest(
            resource=self.database_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.policy)
    set_policy_request = self.Run(
        'spanner databases set-iam-policy dbId {0} --instance=insId'.format(
            self.temp_file))
    self.assertEqual(set_policy_request, self.policy)
    self.AssertErrContains('Updated IAM policy for database [dbId].')

  def testSetIamPolicyWithDefaultInstance(self):
    set_request = self.msgs.SetIamPolicyRequest(policy=self.policy)
    set_request.policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION
    self.client.projects_instances_databases.SetIamPolicy.Expect(
        request=self.msgs.SpannerProjectsInstancesDatabasesSetIamPolicyRequest(
            resource=self.database_ref.RelativeName(),
            setIamPolicyRequest=set_request),
        response=self.policy)
    self.Run('config set spanner/instance insId')
    set_policy_request = self.Run(
        'spanner databases set-iam-policy dbId {0}'.format(self.temp_file))
    self.assertEqual(set_policy_request, self.policy)
    self.AssertErrContains('Updated IAM policy for database [dbId].')

  def testBadJsonOrYamlSetIamPolicyProject(self):
    temp_file = self.Touch(self.temp_path, 'bad', contents='bad')

    with self.AssertRaisesExceptionRegexp(
        exceptions.Error, 'not a properly formatted YAML or JSON policy file'):
      self.Run(
          'spanner databases set-iam-policy dbId {0} --instance=insId'.format(
              temp_file))

  def testBadJsonSetIamPolicyProject(self):
    temp_file = os.path.join(self.temp_path, 'doesnotexist')

    with self.AssertRaisesExceptionRegexp(
        exceptions.Error,
        r'Failed to load YAML from \[{}\]'.format(re.escape(temp_file))):
      self.Run(
          'spanner databases set-iam-policy dbId {0} --instance=insId'.format(
              temp_file))


class SetIamPolicyTestBeta(SetIamPolicyTestGA):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class SetIamPolicyTestAlpha(SetIamPolicyTestBeta):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
