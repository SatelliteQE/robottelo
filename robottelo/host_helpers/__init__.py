from robottelo.host_helpers.capsule_mixins import CapsuleInfo, EnablePluginsCapsule
from robottelo.host_helpers.contenthost_mixins import (
    HostInfo,
    SystemFacts,
    VersionedContent,
)
from robottelo.host_helpers.satellite_mixins import (
    ContentInfo,
    EnablePluginsSatellite,
    Factories,
    ProvisioningSetup,
    SystemInfo,
)


class ContentHostMixins(HostInfo, SystemFacts, VersionedContent):
    pass


class CapsuleMixins(CapsuleInfo, EnablePluginsCapsule):
    pass


class SatelliteMixins(
    ContentInfo, Factories, SystemInfo, EnablePluginsSatellite, ProvisioningSetup
):
    pass
