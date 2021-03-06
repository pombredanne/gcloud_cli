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
"""Tests for the interconnect attachment partner provider patch subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.compute import test_base


class InterconnectAttachmentsProviderCreateGaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.SelectApi('v1')
    self.message_version = self.compute_v1

  def CheckInterconnectAttachmentRequest(self, **kwargs):
    interconnect_attachment_msg = {}
    interconnect_attachment_msg.update(kwargs)
    if 'validateOnly' in kwargs:
      validate_only = interconnect_attachment_msg.pop('validateOnly')
      self.CheckRequests(
          [(self.message_version.interconnectAttachments, 'Insert',
            self.messages.ComputeInterconnectAttachmentsInsertRequest(
                project='my-project',
                region='us-central1',
                validateOnly=validate_only,
                interconnectAttachment=self.messages.InterconnectAttachment(
                    **interconnect_attachment_msg)))],)
    else:
      self.CheckRequests(
          [(self.message_version.interconnectAttachments, 'Insert',
            self.messages.ComputeInterconnectAttachmentsInsertRequest(
                project='my-project',
                region='us-central1',
                interconnectAttachment=self.messages.InterconnectAttachment(
                    **interconnect_attachment_msg)))],)

  def testCreateInterconnectAttachment(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'PARTNER_PROVIDER'),
                bandwidth=messages.InterconnectAttachment
                .BandwidthValueValuesEnum('BPS_1G'),
                pairingKey='sample-pairing-key',
                partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
                    interconnectName='Test Interconnect 1',
                    partnerName='Example Partner Name',
                    portalUrl='https://example.com/portal-url-login'))
        ],
    ])

    self.Run(
        'compute interconnects attachments provider create my-attachment '
        '--region us-central1 --interconnect my-interconnect --description '
        '"this is my attachment" --bandwidth 1g --pairing-key '
        'sample-pairing-key --partner-interconnect-name "Test Interconnect 1" '
        '--partner-name "Example Partner Name" --partner-portal-url '
        'https://example.com/portal-url-login')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        type=messages.InterconnectAttachment.TypeValueValuesEnum(
            'PARTNER_PROVIDER'),
        bandwidth=messages.InterconnectAttachment.BandwidthValueValuesEnum(
            'BPS_1G'),
        pairingKey='sample-pairing-key',
        partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
            interconnectName='Test Interconnect 1',
            partnerName='Example Partner Name',
            portalUrl='https://example.com/portal-url-login'))

  def testCreateInterconnectAttachmentWithNewBandWidthEnum(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'PARTNER_PROVIDER'),
                bandwidth=messages.InterconnectAttachment
                .BandwidthValueValuesEnum('BPS_20G'),
                pairingKey='sample-pairing-key',
                partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
                    interconnectName='Test Interconnect 1',
                    partnerName='Example Partner Name',
                    portalUrl='https://example.com/portal-url-login'))
        ],
    ])

    self.Run(
        'compute interconnects attachments provider create my-attachment '
        '--region us-central1 --interconnect my-interconnect --description '
        '"this is my attachment" --bandwidth 20g --pairing-key '
        'sample-pairing-key --partner-interconnect-name "Test Interconnect 1" '
        '--partner-name "Example Partner Name" --partner-portal-url '
        'https://example.com/portal-url-login')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        type=messages.InterconnectAttachment.TypeValueValuesEnum(
            'PARTNER_PROVIDER'),
        bandwidth=messages.InterconnectAttachment.BandwidthValueValuesEnum(
            'BPS_20G'),
        pairingKey='sample-pairing-key',
        partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
            interconnectName='Test Interconnect 1',
            partnerName='Example Partner Name',
            portalUrl='https://example.com/portal-url-login'))

  def testCreateInterconnectAttachmentWithUri(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'PARTNER_PROVIDER'),
                bandwidth=messages.InterconnectAttachment
                .BandwidthValueValuesEnum('BPS_1G'),
                pairingKey='sample-pairing-key',
                partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
                    interconnectName='Test Interconnect 1',
                    partnerName='Example Partner Name,',
                    portalUrl='https://example.com/portal-url-login'))
        ],
    ])

    self.Run(
        'compute interconnects attachments provider create ' +
        self.compute_uri + '/projects/my-project/regions/us-central1/'
        'interconnectAttachments/my-attachment'
        ' --interconnect my-interconnect --description "this is my attachment"'
        ' --bandwidth 1g --pairing-key sample-pairing-key '
        '--partner-interconnect-name "Test Interconnect 1" --partner-name '
        '"Example Partner Name", --partner-portal-url '
        'https://example.com/portal-url-login')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        type=messages.InterconnectAttachment.TypeValueValuesEnum(
            'PARTNER_PROVIDER'),
        bandwidth=messages.InterconnectAttachment.BandwidthValueValuesEnum(
            'BPS_1G'),
        pairingKey='sample-pairing-key',
        partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
            interconnectName='Test Interconnect 1',
            partnerName='Example Partner Name,',
            portalUrl='https://example.com/portal-url-login'))

  def testSimpleInvocationWithRegionPrompt(self):
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)
    messages = self.messages

    self.WriteInput('2\n')
    self.make_requests.side_effect = iter(
        [[
            self.messages.Region(name='region-1'),
            self.messages.Region(name='region-2'),
            self.messages.Region(name='region-3'),
        ],
         [
             messages.InterconnectAttachment(
                 name='my-attachment',
                 description='',
                 region='region-2',
                 interconnect=self.compute_uri +
                 '/projects/my-project/global/interconnects/'
                 'my-interconnect',
                 router=self.compute_uri + '/projects/my-project/regions/'
                 'region-2/routers/my-router',
                 type=messages.InterconnectAttachment.TypeValueValuesEnum(
                     'PARTNER_PROVIDER'),
                 bandwidth=messages.InterconnectAttachment
                 .BandwidthValueValuesEnum('BPS_1G'),
                 pairingKey='sample-pairing-key',
                 partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
                     interconnectName='Test Interconnect 1',
                     partnerName='Example Partner Name,',
                     portalUrl='https://example.com/portal-url-login'))
         ]])

    self.Run(
        'compute interconnects attachments provider create my-attachment '
        '--interconnect my-interconnect --description "this is my attachment" '
        '--bandwidth 1g --pairing-key sample-pairing-key '
        '--partner-interconnect-name "Test Interconnect 1" --partner-name '
        '"Example Partner Name", --partner-portal-url '
        'https://example.com/portal-url-login')

    self.CheckRequests(
        [(self.compute.regions, 'List',
          messages.ComputeRegionsListRequest(
              project='my-project', maxResults=500))],
        [(self.message_version.interconnectAttachments, 'Insert',
          self.messages.ComputeInterconnectAttachmentsInsertRequest(
              project='my-project',
              region='region-2',
              interconnectAttachment=self.messages.InterconnectAttachment(
                  name='my-attachment',
                  description='this is my attachment',
                  interconnect=self.compute_uri +
                  '/projects/my-project/global/interconnects/my-interconnect',
                  type=messages.InterconnectAttachment.TypeValueValuesEnum(
                      'PARTNER_PROVIDER'),
                  bandwidth=messages.InterconnectAttachment
                  .BandwidthValueValuesEnum('BPS_1G'),
                  pairingKey='sample-pairing-key',
                  partnerMetadata=(
                      messages.InterconnectAttachmentPartnerMetadata(
                          interconnectName='Test Interconnect 1',
                          partnerName='Example Partner Name,',
                          portalUrl='https://example.com/portal-url-login')))))
        ],
    )
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains('"choices": ["region-1", "region-2", "region-3"]')
    self.AssertOutputEquals('')


class InterconnectAttachmentsProviderCreateBetaTest(
    InterconnectAttachmentsProviderCreateGaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    self.message_version = self.compute_beta


class InterconnectAttachmentsProviderCreateAlphaTest(
    InterconnectAttachmentsProviderCreateBetaTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.message_version = self.compute_alpha

  def testCreateInterconnectAttachmentWithNewBandWidthEnumAndValidateOnly(self):
    messages = self.messages
    self.make_requests.side_effect = iter([
        [
            messages.InterconnectAttachment(
                name='my-attachment',
                description='',
                region='us-central1',
                interconnect=self.compute_uri +
                '/projects/my-project/global/interconnects/'
                'my-interconnect',
                router=self.compute_uri + '/projects/my-project/regions/'
                'us-central1/routers/my-router',
                type=messages.InterconnectAttachment.TypeValueValuesEnum(
                    'PARTNER_PROVIDER'),
                bandwidth=messages.InterconnectAttachment
                .BandwidthValueValuesEnum('BPS_50G'),
                pairingKey='sample-pairing-key',
                partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
                    interconnectName='Test Interconnect 1',
                    partnerName='Example Partner Name',
                    portalUrl='https://example.com/portal-url-login'))
        ],
    ])

    self.Run(
        'compute interconnects attachments provider create my-attachment '
        '--region us-central1 --interconnect my-interconnect --description '
        '"this is my attachment" --bandwidth 50g --pairing-key '
        'sample-pairing-key --partner-interconnect-name "Test Interconnect 1" '
        '--partner-name "Example Partner Name" --partner-portal-url '
        'https://example.com/portal-url-login --dry-run')

    self.CheckInterconnectAttachmentRequest(
        name='my-attachment',
        description='this is my attachment',
        interconnect=self.compute_uri +
        '/projects/my-project/global/interconnects/my-interconnect',
        type=messages.InterconnectAttachment.TypeValueValuesEnum(
            'PARTNER_PROVIDER'),
        bandwidth=messages.InterconnectAttachment.BandwidthValueValuesEnum(
            'BPS_50G'),
        pairingKey='sample-pairing-key',
        partnerMetadata=messages.InterconnectAttachmentPartnerMetadata(
            interconnectName='Test Interconnect 1',
            partnerName='Example Partner Name',
            portalUrl='https://example.com/portal-url-login'),
        validateOnly=True)
