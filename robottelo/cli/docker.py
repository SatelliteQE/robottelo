# -*- encoding: utf-8 -*-

"""Docker related hammer commands"""

from robottelo.cli.base import Base


class DockerContainer(Base):
    """Manipulates Docker containers

    Usage::

        hammer docker container [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters::

        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands::

        create                        Create a container
        delete                        Delete a container
        info                          Show a container
        list                          List all containers
        logs                          Show container logs
        start                         Power a container on
        status                        Run power operation on a container
        stop                          Power a container off

    """
    command_base = 'docker container'

    @classmethod
    def create(cls, options=None):
        """Creates a docker container

        Usage::

            hammer docker container create [OPTIONS]

        Options::

            --attach-stderr ATTACH_STDERR             One of true/false,
                                                      yes/no, 1/0.
            --attach-stdin ATTACH_STDIN               One of true/false,
                                                      yes/no, 1/0.
            --attach-stdout ATTACH_STDOUT             One of true/false,
                                                      yes/no, 1/0.
            --capsule CAPSULE_NAME                    Name to search by
            --capsule-id CAPSULE_ID                   Id of the capsule
            --command COMMAND
            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --cpu-sets CPU_SETS
            --cpu-shares CPU_SHARES
            --entrypoint ENTRYPOINT
            --location-ids LOCATION_IDS               REPLACE locations with
                                                      given ids. Comma
                                                      separated list of values.
            --locations LOCATION_NAMES                Comma separated list of
                                                      values.
            --memory MEMORY
            --name NAME
            --organization-ids ORGANIZATION_IDS       REPLACE organizations
                                                      with given ids.  Comma
                                                      separated list of values.
            --organizations ORGANIZATION_NAMES        Comma separated list of
                                                      values.
            --registry-id REGISTRY_ID
            --repository-name REPOSITORY_NAME         Name of the repository to
                                                      use to create the
                                                      container. e.g. centos
            --tag TAG                                 Tag to use to create the
                                                      container. e.g. latest
            --tty TTY                                 One of true/false,
                                                      yes/no, 1/0.

        """
        return super(DockerContainer, cls).create(options)

    @classmethod
    def delete(cls, options=None):
        """Deletes a docker container

        Usage::

            hammer docker container delete [OPTIONS]

        Options::

            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --id ID
            --name NAME                               Name to search by

        """
        return super(DockerContainer, cls).delete(options)

    @classmethod
    def info(cls, options=None):
        """Gets information about a docker container

        Usage::

            hammer docker container info [OPTIONS]

        Options::

            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --id ID
            --name NAME                               Name to search by

        """
        return super(DockerContainer, cls).info(options)

    @classmethod
    def list(cls, options=None, per_page=True):
        """Lists docker containers

        Usage::

            hammer docker container list [OPTIONS]

        Options::

            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --page PAGE                               paginate results
            --per-page PER_PAGE                       number of entries per
                                                      request

        """
        return super(DockerContainer, cls).list(options)

    @classmethod
    def logs(cls, options=None):
        """Reads container logs

        Usage::

            hammer docker container logs [OPTIONS]

        Options::

            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --id ID
            --name NAME                               Name to search by
            --stderr STDERR                           One of true/false,
                                                      yes/no, 1/0.
            --stdout STDOUT                           One of true/false,
                                                      yes/no, 1/0.
            --tail TAIL                               Number of lines to tail.
                                                      Default: 100

        """
        cls.command_sub = 'logs'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def start(cls, options=None):
        """Starts a docker container

        Usage::

            hammer docker container start [OPTIONS]

        Options::

            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --id ID
            --name NAME                               Name to search by

        """
        cls.command_sub = 'start'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def status(cls, options=None):
        """Gets the running status of a docker container

        Usage::

            hammer docker container status [OPTIONS]

        Options::

            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --id ID
            --name NAME                               Name to search by

        """
        cls.command_sub = 'status'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def stop(cls, options=None):
        """Stops a docker container

        Usage::

            hammer docker container stop [OPTIONS]

        Options::

            --compute-resource COMPUTE_RESOURCE_NAME  Compute resource name
            --compute-resource-id COMPUTE_RESOURCE_ID
            --id ID
            --name NAME                               Name to search by

        """
        cls.command_sub = 'stop'
        return cls.execute(cls._construct_command(options))


class DockerManifest(Base):
    """Manipulates Docker manifests

    Usage::

        hammer docker manifest [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters::

        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands::

        info                          Show a docker manifest
        list                          List docker_manifests

    """
    command_base = 'docker manifest'

    @classmethod
    def info(cls, options=None):
        """Gets information about docker manifests

        Usage::

            hammer docker manifest info [OPTIONS]

        Options::

            --id ID                       a docker manifest identifier
            --name NAME                   Name to search by
            --repository REPOSITORY_NAME  Repository name to search by
            --repository-id REPOSITORY_ID repository ID

        """
        return super(DockerManifest, cls).info(options)

    @classmethod
    def list(cls, options=None, per_page=True):
        """List docker manifests

        Usage::

            hammer docker manifest list [OPTIONS]

        Options::

         --by BY                                             Field to sort the
                                                             results on
         --content-view CONTENT_VIEW_NAME                    Content view name
         --content-view-filter CONTENT_VIEW_FILTER_NAME      Name to search by
         --content-view-filter-id CONTENT_VIEW_FILTER_ID     filter identifier
         --content-view-id CONTENT_VIEW_ID                   content view
                                                             numeric identifier
         --content-view-version CONTENT_VIEW_VERSION_VERSION Content view
                                                             version number
         --content-view-version-id CONTENT_VIEW_VERSION_ID   Content view
                                                             version identifier
         --full-results FULL_RESULTS                         Whether or not to
                                                             show all results
                                                             One of true/false,
                                                             yes/no, 1/0.
         --ids IDS                                           ids to filter
                                                             content by
                                                             Comma separated
                                                             list of values.
         --lifecycle-environment LIFECYCLE_ENVIRONMENT_NAME  Name to search by
         --lifecycle-environment-id LIFECYCLE_ENVIRONMENT_ID
         --order ORDER                                       Sort field and
                                                             order, eg.
                                                             "name DESC"
         --organization ORGANIZATION_NAME                    Organization name
                                                             to search by
         --organization-id ORGANIZATION_ID                   organization ID
         --organization-label ORGANIZATION_LABEL             Organization label
                                                             to search by
         --page PAGE                                         Page number,
                                                             starting at 1
         --per-page PER_PAGE                                 Number of results
                                                             per page to return
         --product PRODUCT_NAME                              Product name to
                                                             search by
         --product-id PRODUCT_ID                             product numeric
                                                             identifier
         --repository REPOSITORY_NAME                        Repository name to
                                                             search by
         --repository-id REPOSITORY_ID                       repository ID
         --search SEARCH                                     Search string

        """
        return super(DockerManifest, cls).list(options, per_page)


