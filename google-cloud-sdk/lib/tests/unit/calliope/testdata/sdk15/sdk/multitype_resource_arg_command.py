# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""gcloud sdk tests command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


class BetaSubCommandWithResourceArgs(calliope_base.Command):
  """gcloud sdk tests command."""

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    device_or_registry_spec = multitype.MultitypeResourceSpec(
        'device-or-registry',
        resource_args.GetDeviceResourceSpec(),
        resource_args.GetRegistryResourceSpec())
    concept_parsers.ConceptParser(
        [presentation_specs.MultitypeResourcePresentationSpec(
            'device',
            device_or_registry_spec,
            'Help text for the resource.')]).AddToParser(parser)
