# -*- coding: utf-8 -*- #
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
"""Tests for the `gcloud container binauthz attestations create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.container.binauthz import base as binauthz_test_base


class BaseAttestationsTest(
    sdk_test_base.WithTempCWD,
    binauthz_test_base.BinauthzTestBase,
):

  def SetUp(self):
    self.project_ref = resources.REGISTRY.Parse(
        self.Project(),
        collection='cloudresourcemanager.projects',
    )
    self.artifact_url = self.GenerateArtifactUrl()
    self.pgp_key_fingerprint = 'AAAABBBB'
    self.signature = b'fake-signature'
    self.note_id = 'my-aa-note'
    self.note_project = 'other-' + self.Project()
    self.note_relative_name = 'projects/{}/notes/{}'.format(
        self.note_project, self.note_id)
    self.attestor_id = 'my-attestor'
    self.attestor_project = self.Project()
    self.attestor_relative_name = 'projects/{}/attestors/{}'.format(
        self.attestor_project, self.attestor_id)
    self.attestor = self.messages.Attestor(
        name=self.attestor_relative_name,
        updateTime=None,
        userOwnedDrydockNote=self.messages.UserOwnedDrydockNote(
            noteReference=self.note_relative_name,
            publicKeys=[],
        ))

    self.request_occurrence = self.CreateRequestOccurrence(
        project_ref=self.project_ref,
        artifact_url=self.artifact_url,
        note_ref=resources.REGISTRY.ParseRelativeName(
            relative_name=self.note_relative_name,
            collection='containeranalysis.projects.notes',
        ),
        pgp_key_fingerprint=self.pgp_key_fingerprint,
        signature=self.signature,
    )


class CreateTest(
    binauthz_test_base.WithMockBetaContaineranalysis,
    binauthz_test_base.WithMockBetaBinauthz,
    BaseAttestationsTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testCreateWithAttestor(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_relative_name,
            '--artifact-url',
            self.artifact_url,
            '--pgp-key-fingerprint',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )

  def testCreateWithAttestorUsingProjectFlag(self):
    response_occurrence = self.ExpectProjectsOccurrencesCreate(
        project_ref=self.project_ref,
        request_occurrence=self.request_occurrence,
    )

    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(  # pylint: disable=line-too-long
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)

    sig_path = self.Touch(directory=self.cwd_path, contents=self.signature)
    self.assertEqual(
        response_occurrence,
        self.RunBinauthz([
            'attestations',
            'create',
            '--attestor',
            self.attestor_id,
            '--attestor-project',
            self.attestor_project,
            '--artifact-url',
            self.artifact_url,
            '--pgp-key-fingerprint',
            self.pgp_key_fingerprint,
            '--signature-file',
            sig_path,
        ]),
    )


class ListTest(
    binauthz_test_base.WithMockBetaContaineranalysis,
    binauthz_test_base.WithMockBetaBinauthz,
    BaseAttestationsTest,
):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.response_occurrence = self.CreateResponseOccurrence(
        request_occurrence=self.request_occurrence,
        project_ref=self.project_ref,
    )

  def testAllAttestations(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='',
        occurrences_to_return=[self.response_occurrence],
    )

    self.RunBinauthz([
        'attestations',
        'list',
        '--attestor',
        self.attestor_relative_name,
    ])

    self.AssertOutputContains(self.pgp_key_fingerprint)
    self.AssertOutputContains(self.artifact_url)

  def testArtifactUrl(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='resourceUrl="{}"'.format(self.artifact_url),
        occurrences_to_return=[self.response_occurrence],
    )
    self.RunBinauthz([
        'attestations',
        'list',
        '--attestor',
        self.attestor_relative_name,
        '--artifact-url',
        self.artifact_url,
    ])

    self.AssertOutputContains(self.pgp_key_fingerprint)
    self.AssertOutputContains(self.artifact_url)

  def testArtifactUrl_AttestorWithProject(self):
    req = self.messages.BinaryauthorizationProjectsAttestorsGetRequest(
        name=self.attestor_relative_name,
    )
    self.mock_client.projects_attestors.Get.Expect(req, response=self.attestor)
    self.ExpectProjectsNotesOccurrencesList(
        note_relative_name=self.note_relative_name,
        expected_filter_content='resourceUrl="{}"'.format(self.artifact_url),
        occurrences_to_return=[self.response_occurrence],
    )

    self.RunBinauthz([
        'attestations',
        'list',
        '--attestor',
        self.attestor_id,
        '--attestor-project',
        self.attestor_project,
        '--artifact-url',
        self.artifact_url,
    ])

    self.AssertOutputContains(self.pgp_key_fingerprint)
    self.AssertOutputContains(self.artifact_url)


# TODO(b/131112840): CreateAlphaTest.


class ListAlphaTest(binauthz_test_base.WithMockAlphaBinauthz, ListTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
