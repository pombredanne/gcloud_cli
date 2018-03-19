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
"""Tests for the forwarding-rules create subcommand."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GlobalForwardingRulesCreateTest(test_base.BaseTest):

  def testGlobalMutuallyExclusiveWithTargetInstance(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-instance\] for a global '
        'forwarding rule.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --global
            --ports 80
            --target-instance target-instance-1
          """)

    self.CheckRequests()

  def testGlobalMutuallyExclusiveWithTargetPool(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-pool\] for a global '
        'forwarding rule.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --global
            --ports 80
            --target-pool target-instance-1
          """)

    self.CheckRequests()

  def testMutuallyExclusiveTargetPoolTargetInstance(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-instance: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-pool target-pool-1
            --ports 80
            --target-instance target-instance-1
          """)

    self.CheckRequests()

  def testMutuallyExclusiveTargetInstanceTargetHttpProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-instance target-instance-1
            --ports 80
            --target-http-proxy target-http-proxy-1
          """)

    self.CheckRequests()

  def testRegionGlobalFlagsMutuallyExclusive(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --region '
        'may be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-pool target-pool-1
            --region us-central1
            --ports 80
            --global
          """)

    self.CheckRequests()

  def testSimpleCaseWithGlobalTargetHttpProxy(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy target-http-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testSimpleCaseWithGlobalTargetHttpProxyEsp(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy target-http-proxy-1
          --ip-protocol ESP
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  IPProtocol=(self.messages.ForwardingRule.
                              IPProtocolValueValuesEnum('ESP')),
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testSimpleCaseWithGlobalTargetHttpProxyUdp(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy target-http-proxy-1
          --ip-protocol UDP
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  IPProtocol=(self.messages.ForwardingRule.
                              IPProtocolValueValuesEnum('UDP')),
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testGlobalRequiresPorts(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--ports\] is required for global forwarding rules'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --global
            --target-http-proxy target-http-proxy-1
          """)

    self.CheckRequests()

  def testHttpProxyUriSupport(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-http-proxy {compute_uri}/projects/my-project/global/targetHttpProxies/target-http-proxy-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      self.messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testSimpleCaseWithGlobalTargetHttpsProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-https-proxy target-https-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetHttpsProxies/'
                          'target-https-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testHttpsProxyUriSupport(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 8080
          --target-https-proxy {uri}/projects/my-project/global/targetHttpsProxies/target-https-proxy-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetHttpsProxies/'
                          'target-https-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testMutuallyExclusiveTargetHttpProxyTargetHttpsProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 80
            --target-http-proxy target-http-proxy-1
            --target-https-proxy target-https-proxy-1
          """)

  def testSimpleCaseWithGlobalTargetSslProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-ssl-proxy target-ssl-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='443',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetSslProxies/'
                          'target-ssl-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testSslProxyUriSupport(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-ssl-proxy
          {uri}/projects/my-project/global/targetSslProxies/target-ssl-proxy-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='443',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetSslProxies/'
                          'target-ssl-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testMutuallyExclusiveTargetHttpProxyTargetSslProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-http-proxy target-http-proxy-1
            --target-ssl-proxy target-ssl-proxy-1
          """)

  def testMutuallyExclusiveTargetHttpsProxyTargetSslProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-https-proxy: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-https-proxy target-https-proxy-1
            --target-ssl-proxy target-ssl-proxy-1
          """)

  def testSimpleCaseWithGlobalTargetTcpProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-tcp-proxy target-tcp-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='443',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetTcpProxies/'
                          'target-tcp-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testTcpProxyUriSupport(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-tcp-proxy
          {uri}/projects/my-project/global/targetTcpProxies/target-ssl-proxy-1
        """.format(uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='443',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetTcpProxies/'
                          'target-ssl-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testMutuallyExclusiveTargetHttpProxyTargetTcpProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-http-proxy: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-http-proxy target-http-proxy-1
            --target-tcp-proxy target-tcp-proxy-1
          """)

  def testMutuallyExclusiveTargetHttpsProxyTargetTcpProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-https-proxy: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-https-proxy target-https-proxy-1
            --target-tcp-proxy target-tcp-proxy-1
          """)

  def testMutuallyExclusiveTargetSslProxyTargetTcpProxy(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-ssl-proxy: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --ports 443
            --target-ssl-proxy target-ssl-proxy-1
            --target-tcp-proxy target-tcp-proxy-1
          """)

  def testRegionalMutuallyExclusiveWithTargetTcpProxy(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-tcp-proxy\] for a regional '
        'forwarding rule.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-centeral2
            --target-tcp-proxy target-tcp-proxy-1
          """)

    self.CheckRequests()

  def testIpAddressGlobalResource(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --target-http-proxy target-proxy-1
          --ports 8080
          --address foo
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/global/addresses/foo')
                  .format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-proxy-1').format(
                              compute_uri=self.compute_uri),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testIpAddressGlobalURI(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --target-http-proxy target-proxy-1
          --ports 8080
          --address {compute_uri}/projects/my-project/global/addresses/foo
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/global/addresses/foo')
                  .format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-proxy-1').format(
                              compute_uri=self.compute_uri),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)


class IpVersionTest(test_base.BaseTest):

  def SetUp(self):
    properties.VALUES.core.check_gce_metadata.Set(False)

  def testSimpleCaseWithGlobalTargetTcpProxy(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --global
          --ports 443
          --target-tcp-proxy target-tcp-proxy-1
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='443',
                  target=(self.compute_uri + '/projects/'
                          'my-project/global/targetTcpProxies/'
                          'target-tcp-proxy-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)


class VpnTests(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.track = calliope_base.ReleaseTrack.BETA

  def testSimpleTargetVpnGateway(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-vpn-gateway target-vpn-gateway-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(self.compute_uri + '/projects/'
                          'my-project/regions/us-central2/targetVpnGateways/'
                          'target-vpn-gateway-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testMutuallyExclusiveTargetInstanceWithTargetVpnGateway(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-instance: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-instance target-instance-1
            --ports 80
            --target-vpn-gateway target-vpn-gateway1
          """)

    self.CheckRequests()


