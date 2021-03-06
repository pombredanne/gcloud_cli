# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the resource policies create-snapshot-schedule command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import resource_policies_base


class CreateSnapshotScheduleBetaTest(resource_policies_base.TestBase,
                                     parameterized.TestCase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.day_enum = (
        self.messages.ResourcePolicyWeeklyCycleDayOfWeek.DayValueValuesEnum)

  def _ExpectCreate(self, policy):
    request = self.messages.ComputeResourcePoliciesInsertRequest(
        project=self.Project(),
        region=self.region,
        resourcePolicy=policy)
    self.make_requests.side_effect = [[policy]]
    return request

  def testCreate_Simple(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        dailySchedule=self.messages.ResourcePolicyDailyCycle(
            daysInCycle=1, startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1),
            schedule=schedule))

    request = self._ExpectCreate(policy)

    result = self.Run('compute resource-policies create snapshot-schedule pol1 '
                      '--start-time 04:00 --region {} --daily-schedule '
                      '--max-retention-days 1'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_Description(self):
    description = 'This is a maintenance policy.'
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        dailySchedule=self.messages.ResourcePolicyDailyCycle(
            daysInCycle=1, startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        description=description,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 '
        '--start-time 04:00 --region {} --description "{}" --daily-schedule '
        '--max-retention-days 1'.format(self.region, description))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_StartTime(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        dailySchedule=self.messages.ResourcePolicyDailyCycle(
            daysInCycle=1, startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1'
        ' --start-time 03:00.52-1:00 --region {} --daily-schedule '
        '--max-retention-days 1'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_HourlySchedule(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        hourlySchedule=self.messages.ResourcePolicyHourlyCycle(
            hoursInCycle=2, startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 --region {} '
        ' --start-time 04:00Z --hourly-schedule 2 '
        '--max-retention-days 1'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_WeeklySchedule(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        weeklySchedule=self.messages.ResourcePolicyWeeklyCycle(dayOfWeeks=[
            self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                day=self.day_enum.MONDAY, startTime='04:00')
        ]))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 --region {} '
        ' --start-time 04:00Z --weekly-schedule monday '
        '--max-retention-days 1'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_WeeklyScheduleFromFile(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        weeklySchedule=self.messages.ResourcePolicyWeeklyCycle(dayOfWeeks=[
            self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                day=self.day_enum.MONDAY, startTime='04:00'),
            self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                day=self.day_enum.WEDNESDAY, startTime='10:00')
        ]))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=3),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    contents = ('[{"day": "MONDAY", "startTime": "04:00"}, '
                '{"day": "WEDNESDAY", "startTime": "02:00-8:00"}]')
    schedule_file = self.Touch(self.temp_path, 'my-schedule.json',
                               contents=contents)
    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 --region {0} '
        '--max-retention-days 3 --weekly-schedule-from-file {1}'.format(
            self.region, schedule_file))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_WeeklyScheduleDayIsConverted(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        weeklySchedule=self.messages.ResourcePolicyWeeklyCycle(dayOfWeeks=[
            self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                day=self.day_enum.THURSDAY, startTime='00:00')
        ]))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 --region {} '
        ' --start-time 17:00-07 --weekly-schedule wednesday '
        '--max-retention-days 1'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_WeeklyScheduleFromFileDayIsConverted(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        weeklySchedule=self.messages.ResourcePolicyWeeklyCycle(dayOfWeeks=[
            self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                day=self.day_enum.SUNDAY, startTime='23:00'),
            self.messages.ResourcePolicyWeeklyCycleDayOfWeek(
                day=self.day_enum.THURSDAY, startTime='00:00')
        ]))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=3),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    contents = ('[{"day": "MONDAY", "startTime": "04:00+05"}, '
                '{"day": "WEDNESDAY", "startTime": "16:00-8:00"}]')
    schedule_file = self.Touch(self.temp_path, 'my-schedule.json',
                               contents=contents)
    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 --region {0} '
        '--max-retention-days 3 --weekly-schedule-from-file {1}'.format(
            self.region, schedule_file))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_RetentionBehaviorFlags(self):
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        hourlySchedule=self.messages.ResourcePolicyHourlyCycle(
            hoursInCycle=2, startTime='04:00'))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1,
                onSourceDiskDelete=self.messages
                .ResourcePolicySnapshotSchedulePolicyRetentionPolicy
                .OnSourceDiskDeleteValueValuesEnum.KEEP_AUTO_SNAPSHOTS),
            schedule=schedule))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 --region {} '
        '--start-time 04:00Z --hourly-schedule 2 --max-retention-days 1 '
        '--on-source-disk-delete keep-auto-snapshots'.format(self.region))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  @parameterized.named_parameters(
      ('WithStorageLocation', '--storage-location us-west1', ['us-west1']),
      ('WithoutStorageLocation', '', []))
  def testCreate_SnapshotProperties(self, storage_location_flag,
                                    storage_location_value):
    description = 'This is a maintenance policy.'
    schedule = self.messages.ResourcePolicySnapshotSchedulePolicySchedule(
        dailySchedule=self.messages.ResourcePolicyDailyCycle(
            daysInCycle=1, startTime='04:00'))
    labels_cls = (
        self.messages.ResourcePolicySnapshotSchedulePolicySnapshotProperties
        .LabelsValue)
    snapshot_properties = (
        self.messages.ResourcePolicySnapshotSchedulePolicySnapshotProperties(
            guestFlush=True,
            labels=labels_cls(additionalProperties=[
                labels_cls.AdditionalProperty(key='k1', value='v1'),
                labels_cls.AdditionalProperty(key='k2', value='v2')
            ]),
            storageLocations=storage_location_value))
    policy = self.messages.ResourcePolicy(
        name='pol1',
        region=self.region,
        description=description,
        snapshotSchedulePolicy=self.messages
        .ResourcePolicySnapshotSchedulePolicy(
            retentionPolicy=self.messages
            .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
                maxRetentionDays=1),
            schedule=schedule,
            snapshotProperties=snapshot_properties))
    request = self._ExpectCreate(policy)

    result = self.Run(
        'compute resource-policies create snapshot-schedule pol1 '
        '--start-time 04:00Z --region {} --description "{}" --daily-schedule '
        '--max-retention-days 1 --guest-flush --snapshot-labels k1=v1,k2=v2 {}'
        .format(self.region, description, storage_location_flag))

    self.CheckRequests([(self.compute.resourcePolicies, 'Insert', request)])
    self.assertEqual(result, policy)

  def testCreate_NoDailyCycleShouldFail(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'cannot request a non-daily cycle.'):
      self.Run(
          'compute resource-policies create snapshot-schedule pol1 --region {0}'
          ' --max-retention-days 1 --no-daily-schedule  --start-time 04:00Z'
          .format(self.region))

  @parameterized.parameters(
      '--start-time 04:00Z --weekly-schedule-from-file myfile.txt',
      '--weekly-schedule monday', '--daily-schedule', '--hourly-schedule 2')
  def testCreate_FreqGroupValidation(self, flags):
    with self.AssertRaisesArgumentError():
      self.Run(
          'compute resource-policies create snapshot-schedule pol1 --region {0}'
          ' --max-retention-days 1 {1}'.format(self.region, flags))

  @parameterized.parameters(
      ('[{"day": "MONDAY"}]',
       'Each JSON/YAML object in the list must have the following keys: '
       '[day, startTime].'),
      ('[{"startTime": "04:00"}]',
       'Each JSON/YAML object in the list must have the following keys: '
       '[day, startTime].'),
      ('[{}]',
       'Each JSON/YAML object in the list must have the following keys: '
       '[day, startTime].'),
      ('[{"day": "CATURDAY", "startTime": "04:00Z"}]',
       'Invalid value for `day`: [CATURDAY]'),
      ('', 'File cannot be empty.'))
  def testCreate_InvalidWeeklyFileError(self, contents, message):
    schedule_file = self.Touch(self.temp_path, 'my-schedule.json',
                               contents=contents)
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException, message):
      self.Run(
          'compute resource-policies create snapshot-schedule pol1 --region {0}'
          ' --max-retention-days 1 --weekly-schedule-from-file {1}'.format(
              self.region, schedule_file))


class CreateSnapshotScheduleAlphaTest(CreateSnapshotScheduleBetaTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
