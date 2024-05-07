"""Docker related hammer commands"""

from robottelo.cli.base import Base


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
        return super().info(options)

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
        return super().list(options, per_page)


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
        return super().info(options)

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
        return super().list(options, per_page)


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
    manifest = DockerManifest
    tag = DockerTag