class RegionalForwardingRulesCreateTest(test_base.BaseTest):

  def SetUp(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch(
        'googlecloudsdk.core.console.console_io.CanPrompt', return_value=True)

  def testRegionalMutuallyExclusiveWithTargetPool(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-http-proxy\] for a regional '
        'forwarding rule.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-centeral2
            --target-http-proxy target-http-proxy-1
          """)

    self.CheckRequests()

  def testSimpleCaseWithRegion(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testIpAddressOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --address 162.222.178.83
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress='162.222.178.83',
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testIpAddressResource(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --address foo
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'addresses/foo').format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testIpAddressURI(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --address {compute_uri}/projects/my-project/regions/us-central2/addresses/foo
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPAddress=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'addresses/foo').format(compute_uri=self.compute_uri),
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testIpProtocolOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --ip-protocol TCP
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPProtocol=(
                      self.messages.ForwardingRule.IPProtocolValueValuesEnum.TCP
                  ),
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testIcmpProtocolOption(self):
    self.SelectApi('alpha')
    self.Run("""
        alpha compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --ip-protocol ICMP
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  IPProtocol=(self.messages.ForwardingRule.
                              IPProtocolValueValuesEnum.ICMP),
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)
    self.SelectApi('v1')

  def testIpProtocolOptionWithIllegalProtocol(self):
    with self.AssertRaisesArgumentErrorMatches(
        "argument --ip-protocol: Invalid choice: 'TCPTCP'"):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --target-pool target-pool-1
            --ip-protocol TCPTCP
          """)

    self.CheckRequests()

  def testPortRangeOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --ports 1-1000
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  portRange='1-1000',
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testDeprecatedPortRangeOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --port-range 1-1000
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  portRange='1-1000',
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)
    self.AssertErrEquals('WARNING: The --port-range flag is deprecated. '
                         'Use equivalent --ports=1-1000 flag.\n')

  def testDescriptionOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --description hello
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  description='hello',
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testTargetInstanceOption(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-instance target-instance-1
          --target-instance-zone us-central2-a
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-a/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testTargetInstanceZoneWithoutInstanceOption(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--target-instance-zone\] unless you are '
        r'specifying \[--target-instance\].'):
      self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --target-instance-zone us-central2-a
          """)
    self.CheckRequests()

  def testWithConflictingContext(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--backend-service | --target-http-proxy | '
        '--target-https-proxy | --target-instance | --target-pool | '
        '--target-ssl-proxy | --target-tcp-proxy | --target-vpn-gateway) '
        'must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --global
          """)
    self.CheckRequests()

  def testTargetPoolUriSupport(self):
    self.Run("""
        compute forwarding-rules create {compute_uri}/projects/my-project/regions/us-central2/forwardingRules/forwarding-rule-1
          --target-pool {compute_uri}/projects/my-project/regions/us-central2/targetPools/target-pool-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testTargetInstanceUriSupport(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-instance {compute_uri}/projects/my-project/zones/us-central2-a/targetInstances/target-instance-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-a/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testTargetInstanceZoneUriSupport(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-instance target-instance-1
          --target-instance-zone {compute_uri}/projects/my-project/zones/us-central2-a
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-a/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testRegionalPrompting(self):
    self.WriteInput('3\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Region(name='us-central1'),
            self.messages.Region(name='us-central2'),
        ],

        [],
    ])
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --target-pool target-pool-1
        """)

    self.CheckRequests(
        self.regions_list_request,
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)
    self.AssertErrContains('forwarding rule')
    self.AssertErrContains('forwarding-rule-1')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')

  def testZonalPromptingForTargetInstance(self):
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='us-central2-a'),
            self.messages.Zone(name='us-central2-b'),
        ],

        [],
    ])
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --target-instance target-instance-1
          --region us-central2
        """)

    self.CheckRequests(
        self.filtered_zones_list_request,
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-b/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)
    self.AssertErrContains('target instance:')
    self.AssertErrContains('target-instance-1')
    self.AssertErrContains('us-central2-a')
    self.AssertErrContains('us-central2-b')

  def testPromptingErrorForTargetInstance(self):
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [],
    ])

    with self.AssertRaisesToolExceptionRegexp(
        'Unable to fetch a list of zones. Specifying '
        r'\[--target-instance-zone\] may fix this issue.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --target-instance target-instance-1
          """)

    self.CheckRequests(
        self.filtered_zones_list_request,
    )

  def testDefaultUsedForTargetInstanceZone(self):
    properties.VALUES.compute.zone.Set('us-central2-b')
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --target-instance target-instance-1
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-b/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleTargetVpnGateway(self):
    messages = self.messages
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-vpn-gateway target-vpn-gateway-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(self.compute_uri + '/projects/'
                          'my-project/regions/us-central2/targetVpnGateways/'
                          'target-vpn-gateway-1'),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testMutuallyExclusiveTargetInstanceWithTargetVpnGateway(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --target-instance: Exactly one of (--backend-service | '
        '--target-http-proxy | --target-https-proxy | --target-instance | '
        '--target-pool | --target-ssl-proxy | --target-tcp-proxy | '
        '--target-vpn-gateway) must be specified.'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --target-instance target-instance-1
            --ports 80
            --target-vpn-gateway target-vpn-gateway1
          """)

  def testInstanceRegionalWithPorts(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --ports 80-82,85
          --load-balancing-scheme internal
          --target-instance target-instance-1
          --target-instance-zone us-central2-a
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-a/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.INTERNAL,
                  ports=['80', '81', '82', '85']),
              project='my-project',
              region='us-central2'))],)

  def testInstanceRegionalWithPortRange(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --port-range 80-82
          --target-instance target-instance-1
          --target-instance-zone us-central2-a
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/zones/us-central2-a/'
                      'targetInstances/target-instance-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL,
                  portRange='80-82'),
              project='my-project',
              region='us-central2'))],)


