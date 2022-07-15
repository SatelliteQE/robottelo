from robottelo.host_helpers.capsule_mixins import CapsuleInfo
from robottelo.host_helpers.contenthost_mixins import SystemFacts
from robottelo.host_helpers.contenthost_mixins import VersionedContent
from robottelo.host_helpers.host_mixins import IOHelpers
from robottelo.host_helpers.satellite_mixins import ContentInfo
from robottelo.host_helpers.satellite_mixins import Factories


class ContentHostMixins(SystemFacts, VersionedContent):
    pass


class CapsuleMixins(CapsuleInfo):
    pass


class SatelliteMixins(ContentInfo, Factories):
    pass


class HostMixins(IOHelpers):
    pass
