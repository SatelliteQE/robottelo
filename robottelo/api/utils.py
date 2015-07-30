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
    prd_id = entities.Product(name=product, organization=org_id).search()[0].id
    reposet = entities.RepositorySet(name=reposet, product=prd_id).search()[0]
    payload = {}
    if basearch is not None:
        payload['basearch'] = basearch
    if releasever is not None:
        payload['releasever'] = releasever
    reposet.enable(payload)
    return entities.Repository(name=repo).search(
        query={'organization_id': org_id})[0].id
