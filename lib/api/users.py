import lib.api.base

def query(opts = None,api = None):
    api = api or lib.api.base.ApiRequest()
    if opts:
        api.content(opts)
    return api.path("/api/users").get().submit()

def read(id,api = None):
    api = api or lib.api.base.ApiRequest()
    return api.path("/api/users/{0}".format(id)).get().submit()

def create(opts, api = None):
    api = api or lib.api.base.ApiRequest()
    api.content(opts)
    return api.path("/api/users").post().submit()

def remove(id,api = None):
    api = api or lib.api.base.ApiRequest()
    return api.path("/api/users/{0}".format(id)).delete().submit()

def update(id,opts,api = None):
    api = api or lib.api.base.ApiRequest()
    api.content(opts)
    return api.path("/api/users/{0}".format(id)).put().submit()
