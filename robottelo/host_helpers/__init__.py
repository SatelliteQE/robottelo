from robottelo.host_helpers.capsule_mixins import (
    CapsuleInfo,
    EnablePluginsCapsule,
    InstallationVerification,
)
from robottelo.host_helpers.contenthost_mixins import (
    HostInfo,
    SystemFacts,
    VersionedContent,
)
from robottelo.host_helpers.satellite_mixins import (
    ContentInfo,
    DisconnectedInstall,
    EnablePluginsSatellite,
    Factories,
    IoPSetup,
    ProvisioningSetup,
    SystemInfo,
)


class ContentHostMixins(HostInfo, SystemFacts, VersionedContent):
    pass


class CapsuleMixins(CapsuleInfo, EnablePluginsCapsule, InstallationVerification):
    pass


class SatelliteMixins(
    ContentInfo,
    DisconnectedInstall,
    Factories,
    SystemInfo,
    EnablePluginsSatellite,
    ProvisioningSetup,
    IoPSetup,
):
    pass