class RegionalForwardingRulesCreateBackendServicesTest(test_base.BaseTest):

  def SetUp(self):
    properties.VALUES.core.check_gce_metadata.Set(False)
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testBackendServiceMutuallyExclusiveWithGlobal(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--backend-service\] for a global '
        'forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --backend-service BS1
                  --global
                  --ports 80""")

    self.CheckRequests()

  def testInternalMutuallyExclusiveWithGlobal(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify internal \[--load-balancing-scheme\] for a global '
        'forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --load-balancing-scheme internal
                  --target-http-proxy target-http-proxy-1
                  --global
                  --ports 80""")

    self.CheckRequests()

  def testExternalMutuallyExclusiveWithSubnet(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--subnet\] or \[--network\] for non-internal '
        r'\[--load-balancing-scheme\] forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --subnet subnet-abc
                  --load-balancing-scheme external
                  --backend-service BS1
                  --ports 80
                  --region alaska""")

    self.CheckRequests()

  def testExternalMutuallyExclusiveWithNetwork(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--subnet\] or \[--network\] for non-internal '
        r'\[--load-balancing-scheme\] forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --network network-abc
                  --load-balancing-scheme external
                  --backend-service BS1
                  --ports 80
                  --region alaska""")

    self.CheckRequests()

  def testInternalWithAddressAndPorts(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --address 162.222.178.83
                --ports 80-82,85
                --subnet subdefault
                --network default
                --backend-service BS1
                --region alaska
                --load-balancing-scheme internal""")

    load_balancing_scheme = (self.messages.ForwardingRule
                             .LoadBalancingSchemeValueValuesEnum.INTERNAL)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  IPAddress='162.222.178.83',
                  ports=['80', '81', '82', '85'],
                  network=('{0}/projects/my-project/global/networks/default'
                           .format(self.compute_uri)),
                  subnetwork=('{0}/projects/my-project/regions/alaska/'
                              'subnetworks/subdefault'
                              .format(self.compute_uri)),
                  loadBalancingScheme=load_balancing_scheme,
                  backendService='https://www.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),),
              project='my-project',
              region='alaska'))],)

  def testInternalBackendServiceWithPortRange(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify \[--port-range\] for a forwarding rule whose '
        r'\[--load-balancing-scheme\] is internal, please use '
        r'\[--ports\] flag instead.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --port-range 100-105
                  --load-balancing-scheme internal
                  --backend-service BS1
                  --region alaska""")

  def testInternalBackendService(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --backend-service BS1
                --region alaska""")

    load_balancing_scheme = (self.messages.ForwardingRule
                             .LoadBalancingSchemeValueValuesEnum.INTERNAL)
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  backendService='https://www.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),),
              project='my-project',
              region='alaska'))],)

  def testInternalTargetInstance(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --target-instance ti
                --region us-central2
                --target-instance-zone us-central2-b
                --ports 80""")

    load_balancing_scheme = (
        self.messages.ForwardingRule.LoadBalancingSchemeValueValuesEnum.INTERNAL
    )
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  target='https://www.googleapis.com/compute/{api}/'
                  'projects/my-project/zones/us-central2-b/'
                  'targetInstances/'
                  'ti'.format(api=self.resource_api),
                  ports=['80'],),
              project='my-project',
              region='us-central2'))],)

  def testInternalTargetPool(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --target-pool TP1
                --region alaska""")

    load_balancing_scheme = (self.messages.ForwardingRule
                             .LoadBalancingSchemeValueValuesEnum.INTERNAL)
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  target='https://www.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'targetPools/'
                  'TP1'.format(api=self.resource_api),),
              project='my-project',
              region='alaska'))],)

  def testInternalTargetHttpProxy(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'You cannot specify internal \[--load-balancing-scheme\] '
        'for a global forwarding rule.'):
      self.Run("""compute forwarding-rules create forwarding-rule-1
                  --load-balancing-scheme internal
                  --target-http-proxy TP1
                  --ports 80
                  --global""")

  def testExternalBackendService(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --backend-service BS1
                --region alaska""")

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  backendService='https://www.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='alaska'))],)

  def testBackendServiceWithServiceLabel(self):
    self.Run("""compute forwarding-rules create forwarding-rule-1
                --load-balancing-scheme internal
                --backend-service BS1
                --service-label label1
               --region alaska""")

    load_balancing_scheme = (self.messages.ForwardingRule
                             .LoadBalancingSchemeValueValuesEnum.INTERNAL)
    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  loadBalancingScheme=load_balancing_scheme,
                  backendService='https://www.googleapis.com/compute/{api}/'
                  'projects/my-project/regions/alaska/'
                  'backendServices/'
                  'BS1'.format(api=self.resource_api),
                  serviceLabel='label1',),
              project='my-project',
              region='alaska'))],)


