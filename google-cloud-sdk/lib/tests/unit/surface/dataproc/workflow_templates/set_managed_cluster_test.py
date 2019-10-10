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
"""Test of the 'workflow-template set-managed-cluster' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy

from apitools.base.py import encoding

from googlecloudsdk import calliope

from googlecloudsdk.core import properties
from tests.lib.surface.dataproc import compute_base
from tests.lib.surface.dataproc import unit_base


class WorkflowTemplateSetManagedClusterUnitTest(
    unit_base.DataprocUnitTestBase, compute_base.BaseComputeUnitTest):
  """Tests for dataproc workflow-template set-managed-cluster."""

  def MakeManagedCluster(self, **kwargs):
    cluster = self.MakeCluster(**kwargs)
    return self.messages.ManagedCluster(
        clusterName=cluster.clusterName,
        config=cluster.config,
        labels=cluster.labels)

  def ExpectSetManagedCluster(self,
                              workflow_template=None,
                              response=None,
                              exception=None):
    if not (response or exception):
      response = copy.deepcopy(workflow_template)
    self.mock_client.projects_regions_workflowTemplates.Update.Expect(
        workflow_template, response=response, exception=exception)

  def ExpectCallSetManagedCluster(self,
                                  workflow_template=None,
                                  managed_cluster=None,
                                  response=None,
                                  exception=None):
    if not workflow_template:
      workflow_template = self.MakeWorkflowTemplate()
    self.ExpectGetWorkflowTemplate(
        name=workflow_template.name,
        version=workflow_template.version,
        response=workflow_template)
    if not managed_cluster:
      cluster_name = 'test-cluster'
      managed_cluster = self.MakeManagedCluster(clusterName=cluster_name)
    workflow_template.placement = self.messages.WorkflowTemplatePlacement(
        managedCluster=managed_cluster)
    if not (response or exception):
      response = copy.deepcopy(workflow_template)
    self.ExpectSetManagedCluster(
        workflow_template, response=response, exception=exception)

  def testSetManagedCluster(self):
    workflow_template = self.MakeWorkflowTemplate()
    cluster_name = 'test-cluster'
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        zoneUri='us-west1-a',
        masterMachineTypeUri='n1-standard-2',
        workerConfigNumInstances=2)
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)
    result = self.RunDataproc('workflow-templates set-managed-cluster {0} '
                              '--cluster-name {1} '
                              '--zone us-west1-a --num-workers 2 '
                              '--master-machine-type n1-standard-2'.format(
                                  self.WORKFLOW_TEMPLATE, cluster_name))
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedClusterFlags(self):
    cluster_name = 'test-cluster'
    zone = 'foo-zone'
    master_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    bucket = 'foo-bucket'
    num_masters = 3
    num_workers = 7
    num_preemptible_workers = 5
    image_version = '1.7'
    network = 'foo-network'
    network_uri = ('https://compute.googleapis.com/compute/v1/projects/'
                   'fake-project/global/networks/foo-network')
    action_uris = ['gs://my-bucket/action1.sh', 'gs://my-bucket/action2.sh']
    initialization_actions = [
        self.messages.NodeInitializationAction(
            executableFile=action_uris[0], executionTimeout='120s'),
        self.messages.NodeInitializationAction(
            executableFile=action_uris[1], executionTimeout='120s')
    ]
    service_account = 'test-account'
    scope_list = 'https://www.googleapis.com/auth/dataproc-stuff,cloud-platform'
    scope_uris = [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/dataproc-stuff',
    ]
    cluster_properties = collections.OrderedDict([
        ('core:com.foo', 'foo'),
        ('hdfs:com.bar', 'bar')])
    cluster_metadata = collections.OrderedDict([
        ('key1', 'value1'),
        ('key2', 'value2')])

    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        configBucket=bucket,
        imageVersion=image_version,
        masterMachineTypeUri=master_machine_type,
        workerMachineTypeUri=worker_machine_type,
        networkUri=network_uri,
        masterConfigNumInstances=num_masters,
        workerConfigNumInstances=num_workers,
        secondaryWorkerConfigNumInstances=num_preemptible_workers,
        zoneUri=zone,
        initializationActions=initialization_actions,
        serviceAccount=service_account,
        serviceAccountScopes=scope_uris,
        properties=encoding.DictToAdditionalPropertyMessage(
            cluster_properties, self.messages.SoftwareConfig.PropertiesValue),
        tags=['tag1', 'tag2'],
        metadata=encoding.DictToAdditionalPropertyMessage(
            cluster_metadata, self.messages.GceClusterConfig.MetadataValue))

    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    command = ('workflow-templates set-managed-cluster {template} '
               '--cluster-name {cluster_name} '
               '--bucket {bucket} '
               '--zone {zone} '
               '--num-masters {num_masters} '
               '--num-workers {num_workers} '
               '--master-machine-type {master_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--network {network} '
               '--image-version {image_version} '
               '--initialization-action-timeout 2m '
               '--initialization-actions {actions} '
               '--num-preemptible-workers {num_preemptible} '
               '--service-account {service_account} '
               '--scopes {scopes} '
               '--properties core:com.foo=foo,hdfs:com.bar=bar '
               '--tags tag1,tag2 '
               '--metadata key1=value1,key2=value2 ').format(
                   template=self.WORKFLOW_TEMPLATE,
                   cluster_name=cluster_name,
                   bucket=bucket,
                   zone=zone,
                   num_masters=num_masters,
                   num_workers=num_workers,
                   master_machine_type=master_machine_type,
                   worker_machine_type=worker_machine_type,
                   network=network,
                   image_version=image_version,
                   actions=','.join(action_uris),
                   num_preemptible=num_preemptible_workers,
                   service_account=service_account,
                   scopes=scope_list)

    result = self.RunDataproc(command)
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedClusterAutoZone(self):
    properties.VALUES.dataproc.region.Set('us-test1')
    template_name = self.WorkflowTemplateName(region='us-test1')
    cluster_name = 'test-cluster'
    workflow_template = self.MakeWorkflowTemplate(name=template_name)
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name, region='us-test1', zoneUri='')
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)
    result = self.RunDataproc(
        'workflow-templates set-managed-cluster {template} '
        '--cluster-name {cluster_name} '
        '--zone=""'.format(
            template=workflow_template.id, cluster_name=cluster_name))
    self.AssertMessagesEqual(workflow_template, result)
    self.AssertErrEquals('')

  def testSetManagedClusterNoName(self):
    workflow_template = self.MakeWorkflowTemplate()
    project = self.Project()
    zone = 'foo-zone'
    managed_cluster = self.MakeManagedCluster(
        clusterName=workflow_template.id, projectId=project, zoneUri=zone)
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    result = self.RunDataproc(
        'workflow-templates set-managed-cluster {template} '
        '--zone {zone}'.format(template=workflow_template.id, zone=zone))
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedClusterOmitZone_globalRegion(self):
    self.MockCompute()
    self.ExpectListZones()
    self.WriteInput('3\n')  # us-central1-a

    template_name = self.WorkflowTemplateName()
    cluster_name = 'test-cluster'
    workflow_template = self.MakeWorkflowTemplate(name=template_name)
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name, zoneUri='')
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)
    result = self.RunDataproc(
        'workflow-templates set-managed-cluster {template} '
        '--cluster-name {cluster_name} '
        '--zone=""'.format(
            template=workflow_template.id, cluster_name=cluster_name))
    self.AssertMessagesEqual(workflow_template, result)
    self.AssertErrContains('PROMPT_CHOICE')
    self.AssertErrContains(
        '"choices": ["europe-west1-a", "europe-west1-b (DELETED)", '
        '"us-central1-a (DEPRECATED)", "us-central1-b"]')


class WorkflowTemplateSetManagedClusterUnitTestBeta(
    WorkflowTemplateSetManagedClusterUnitTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA

  def testSetManagedClusterFlags(self):
    cluster_name = 'test-cluster'
    zone = 'foo-zone'
    master_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    bucket = 'foo-bucket'
    num_masters = 3
    num_workers = 7
    num_preemptible_workers = 5
    image_version = '1.7'
    network = 'foo-network'
    network_uri = ('https://compute.googleapis.com/compute/beta/projects/'
                   'fake-project/global/networks/foo-network')
    action_uris = ['gs://my-bucket/action1.sh', 'gs://my-bucket/action2.sh']
    initialization_actions = [
        self.messages.NodeInitializationAction(
            executableFile=action_uris[0], executionTimeout='120s'),
        self.messages.NodeInitializationAction(
            executableFile=action_uris[1], executionTimeout='120s')
    ]
    service_account = 'test-account'
    scope_list = 'https://www.googleapis.com/auth/dataproc-stuff,cloud-platform'
    scope_uris = [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/dataproc-stuff',
    ]
    cluster_properties = collections.OrderedDict([
        ('core:com.foo', 'foo'),
        ('hdfs:com.bar', 'bar')])
    cluster_metadata = collections.OrderedDict([
        ('key1', 'value1'),
        ('key2', 'value2')])
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        configBucket=bucket,
        imageVersion=image_version,
        masterMachineTypeUri=master_machine_type,
        workerMachineTypeUri=worker_machine_type,
        networkUri=network_uri,
        masterConfigNumInstances=num_masters,
        workerConfigNumInstances=num_workers,
        secondaryWorkerConfigNumInstances=num_preemptible_workers,
        zoneUri=zone,
        initializationActions=initialization_actions,
        serviceAccount=service_account,
        serviceAccountScopes=scope_uris,
        properties=encoding.DictToAdditionalPropertyMessage(
            cluster_properties, self.messages.SoftwareConfig.PropertiesValue),
        tags=['tag1', 'tag2'],
        metadata=encoding.DictToAdditionalPropertyMessage(
            cluster_metadata, self.messages.GceClusterConfig.MetadataValue))

    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    command = ('workflow-templates set-managed-cluster {template} '
               '--cluster-name {cluster_name} '
               '--bucket {bucket} '
               '--zone {zone} '
               '--num-masters {num_masters} '
               '--num-workers {num_workers} '
               '--master-machine-type {master_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--network {network} '
               '--image-version {image_version} '
               '--initialization-action-timeout 2m '
               '--initialization-actions {actions} '
               '--num-preemptible-workers {num_preemptible} '
               '--service-account {service_account} '
               '--scopes {scopes} '
               '--properties core:com.foo=foo,hdfs:com.bar=bar '
               '--tags tag1,tag2 '
               '--metadata key1=value1,key2=value2 ').format(
                   template=self.WORKFLOW_TEMPLATE,
                   cluster_name=cluster_name,
                   bucket=bucket,
                   zone=zone,
                   num_masters=num_masters,
                   num_workers=num_workers,
                   master_machine_type=master_machine_type,
                   worker_machine_type=worker_machine_type,
                   network=network,
                   image_version=image_version,
                   actions=','.join(action_uris),
                   num_preemptible=num_preemptible_workers,
                   service_account=service_account,
                   scopes=scope_list)

    result = self.RunDataproc(command)
    self.AssertMessagesEqual(workflow_template, result)

  def testSetManagedClusterBetaFlags(self):
    cluster_name = 'test-cluster'
    master_accelerator_type = 'foo-gpu'
    worker_accelerator_type = 'bar-gpu'
    zone = 'foo-zone'
    image = 'test-image'
    image_uri = ('https://compute.googleapis.com/compute/beta/projects/'
                 'fake-project/global/images/test-image')
    master_machine_type = 'foo-type'
    worker_machine_type = 'bar-type'
    master_min_cpu_platform = 'Intel Skylake'
    worker_min_cpu_platform = 'Intel Haswell'
    managed_cluster = self.MakeManagedCluster(
        clusterName=cluster_name,
        projectId=self.Project(),
        masterAcceleratorTypeUri=master_accelerator_type,
        masterAcceleratorCount=1,
        workerAcceleratorTypeUri=worker_accelerator_type,
        workerAcceleratorCount=2,
        masterMachineTypeUri=master_machine_type,
        workerMachineTypeUri=worker_machine_type,
        masterBootDiskSizeGb=15,
        workerBootDiskSizeGb=30,
        secondaryWorkerBootDiskSizeGb=42,
        masterBootDiskType='pd-standard',
        workerBootDiskType='pd-ssd',
        secondaryWorkerBootDiskType='pd-standard',
        internalIpOnly=True,
        imageUri=image_uri,
        zoneUri=zone)
    self.AddMinCpuPlatform(managed_cluster, master_min_cpu_platform,
                           worker_min_cpu_platform)

    workflow_template = self.MakeWorkflowTemplate()
    self.ExpectCallSetManagedCluster(
        workflow_template=workflow_template, managed_cluster=managed_cluster)

    command = ('workflow-templates set-managed-cluster {template} '
               '--cluster-name {cluster_name} '
               '--master-accelerator type={master_accelerator_type},count=1 '
               '--worker-accelerator type={worker_accelerator_type},count=2 '
               '--master-boot-disk-size 15GB '
               '--worker-boot-disk-size 30GB '
               '--master-boot-disk-type pd-standard '
               '--worker-boot-disk-type pd-ssd '
               '--master-machine-type {master_machine_type} '
               '--worker-machine-type {worker_machine_type} '
               '--image {image} '
               '--preemptible-worker-boot-disk-size 42GB '
               '--preemptible-worker-boot-disk-type pd-standard '
               '--master-min-cpu-platform="{master_min_cpu_platform}" '
               '--worker-min-cpu-platform="{worker_min_cpu_platform}" '
               '--no-address '
               '--zone {zone} ').format(
                   template=self.WORKFLOW_TEMPLATE,
                   cluster_name=cluster_name,
                   master_accelerator_type=master_accelerator_type,
                   worker_accelerator_type=worker_accelerator_type,
                   master_machine_type=master_machine_type,
                   worker_machine_type=worker_machine_type,
                   master_min_cpu_platform=master_min_cpu_platform,
                   worker_min_cpu_platform=worker_min_cpu_platform,
                   image=image,
                   zone=zone)

    result = self.RunDataproc(command)
    self.AssertMessagesEqual(workflow_template, result)


class WorkflowTemplateSetManagedClusterUnitTestAlpha(
    WorkflowTemplateSetManagedClusterUnitTestBeta):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
