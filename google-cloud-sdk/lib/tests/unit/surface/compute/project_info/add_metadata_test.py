# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the project-info add-metadata subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class ProjectInfoAddMetadataTest(test_base.BaseTest):

  def testWithNoKeys(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'At least one of \[--metadata\] or \[--metadata-from-file\] must be '
        'provided.'):
      self.Run("""
          compute project-info add-metadata
          """)
    self.CheckRequests()

  def testWithNoExistingMetadata(self):
    self.make_requests.side_effect = iter([
        [messages.Project(name='my-project')],
        [],
    ])

    self.Run("""
        compute project-info add-metadata
          --metadata x=y,a=b,hello=world
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'Get',
          messages.ComputeProjectsGetRequest(
              project='my-project'))],

        [(self.compute_v1.projects,
          'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(
                  items=[
                      messages.Metadata.ItemsValueListEntry(
                          key='a',
                          value='b'),
                      messages.Metadata.ItemsValueListEntry(
                          key='hello',
                          value='world'),
                      messages.Metadata.ItemsValueListEntry(
                          key='x',
                          value='y'),
                  ]),
              project='my-project'))],
    )

  def testWithExistingMetadata(self):
    self.make_requests.side_effect = iter([
        [
            messages.Project(
                name='my-project',
                commonInstanceMetadata=messages.Metadata(
                    fingerprint=b'my-fingerprint',
                    items=[
                        messages.Metadata.ItemsValueListEntry(
                            key='a', value='b'),
                        messages.Metadata.ItemsValueListEntry(
                            key='hello', value='world'),
                        messages.Metadata.ItemsValueListEntry(
                            key='x', value='y'),
                    ]))
        ],
        [],
    ])

    self.Run("""
        compute project-info add-metadata
          --metadata x=z,a=c,new-key=new-value
        """)

    self.CheckRequests(
        [(self.compute_v1.projects, 'Get',
          messages.ComputeProjectsGetRequest(project='my-project'))],
        [(self.compute_v1.projects, 'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(
                  fingerprint=b'my-fingerprint',
                  items=[
                      messages.Metadata.ItemsValueListEntry(key='a', value='c'),
                      messages.Metadata.ItemsValueListEntry(
                          key='hello', value='world'),
                      messages.Metadata.ItemsValueListEntry(
                          key='new-key', value='new-value'),
                      messages.Metadata.ItemsValueListEntry(key='x', value='z'),
                  ]),
              project='my-project'))],
    )

  def testWithMetadataFromFile(self):
    self.make_requests.side_effect = iter([
        [
            messages.Project(
                name='my-project',
                commonInstanceMetadata=messages.Metadata(
                    fingerprint=b'my-fingerprint',
                    items=[
                        messages.Metadata.ItemsValueListEntry(
                            key='a', value='b'),
                        messages.Metadata.ItemsValueListEntry(
                            key='hello', value='world'),
                        messages.Metadata.ItemsValueListEntry(
                            key='x', value='y'),
                    ]))
        ],
        [],
    ])

    metadata_file1 = self.Touch(
        self.temp_path, 'file-1', contents='hello')
    metadata_file2 = self.Touch(
        self.temp_path, 'file-2', contents='hello\nand\ngoodbye')

    self.Run("""
        compute project-info add-metadata --metadata new-key=new-value
          --metadata-from-file x={},a={}
        """.format(metadata_file1, metadata_file2))

    self.CheckRequests(
        [(self.compute_v1.projects, 'Get',
          messages.ComputeProjectsGetRequest(project='my-project'))],
        [(self.compute_v1.projects, 'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(
                  fingerprint=b'my-fingerprint',
                  items=[
                      messages.Metadata.ItemsValueListEntry(
                          key='a', value='hello\nand\ngoodbye'),
                      messages.Metadata.ItemsValueListEntry(
                          key='hello', value='world'),
                      messages.Metadata.ItemsValueListEntry(
                          key='new-key', value='new-value'),
                      messages.Metadata.ItemsValueListEntry(
                          key='x', value='hello'),
                  ]),
              project='my-project'))],
    )

  def testWithNoModification(self):
    self.make_requests.side_effect = iter([
        [
            messages.Project(
                name='my-project',
                commonInstanceMetadata=messages.Metadata(
                    fingerprint=b'my-fingerprint',
                    items=[
                        messages.Metadata.ItemsValueListEntry(
                            key='hello', value='world'),
                        messages.Metadata.ItemsValueListEntry(
                            key='a', value='b'),
                        messages.Metadata.ItemsValueListEntry(
                            key='x', value='y'),
                    ]))
        ],
        [],
    ])

    self.Run("""
        compute project-info add-metadata --metadata a=b,x=y
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'Get',
          messages.ComputeProjectsGetRequest(
              project='my-project'))],
    )

  def testAddMetadataSshKeys_InvalidPublicKey(self):
    self.make_requests.side_effect = iter([
        [messages.Project(name='my-project')],
        [],
    ])

    self.Run("""
        compute project-info add-metadata
          --metadata="ssh-keys=ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy6PKBE/xkf+I test,sshKeys=ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHA test"
        """)

    self.CheckRequests(
        [(self.compute_v1.projects, 'Get',
          messages.ComputeProjectsGetRequest(project='my-project'))],
        [(self.compute_v1.projects, 'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(items=[
                  messages.Metadata.ItemsValueListEntry(
                      key='ssh-keys',
                      value=
                      'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy6PKBE/xkf+I test'
                  ),
                  messages.Metadata.ItemsValueListEntry(
                      key='sshKeys',
                      value=
                      'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHA test'),
              ]),
              project='my-project'))],
    )

    self.AssertErrEquals(
        'WARNING: '
        'The following key(s) are missing the <username> at the front\n'
        'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy6PKBE/xkf+I test\n'
        'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHA test\n\n'
        'Format ssh keys following '
        'https://cloud.google.com/compute/docs/'
        'instances/adding-removing-ssh-keys\n')

  def testAddMetadataSshKeys_PrivateKey(self):
    self.make_requests.side_effect = iter([
        [messages.Project(name='my-project')],
        [],
    ])

    self.Run("""
        compute project-info add-metadata
          --metadata="ssh-keys=-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAsujygRP8ZH/iHVz0iXSqoProNu0m8aF7ZfogLiToZsvR5MaU\n-----END RSA PRIVATE KEY-----"
        """)

    self.CheckRequests(
        [(self.compute_v1.projects, 'Get',
          messages.ComputeProjectsGetRequest(project='my-project'))],
        [(self.compute_v1.projects, 'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(items=[
                  messages.Metadata.ItemsValueListEntry(
                      key='ssh-keys',
                      value='-----BEGIN RSA PRIVATE KEY-----\n'
                      'MIIEpAIBAAKCAQEAsujygRP8ZH/iHVz0'
                      'iXSqoProNu0m8aF7ZfogLiToZsvR5MaU\n'
                      '-----END RSA PRIVATE KEY-----'),
              ]),
              project='my-project'))],
    )

    self.AssertErrEquals(
        'WARNING: '
        'Private key(s) are detected. Note that only public keys '
        'should be added.\n')

  def testAddMetadataSshKeys_CorrectKey(self):
    self.make_requests.side_effect = iter([
        [messages.Project(name='my-project')],
        [],
    ])

    self.Run("""
        compute project-info add-metadata
          --metadata="ssh-keys=test:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCy6PKBE/xkf+I test,sshKeys=test:ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHA test"
        """)

    self.CheckRequests(
        [(self.compute_v1.projects, 'Get',
          messages.ComputeProjectsGetRequest(project='my-project'))],
        [(self.compute_v1.projects, 'SetCommonInstanceMetadata',
          messages.ComputeProjectsSetCommonInstanceMetadataRequest(
              metadata=messages.Metadata(items=[
                  messages.Metadata.ItemsValueListEntry(
                      key='ssh-keys',
                      value=
                      'test:ssh-rsa '
                      'AAAAB3NzaC1yc2EAAAADAQABAAABAQCy6PKBE/xkf+I test'
                  ),
                  messages.Metadata.ItemsValueListEntry(
                      key='sshKeys',
                      value=
                      'test:ecdsa-sha2-nistp256 '
                      'AAAAE2VjZHNhLXNoYTItbmlzdHA test'
                  ),
              ]),
              project='my-project'))],
    )

    self.AssertErrNotContains('WARNING')


if __name__ == '__main__':
  test_case.main()