class DockerRegistry(Base):
    """Manipulates Docker registries

    Usage::

        hammer docker registry [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters::

        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands::

        create                        Create a docker registry
        delete                        Delete a docker registry
        info                          Show a docker registry
        list                          List all docker registries
        update                        Update a docker registry

    """
    command_base = 'docker registry'

    @classmethod
    def create(cls, options=None):
        """Creates a docker registry

        Usage::

            hammer docker registry create [OPTIONS]

        Options::

            --description DESCRIPTION
            --name NAME
            --password PASSWORD
            --url URL
            --username USERNAME

        """
        return super(DockerRegistry, cls).create(options)

    @classmethod
    def delete(cls, options=None):
        """Deletes a docker registry

        Usage::

            hammer docker registry delete [OPTIONS]

        Options::

            --id ID
            --name NAME                               Name to search by

        """
        return super(DockerRegistry, cls).delete(options)

    @classmethod
    def info(cls, options=None):
        """Gets information about docker registry

        Usage::

            hammer docker registry info [OPTIONS]

        Options::

            --id ID
            --name NAME                   Name to search by

        """
        return super(DockerRegistry, cls).info(options)

    @classmethod
    def list(cls, options=None, per_page=True):
        """List docker registries

        Usage::

            hammer docker registry list [OPTIONS]

        Options::

            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --search SEARCH               filter results

        """
        return super(DockerRegistry, cls).list(options, per_page)

    @classmethod
    def update(cls, options=None):
        """Updates a docker registry

        Usage::

            hammer docker registry update [OPTIONS]

        Options::

            --description DESCRIPTION
            --id ID
            --name NAME                               Name to search by
            --new-name NEW_NAME
            --password PASSWORD
            --url URL
            --username USERNAME

        """
        return super(DockerRegistry, cls).update(options)


class DockerTag(Base):
    """Manipulates Docker tags

    Usage::

        hammer docker tag [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters::

        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands::

        info                          Show a docker tag
        list                          List docker_tags

    """
    command_base = 'docker tag'

    @classmethod
    def info(cls, options=None):
        """Gets information about docker tags

        Usage::

            hammer docker tag info [OPTIONS]

        Options::

            --id ID                       a docker tag identifier
            --name NAME                   Name to search by
            --repository REPOSITORY_NAME  Repository name to search by
            --repository-id REPOSITORY_ID repository ID

        """
        return super(DockerTag, cls).info(options)

    @classmethod
    def list(cls, options=None, per_page=True):
        """List docker tags

        Usage::

            hammer docker tag list [OPTIONS]

        Options::

            --content-view CONTENT_VIEW_NAME                    Content view
                                                                name
            --content-view-filter CONTENT_VIEW_FILTER_NAME      Name to search
                                                                by
            --content-view-filter-id CONTENT_VIEW_FILTER_ID     filter
                                                                identifier
            --content-view-id CONTENT_VIEW_ID                   content view
                                                                numeric
                                                                identifier
            --content-view-version CONTENT_VIEW_VERSION_VERSION Content view
                                                                version number
            --content-view-version-id CONTENT_VIEW_VERSION_ID   Content view
                                                                version
                                                                identifier
            --environment ENVIRONMENT_NAME                      Name to search
                                                                by
            --environment-id ENVIRONMENT_ID
            --organization ORGANIZATION_NAME                    Organization
                                                                name to search
                                                                by
            --organization-id ORGANIZATION_ID                   organization ID
            --organization-label ORGANIZATION_LABEL             Organization
                                                                label to search
                                                                by
            --product PRODUCT_NAME                              Product name to
                                                                search by
            --product-id PRODUCT_ID                             product numeric
                                                                identifier
            --repository REPOSITORY_NAME                        Repository name
                                                                to search by
            --repository-id REPOSITORY_ID                       repository ID

        """
        return super(DockerTag, cls).list(options, per_page)


class Docker(Base):
    """Manipulates Docker manifests and tags

    Usage::

        hammer docker [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters::

        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands::

        container                     Manage docker containers
        manifest                      Manage docker manifests
        registry                      Manage docker registries
        tag                           Manage docker tags

    """
    command_base = 'docker'

    # Shortcuts to docker subcommands. Instead of importing each subcommand
    # class, import the Docker class and use it like this: Docker.tag.list()
    container = DockerContainer
    manifest = DockerManifest
    registry = DockerRegistry
    tag = DockerTag
