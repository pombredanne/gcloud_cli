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

"""Testing resources for genomics commands."""

from googlecloudsdk.api_lib.util import apis

GENOMICS_V1_MESSAGES = apis.GetMessagesModule('genomics', 'v1')

TEST_IAM_POLICY = GENOMICS_V1_MESSAGES.Policy(
    bindings=[
        GENOMICS_V1_MESSAGES.Binding(
            members=['group:test_viewer_group@googlegroups.com'],
            role='roles/viewer'),
        GENOMICS_V1_MESSAGES.Binding(
            members=['user:test_editor@test.com'],
            role='roles/editor'),
        GENOMICS_V1_MESSAGES.Binding(
            members=['user:test_owner@test.com'],
            role=u'roles/owner')],
    etag='<< Unique versioning etag bytefield >>',
    version=0)