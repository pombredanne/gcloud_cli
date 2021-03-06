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
"""Tests for the images export subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import daisy_test_base


class ImagesExportTestGA(daisy_test_base.DaisyBaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.image_name = 'my-image'
    self.destination_uri = 'gs://31dd/my-image.tar.gz'
    self.builder = daisy_utils._IMAGE_EXPORT_BUILDER.format(
        daisy_utils._DEFAULT_BUILDER_VERSION)
    self.tags = ['gce-daisy', 'gce-daisy-image-export']

  def PrepareDaisyMocksForExport(self, daisy_step, timeout='7200s',
                                 log_location=None, permissions=None,
                                 async_flag=False):
    super(ImagesExportTestGA, self).PrepareDaisyMocksWithRegionalBucket(
        daisy_step,
        timeout=timeout,
        log_location=log_location,
        permissions=permissions,
        async_flag=async_flag,
        is_import=False)

  def GetNetworkStepForExport(
      self, network=None, subnet=None, include_zone=True,
      include_empty_network=False, image_project='my-project',
      workflow='../workflows/export/image_export.wf.json',
      image_format=''):
    export_vars = []

    if subnet:
      daisy_utils.AppendArg(export_vars, 'subnet', subnet)

    if network:
      daisy_utils.AppendArg(export_vars, 'network', network)

    if include_zone:
      daisy_utils.AppendArg(export_vars, 'zone', 'my-region-c')

    daisy_utils.AppendArg(
        export_vars, 'scratch_bucket_gcs_path',
        'gs://{0}/'.format(self.GetScratchBucketNameWithRegion()))

    daisy_utils.AppendArg(export_vars, 'timeout',
                          daisy_test_base._DEFAULT_TIMEOUT)
    daisy_utils.AppendArg(export_vars, 'client_id', 'gcloud')
    daisy_utils.AppendArg(
        export_vars, 'source_image', 'projects/{0}/global/images/{1}'.format(
            image_project, self.image_name))
    daisy_utils.AppendArg(export_vars, 'destination_uri', self.destination_uri)
    daisy_utils.AppendArg(export_vars, 'format', image_format)
    daisy_utils.AppendArg(export_vars, 'client_version',
                          config.CLOUD_SDK_VERSION)

    return self.cloudbuild_v1_messages.BuildStep(
        args=export_vars, name=self.builder)

  def testCommonCase(self):
    build_step = self.GetNetworkStepForExport(include_zone=False)
    self.PrepareDaisyMocksForExport(build_step)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testExportFormat(self):
    build_step = self.GetNetworkStepForExport(
        include_zone=False,
        workflow='../workflows/export/image_export_ext.wf.json',
        image_format='vmdk')
    self.PrepareDaisyMocksForExport(build_step)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --export-format=vmdk
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testZoneFlag(self):
    build_step = self.GetNetworkStepForExport()
    self.PrepareDaisyMocksForExport(build_step)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --zone={2}
             """.format(self.image_name, self.destination_uri, 'my-region-c'))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testCloudbuildServiceNotEnabled(self):
    self._ExpectServiceUsage(build_enabled=False, compute_enabled=False)

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.PrepareDaisyBucketMocksWithRegion()

    with self.assertRaisesRegexp(console_io.UnattendedPromptError,
                                 'This prompt could not be answered because '
                                 'you are not in an interactive session.'):
      self.Run("""
               compute images export --image {0}
               --destination-uri {1}
               """.format(self.image_name, self.destination_uri))

    self.AssertErrContains('cloudbuild.googleapis.com')

  def testComputeServiceNotEnabled(self):
    self._ExpectServiceUsage(compute_enabled=False)

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.PrepareDaisyBucketMocksWithRegion()

    with self.assertRaisesRegexp(console_io.UnattendedPromptError,
                                 ('This prompt could not be answered because '
                                  'you are not in an interactive session.')):
      self.Run("""
               compute images export --image {0}
               --destination-uri {1}
               """.format(self.image_name, self.destination_uri))

    self.AssertErrContains('compute.googleapis.com')

  def testImageProject(self):
    build_step = self.GetNetworkStepForExport(include_zone=False,
                                              image_project='debian-cloud')
    self.PrepareDaisyMocksForExport(build_step)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --image-project debian-cloud
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testNetworkFlag(self):
    build_step = self.GetNetworkStepForExport(
        network=self.network, include_zone=False)
    self.PrepareDaisyMocksForExport(build_step)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --network {2}
             """.format(self.image_name, self.destination_uri, self.network))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testMissingImage(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--image | --image-family) must be specified.'):
      self.Run("""
               compute images export --destination-uri {0}
               """.format(self.destination_uri))

  def testMissingDestination(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --destination-uri: Must be specified'):
      self.Run("""
               compute images export --image {0}
               """.format(self.image_name))

  def testSubnetFlag(self):
    build_step = self.GetNetworkStepForExport(
        network=self.network, subnet=self.subnet)
    self.PrepareDaisyMocksForExport(build_step)

    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --network {2} --subnet {3} --zone my-region-c
             """.format(self.image_name, self.destination_uri, self.network,
                        self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testSubnetFlagNetworkVariableClearedIfNetworkFlagNotSpecified(self):
    build_step = self.GetNetworkStepForExport(
        network='', include_empty_network=True, subnet=self.subnet)
    self.PrepareDaisyMocksForExport(build_step)

    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --subnet {2} --zone my-region-c
             """.format(self.image_name, self.destination_uri, self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  # Subnet region logic is hosted by export cli tool, so there won't be
  # exception thrown anymore.
  def testSubnetFlagZoneAndRegionNotSpecified(self):
    daisy_step = self.GetNetworkStepForExport(subnet=self.subnet,
                                              include_zone=False)
    self.PrepareDaisyMocksForExport(daisy_step)

    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --subnet {2}
             """.format(self.image_name, self.destination_uri, self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testSubnetFlagZoneAsProperty(self):
    build_step = self.GetNetworkStepForExport(
        network=self.network, subnet=self.subnet)
    self.PrepareDaisyMocksForExport(build_step)

    properties.VALUES.compute.zone.Set('my-region-c')
    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --network {2} --subnet {3}
             """.format(self.image_name, self.destination_uri, self.network,
                        self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testSubnetFlagRegionAsProperty(self):
    build_step = self.GetNetworkStepForExport(
        network=self.network, subnet=self.subnet, include_zone=False)
    self.PrepareDaisyMocksForExport(build_step)

    properties.VALUES.compute.region.Set('my-region')
    self.Run("""
             compute images export --image {0} --destination-uri {1}
             --network {2} --subnet {3}
             """.format(self.image_name, self.destination_uri, self.network,
                        self.subnet))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testScratchBucketCreatedInSourceRegion(self):
    build_step = self.GetNetworkStepForExport(include_zone=False)
    self.PrepareDaisyMocks(build_step, is_import=False)

    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(bucket='31dd'),
        response=self.storage_v1_messages.Bucket(
            name='31dd',
            storageClass='REGIONAL',
            location=self.GetScratchBucketRegion()
        ),
    )

    daisy_bucket_name = self.GetScratchBucketNameWithRegion()
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_v1_messages.StorageBucketsGetRequest(
            bucket=daisy_bucket_name),
        exception=api_exceptions.HttpNotFoundError(None, None, None))
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                kind='storage#bucket',
                name=daisy_bucket_name,
                location=self.GetScratchBucketRegion(),

            ),
            project='my-project',
        ),
        response=self.storage_v1_messages.Bucket(id=daisy_bucket_name))

    self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testAllowFailedServiceAccountPermissionModification(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
    ])
    build_step = self.GetNetworkStepForExport(include_zone=False)
    self.PrepareDaisyMocksForExport(build_step, permissions=actual_permissions)

    # mock for 2 service accounts.
    for _ in range(2):
      self.mocked_crm_v1.projects.GetIamPolicy.Expect(
          request=(
              self.crm_v1_messages
              .CloudresourcemanagerProjectsGetIamPolicyRequest(
                  getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
                      options=self.crm_v1_messages.GetPolicyOptions(
                          requestedPolicyVersion=iam_util
                          .MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
                  resource='my-project')),
          response=self.permissions,
      )

      self.mocked_crm_v1.projects.SetIamPolicy.Expect(
          self.crm_v1_messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
              resource='my-project',
              setIamPolicyRequest=self.crm_v1_messages.SetIamPolicyRequest(
                  policy=self.permissions,),
          ),
          exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                      'url'))
    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --quiet
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains(
        """\
        [image-export] output
        """, normalize_space=True)

  def testAllowFailedIamGetRoles(self):
    self.PrepareDaisyBucketMocksWithRegion()
    self._ExpectServiceUsage()

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    get_request = self.crm_v1_messages \
      .CloudresourcemanagerProjectsGetIamPolicyRequest(
          getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
              options=self.crm_v1_messages.GetPolicyOptions(
                  requestedPolicyVersion=
                  iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
          resource='my-project')
    actual_permissions = self.crm_v1_messages.Policy(bindings=[])
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=actual_permissions,
    )

    self.mocked_iam_v1.roles.Get.Expect(
        self.iam_v1_messages.IamRolesGetRequest(
            name=daisy_utils.ROLE_COMPUTE_ADMIN),
        exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                    'url'))
    self.mocked_iam_v1.roles.Get.Expect(
        self.iam_v1_messages.IamRolesGetRequest(
            name=daisy_utils.ROLE_COMPUTE_STORAGE_ADMIN),
        exception=api_exceptions.HttpForbiddenError('response', 'content',
                                                    'url'))

    # Called once for each missed service account role.
    self._ExpectAddIamPolicyBinding(5)

    self._ExpectCloudBuild(self.GetNetworkStepForExport(include_zone=False))

    self.Run("""
             compute images export --image {0}
             --destination-uri {1} --quiet
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains(
        """\
        [image-export] output
        """, normalize_space=True)

  def testEditorPermissionIsSufficientForComputeAccount(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role=daisy_utils.ROLE_EDITOR),
    ])
    build_step = self.GetNetworkStepForExport(include_zone=False)
    self.PrepareDaisyMocksForExport(build_step, permissions=actual_permissions)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains(
        """\
        [image-export] output
        """, normalize_space=True)

  def testCustomRolePermissionIsSufficientForComputeAccount(self):
    actual_permissions = self.crm_v1_messages.Policy(bindings=[
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_COMPUTE_ADMIN),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_USER),
        self.crm_v1_messages.Binding(
            members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
            role=daisy_utils.ROLE_IAM_SERVICE_ACCOUNT_TOKEN_CREATOR),
        self.crm_v1_messages.Binding(
            members=[
                'serviceAccount:123456-compute@developer.gserviceaccount.com'
            ],
            role='roles/custom'),
    ])
    build_step = self.GetNetworkStepForExport(include_zone=False)
    self.PrepareDaisyMocksForExport(build_step, permissions=actual_permissions)

    self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             """.format(self.image_name, self.destination_uri))

    self.AssertOutputContains(
        """\
        [image-export] output
        """, normalize_space=True)


class ImagesExportTestBeta(ImagesExportTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDockerImageTag(self):
    self.builder = daisy_utils._IMAGE_EXPORT_BUILDER.format(
        daisy_utils._DEFAULT_BUILDER_VERSION)
    self.testCommonCase()

    self.builder = daisy_utils._IMAGE_EXPORT_BUILDER.format('latest')
    build_step = self.GetNetworkStepForExport(include_zone=False)
    self.PrepareDaisyMocksForExport(build_step)
    self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             --docker-image-tag latest
             """.format(self.image_name, self.destination_uri))
    self.AssertOutputContains("""\
        [image-export] output
        """, normalize_space=True)

  def testDestinationUriBucketOnlyGCSPath(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        r'Invalid value for [destination-uri]: must be a path to an object in Google Cloud Storage'
    ):
      self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             """.format(self.image_name, 'gs://bucket'))

  def testDestinationUriInvalidGCSPath(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        r'Invalid value for [destination-uri]: must be a path to an object in Google Cloud Storage'
    ):
      self.Run("""
             compute images export --image {0}
             --destination-uri {1}
             """.format(self.image_name, 'NOT_A_GCS_PATH'))


class ImagesExportTestAlpha(ImagesExportTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
