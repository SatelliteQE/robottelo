from robottelo.host_helpers.capsule_mixins import CapsuleInfo
from robottelo.host_helpers.capsule_mixins import EnablePluginsCapsule
from robottelo.host_helpers.contenthost_mixins import HostInfo
from robottelo.host_helpers.contenthost_mixins import SystemFacts
from robottelo.host_helpers.contenthost_mixins import VersionedContent
from robottelo.host_helpers.satellite_mixins import ContentInfo
from robottelo.host_helpers.satellite_mixins import EnablePluginsSatellite
from robottelo.host_helpers.satellite_mixins import Factories
from robottelo.host_helpers.satellite_mixins import SystemInfo


class ContentHostMixins(HostInfo, SystemFacts, VersionedContent):
    pass


class CapsuleMixins(CapsuleInfo, EnablePluginsCapsule):
    pass


class SatelliteMixins(ContentInfo, Factories, SystemInfo, EnablePluginsSatellite):
    pass
