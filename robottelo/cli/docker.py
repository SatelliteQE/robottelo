# -*- encoding: utf-8 -*-

"""Docker related hammer commands"""

from robottelo.cli.base import Base


class DockerImage(Base):
    """Manipulates Docker images

    Usage::

        hammer docker image [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters::

        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands::

        info                          Show a docker image
        list                          List docker_images

    """
    command_base = 'docker image'

    @classmethod
    def info(cls, options=None):
        """Gets information about docker images

        Usage::

            hammer docker image info [OPTIONS]

        Options::

            --id ID                       a docker image identifier
            --name NAME                   Name to search by
            --repository REPOSITORY_NAME  Repository name to search by
            --repository-id REPOSITORY_ID repository ID

        """
        return super(DockerImage, cls).info(options)

    @classmethod
    def list(cls, options=None, per_page=True):
        """List docker images

        Usage::

            hammer docker image list [OPTIONS]

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
        return super(DockerImage, cls).list(options, per_page)


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
    """Manipulates Docker images and tags

    Usage::

        hammer docker [OPTIONS] SUBCOMMAND [ARG] ...

    Parameters::

        SUBCOMMAND                    subcommand
        [ARG] ...                     subcommand arguments

    Subcommands::

        image                         Manage docker images
        tag                           Manage docker tags

    """
    command_base = 'docker'

    # Shortcuts to docker subcommands. Instead of importing each subcommand
    # class, import the Docker class and use it like this: Docker.image.list()
    image = DockerImage
    tag = DockerTag
