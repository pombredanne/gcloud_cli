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
"""Command to update a trigger."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import triggers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To update the trigger 'my-trigger' by setting its destination Cloud Run service to 'my-service', run:

          $ {command} my-trigger --destination-run-service=my-service
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  """Update an Eventarc trigger."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddTriggerResourceArg(parser, 'The trigger to update.', required=True)
    flags.AddMatchingCriteriaArg(parser)
    flags.AddDestinationRunServiceArg(parser)
    flags.AddDestinationRunRegionArg(parser)
    base.ASYNC_FLAG.AddToParser(parser)

    service_account_group = parser.add_mutually_exclusive_group()
    flags.AddServiceAccountResourceArg(service_account_group)
    flags.AddClearServiceAccountArg(service_account_group)

    destination_run_path_group = parser.add_mutually_exclusive_group()
    flags.AddDestinationRunPathArg(destination_run_path_group)
    flags.AddClearDestinationRunPathArg(destination_run_path_group)

  def Run(self, args):
    """Run the update command."""
    client = triggers.TriggersClient()
    trigger_ref = args.CONCEPTS.trigger.Parse()
    service_account_ref = args.CONCEPTS.service_account.Parse()
    update_mask = triggers.BuildUpdateMask(
        matching_criteria=args.matching_criteria is not None,
        service_account=(service_account_ref is not None) or
        args.clear_service_account,
        destination_run_service=args.destination_run_service is not None,
        destination_run_path=(args.destination_run_path is not None) or
        args.clear_destination_run_path,
        destination_run_region=args.destination_run_region is not None)
    operation = client.Patch(trigger_ref, args.matching_criteria,
                             service_account_ref, args.destination_run_service,
                             args.destination_run_path,
                             args.destination_run_region, update_mask)
    if args.async_:
      return operation
    return client.WaitFor(operation)
