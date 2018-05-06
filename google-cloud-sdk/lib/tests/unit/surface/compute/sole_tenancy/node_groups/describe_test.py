# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Tests for the sole-tenancy node-groups describe subcommand."""
import textwrap

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class NodeGroupsDescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.NODE_GROUPS[0]],
    ])
    self.Run('compute sole-tenancy node-groups describe group-1 '
             '--zone zone-1')

    self.CheckRequests(
        [(self.compute_alpha.nodeGroups,
          'Get',
          self.messages.ComputeNodeGroupsGetRequest(
              nodeGroup='group-1',
              project='my-project',
              zone='zone-1'))],
    )
    self.assertMultiLineEqual(
        self.stdout.getvalue(),
        textwrap.dedent("""\
            creationTimestamp: '2018-01-23T10:00:00.0Z'
            description: description1
            kind: compute#nodeGroup
            name: group-1
            nodeTemplate: https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/nodeTemplates/template-1
            nodes:
            - index: 1
              instances:
              - https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/instances/instance-1
              - https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/instances/instance-2
              nodeType: iAPX-286
            - index: 2
              instances:
              - https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/instances/instance-3
              nodeType: iAPX-286
            selfLink: https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/nodeGroups/group-1
            zone: zone-1
            """))


if __name__ == '__main__':
  test_case.main()