class ForwardingRuleCreateWithNetworkTierAlphaTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testSimpleCaseWithPremiumNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --network-tier PREMIUM
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule.
                               NetworkTierValueValuesEnum.PREMIUM),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithSelectNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --network-tier select
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule.
                               NetworkTierValueValuesEnum.SELECT),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetPoolAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule.
                               NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetHttpProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-http-proxy target-http-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule.
                               NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetHttpsProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-https-proxy target-https-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpsProxies/target-https-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule.
                               NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetSslProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-ssl-proxy target-ssl-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetSslProxies/target-ssl-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule.
                               NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithTargetTcpProxyAndStandardNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-tcp-proxy target-tcp-proxy-1
          --network-tier standard
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetTcpProxies/target-tcp-proxy-1').format(
                              compute_uri=self.compute_uri),
                  networkTier=(self.messages.ForwardingRule.
                               NetworkTierValueValuesEnum.STANDARD),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithMissingNetworkTier(self):
    self.Run("""
        compute forwarding-rules create forwarding-rule-1
          --region us-central2
          --target-pool target-pool-1
        """)

    self.CheckRequests(
        [(self.compute.forwardingRules, 'Insert',
          self.messages.ComputeForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=(
                      '{compute_uri}/projects/my-project/regions/us-central2/'
                      'targetPools/target-pool-1').format(
                          compute_uri=self.compute_uri),
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project',
              region='us-central2'))],)

  def testSimpleCaseWithInvalidNetworkTier(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Invalid value for \[--network-tier\]: Invalid network tier '
        r'\[INVALID-TIER\]'):
      self.Run("""
          compute forwarding-rules create forwarding-rule-1
            --region us-central2
            --network-tier invalid-tier
            --target-pool target-pool-1
          """)


