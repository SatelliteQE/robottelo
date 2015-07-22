"""Module containing convenience functions for working with the API."""
from nailgun import entities


def enable_rhrepo_and_fetchid(basearch, org_id, product, repo,
                              reposet, releasever):
    """Enable a RedHat Repository and fetches it's Id.

    :param str org_id: The organization Id.
    :param str product: The product name in which repository exists.
    :param str reposet: The reposet name in which repository exists.
    :param str repo: The repository name who's Id is to be fetched.
    :param str basearch: The architecture of the repository.
    :param str releasever: The releasever of the repository.
    :return: Returns the repository Id.
    :rtype: str

    """
    prd_id = entities.Product().fetch_rhproduct_id(name=product, org_id=org_id)
    reposet_id = entities.Product(id=prd_id).fetch_reposet_id(name=reposet)
    entities.Product(id=prd_id).enable_rhrepo(
        base_arch=basearch,
        release_ver=releasever,
        reposet_id=reposet_id,
    )
    return entities.Repository().fetch_repoid(name=repo, org_id=org_id)
