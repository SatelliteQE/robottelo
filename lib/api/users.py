from lib.api.base import get, put, post, delete

def raw_query(opts = None, **kwargs):
    """Query users with api.

    :url http://people.redhat.com/~dcleal/apiv2/apidoc/users/index.html

    """

    return get(path="/api/users", json=opts, **kwargs)

def raw_read(uid, **kwargs):
    """Show an user with api.

    :url http://people.redhat.com/~dcleal/apiv2/apidoc/users/show.html

    """
    return get(path="/api/users/{0}".format(uid), **kwargs)

def raw_create(opts, **kwargs):
    """Create an user with api.

    :url http://people.redhat.com/~dcleal/apiv2/apidoc/users/create.html

    """
    return post(path="/api/users", json=opts, **kwargs)

def raw_remove(uid, **kwargs):
    """Delete an user with api.

    :url http://people.redhat.com/~dcleal/apiv2/apidoc/users/destroy.html

    """
    return delete(path="/api/users/{0}".format(uid), **kwargs)

def raw_update(uid, opts, **kwargs):
    """Update an user with api.

    :url http://people.redhat.com/~dcleal/apiv2/apidoc/users/update.html

    """
    return put(path="/api/users/{0}".format(uid), json=opts, **kwargs)
