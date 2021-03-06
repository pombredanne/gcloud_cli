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
"""Tests for Spanner database sessions library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from collections import OrderedDict
import textwrap
from apitools.base.py import extra_types
from googlecloudsdk.api_lib.spanner import database_sessions
from googlecloudsdk.api_lib.spanner.database_sessions import MutationFactory
from googlecloudsdk.command_lib.spanner.write_util import Table
from googlecloudsdk.core import resources
from tests.lib.surface.spanner import base


class DatabaseSessionsClientTest(base.SpannerTestBase):

  def SetUp(self):
    self.db_ref = resources.REGISTRY.Parse(
        'mydb',
        params={
            'instancesId': 'myins',
            'projectsId': self.Project(),
        },
        collection='spanner.projects.instances.databases')
    self.session_ref = resources.REGISTRY.Parse(
        'mysession',
        params={
            'projectsId': self.Project(),
            'instancesId': 'myins',
            'databasesId': 'mydb',
        },
        collection='spanner.projects.instances.databases.sessions')

  def _GivenCommitRequest(self, is_dml=False, mutations=None):
    if is_dml:
      commit_request = self.msgs.CommitRequest(
          mutations=[], transactionId=bytes(123))
    else:
      commit_request = self.msgs.CommitRequest(
          mutations=mutations,
          singleUseTransaction=self.msgs.TransactionOptions(
              readOnly=None, readWrite=self.msgs.ReadWrite()))
    return self.msgs.SpannerProjectsInstancesDatabasesSessionsCommitRequest(
        session=self.session_ref.RelativeName(), commitRequest=commit_request)

  def _GivenExecuteSqlRequest(self, sql, transaction):
    return self.msgs.ExecuteSqlRequest(
        sql=sql,
        queryMode=self.msgs.ExecuteSqlRequest.QueryModeValueValuesEnum.NORMAL,
        transaction=transaction)

  def _ExpectBeginTransaction(self, transaction):
    transaction_options = self.msgs.TransactionOptions(
        partitionedDml=self.msgs.PartitionedDml())
    begin_transaction_req = self.msgs.BeginTransactionRequest(
        options=transaction_options)
    req = (
        self.msgs
        .SpannerProjectsInstancesDatabasesSessionsBeginTransactionRequest(
            beginTransactionRequest=begin_transaction_req,
            session=self.session_ref.RelativeName()))
    self.client.projects_instances_databases_sessions.BeginTransaction.Expect(
        request=req, response=transaction)

  def testCreate(self):
    response = self.msgs.Session()
    request = self.msgs.SpannerProjectsInstancesDatabasesSessionsCreateRequest(
        database=self.db_ref.RelativeName())
    self.client.projects_instances_databases_sessions.Create.Expect(
        request=request, response=response)
    self.assertEqual(database_sessions.Create(self.db_ref), response)

  def testList(self):
    session = self.msgs.Session()
    response = self.msgs.ListSessionsResponse(sessions=[session])
    request = self.msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
        database=self.session_ref.RelativeName())
    self.client.projects_instances_databases_sessions.List.Expect(
        request=request, response=response)
    self.assertEqual(next(database_sessions.List(self.session_ref)), session)

  def testListWithFilter(self):
    session = self.msgs.Session(
        labels=self.msgs.Session.LabelsValue(additionalProperties=[
            self.msgs.Session.LabelsValue.AdditionalProperty(
                key='aLabel', value='stuff')
        ]))
    response = self.msgs.ListSessionsResponse(sessions=[session])
    server_filter = 'labels.aLabel:*'
    request = self.msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
        database=self.session_ref.RelativeName(), filter=server_filter)
    self.client.projects_instances_databases_sessions.List.Expect(
        request=request, response=response)
    self.assertEqual(
        next(database_sessions.List(self.session_ref, server_filter)), session)

  def testDelete(self):
    response = self.msgs.Empty()
    request = self.msgs.SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
        name=self.session_ref.RelativeName())
    self.client.projects_instances_databases_sessions.Delete.Expect(
        request=request, response=response)
    self.assertEqual(database_sessions.Delete(self.session_ref), response)

  def testExecuteSql(self):
    response = self.msgs.ResultSet()
    transaction_options = self.msgs.TransactionOptions(
        readOnly=self.msgs.ReadOnly(strong=True))
    transaction = self.msgs.TransactionSelector(singleUse=transaction_options)
    execute_sql_request = self._GivenExecuteSqlRequest('sql', transaction)
    req = self.msgs.SpannerProjectsInstancesDatabasesSessionsExecuteSqlRequest(
        session=self.session_ref.RelativeName(),
        executeSqlRequest=execute_sql_request)
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=req, response=response)
    self.assertEqual(
        database_sessions.ExecuteSql(self.session_ref, 'sql', 'NORMAL'),
        response)

  def testExecuteSqlWithTimeout(self):
    timeout = 9
    client = database_sessions._GetClientInstance('compute', 'v1',
                                                  http_timeout_sec=timeout)
    self.assertEqual(timeout, client.http.timeout)

  def testExecuteSqlWithDml(self):
    response = self.msgs.ResultSet(
        metadata=self.msgs.ResultSetMetadata(
            transaction=self.msgs.Transaction(id=bytes(123))))
    transaction_options = self.msgs.TransactionOptions(
        readWrite=self.msgs.ReadWrite())
    transaction = self.msgs.TransactionSelector(begin=transaction_options)
    execute_sql_request = self._GivenExecuteSqlRequest(
        'INSERT abc (a) values (1)', transaction)
    req = self.msgs.SpannerProjectsInstancesDatabasesSessionsExecuteSqlRequest(
        session=self.session_ref.RelativeName(),
        executeSqlRequest=execute_sql_request)
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=req, response=response)
    self.client.projects_instances_databases_sessions.Commit.Expect(
        request=self._GivenCommitRequest(True),
        response=self.msgs.CommitResponse())
    self.assertEqual(
        database_sessions.ExecuteSql(
            self.session_ref, 'INSERT abc (a) values (1)', 'NORMAL'), response)

  def testExecuteSqlWithPartitionedDml(self):
    transaction = self.msgs.Transaction(id=bytes(123))
    response = self.msgs.ResultSet(
        metadata=self.msgs.ResultSetMetadata(
            transaction=self.msgs.Transaction(id=transaction.id)))
    execute_sql_request = self._GivenExecuteSqlRequest(
        'INSERT abc (a) values (1)',
        self.msgs.TransactionSelector(id=transaction.id))
    self._ExpectBeginTransaction(transaction)
    req = self.msgs.SpannerProjectsInstancesDatabasesSessionsExecuteSqlRequest(
        session=self.session_ref.RelativeName(),
        executeSqlRequest=execute_sql_request)
    self.client.projects_instances_databases_sessions.ExecuteSql.Expect(
        request=req, response=response)
    self.assertEqual(
        database_sessions.ExecuteSql(
            self.session_ref, 'INSERT abc (a) values (1)', 'NORMAL', True),
        response)

  def testCommit(self):
    response = self.msgs.CommitResponse()
    mutations = _GetMutations()
    self.client.projects_instances_databases_sessions.Commit.Expect(
        request=self._GivenCommitRequest(False, mutations), response=response)
    self.assertEquals(
        database_sessions.Commit(self.session_ref, mutations), response)


class MutationTest(base.SpannerTestBase):

  def testInsertMutation(self):
    insert_mutation = _GetMutations()[0]

    self.assertEqual(
        self.msgs.Mutation(
            insert=self.msgs.Write(
                columns=['SingerId', 'FirstName', 'LastName'],
                table='Singers',
                values=[
                    self.msgs.Write.ValuesValueListEntry(entry=[
                        extra_types.JsonValue(string_value='2'),
                        extra_types.JsonValue(string_value='abc'),
                        extra_types.JsonValue(string_value='cab')
                    ])
                ])),
        insert_mutation)

  def testUpdateMutation(self):
    update_mutation = _GetMutations()[1]

    self.assertEqual(
        self.msgs.Mutation(
            update=self.msgs.Write(
                columns=['SingerId', 'FirstName', 'LastName'],
                table='Singers',
                values=[
                    self.msgs.Write.ValuesValueListEntry(entry=[
                        extra_types.JsonValue(string_value='2'),
                        extra_types.JsonValue(string_value='abc'),
                        extra_types.JsonValue(string_value='cab')
                    ])
                ])),
        update_mutation)

  def testDeleteMutation(self):
    delete_mutation = _GetMutations()[2]

    self.assertEqual(
        self.msgs.Mutation(
            delete=self.msgs.Delete(
                table='Singers',
                keySet=self.msgs.KeySet(keys=[
                    self.msgs.KeySet.KeysValueListEntry(entry=[
                        extra_types.JsonValue(string_value='2'),
                    ])
                ]))),
        delete_mutation)


def _GetMutations():
  ddl = [
      textwrap.dedent("""
          CREATE TABLE Singers (
          SingerId INT64 NOT NULL,
          FirstName STRING(MAX),
          LastName STRING(MAX),) PRIMARY KEY(SingerId)
  """)
  ]

  table = Table.FromDdl(ddl, 'Singers')
  data = OrderedDict([
      ('SingerId', '2'),
      ('FirstName', 'abc'),
      ('LastName', 'cab'),
  ])
  keys = ['2']

  return [
      MutationFactory.Insert(table, data),
      MutationFactory.Update(table, data),
      MutationFactory.Delete(table, keys),
  ]
