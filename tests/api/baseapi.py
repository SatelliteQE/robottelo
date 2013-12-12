
def featuring(match,test):
    if type(match) != type(test):
        return False
    if type(match) is dict:
        return all([k in test and featuring(v,test[k]) for (k,v) in match.items()])
    if type(match) is list:
        return all([any([featuring(m,t) for t in test]) for m in match])
    return match == test

def assertFeaturing(match,test):
    if type(match) != type(test):
        raise AssertionError("Type of {0} is {1} and {2} is {3}".format(match,type(match),test,type(test)))
    elif type(match) is dict:
        for k in match:
            if not k in test:
                raise AssertionError("{0} lacks key {1}".format(test,k))
        for k in match:
            assertFeaturing(match[k],test[k])
    elif type(match) is list:
        for m in match:
            exists = any([featuring(m,t) for t in test])
            if not exists:
                raise AssertionError("{0} lacks {1}".format(test,m))
    else:
        assert match == test