class CreateWithIPVersionApiTest(test_base.BaseTest):

  def RunCreate(self, command):
    super(self.__class__,
          self).Run('compute forwarding-rules create ' + command)

  # When no --ip-version specified, default value of IPV4 should be specified.
  def testDefault(self):
    messages = self.messages

    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --target-http-proxy target-http-proxy-1
          --ports 8080
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testIPv4(self):
    messages = self.messages

    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --ip-version ipv4
          --target-http-proxy target-http-proxy-1
          --ports 8080
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV4
                  ),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testIPv6(self):
    messages = self.messages

    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --ip-version ipV6
          --target-http-proxy target-http-proxy-1
          --ports 8080
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  ipVersion=(
                      messages.ForwardingRule.IpVersionValueValuesEnum.IPV6
                  ),
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

  def testWithAddressFlag(self):
    self.RunCreate("""
        forwarding-rule-1
          --description my-forwarding-rule
          --global
          --target-http-proxy target-http-proxy-1
          --ports 8080
          --address 23.251.146.189
        """)

    self.CheckRequests(
        [(self.compute.globalForwardingRules, 'Insert',
          self.messages.ComputeGlobalForwardingRulesInsertRequest(
              forwardingRule=self.messages.ForwardingRule(
                  name='forwarding-rule-1',
                  target=('{compute_uri}/projects/my-project/global/'
                          'targetHttpProxies/target-http-proxy-1').format(
                              compute_uri=self.compute_uri),
                  description='my-forwarding-rule',
                  IPAddress='23.251.146.189',
                  portRange='8080',
                  loadBalancingScheme=self.messages.ForwardingRule.
                  LoadBalancingSchemeValueValuesEnum.EXTERNAL),
              project='my-project'))],)

if __name__ == '__main__':
  test_case.main()