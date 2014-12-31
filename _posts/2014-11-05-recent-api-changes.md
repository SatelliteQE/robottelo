---
layout: post
title: "Recent API Changes"
date: 2014-11-05 15:12:15
categories: update
author: Jeremy Audet
---

Robottelo's API abstraction layer received a major update in [pull request
1631](https://github.com/SatelliteQE/robottelo/pull/1631). The pull request
changes how client code can go about creating an entity via the API. Any client
code that calls the `create` method (e.g. `Organization().create()`) or one of
its cousins will eventually be affected.

PR 1631 drops the `EntityFactoryMixin` class. It provided the following
methods:

* `attributes`
* `build`
* `create`
* `_factory_data`
* `_factory_path`

PR 1631 also adds the `EntityCreateMixin` class. It provides the following
methods:

* `create`
* `create_json`
* `create_raw`
* `create_missing`
* `create_payload`

These are completely different! Thankfully, PR 1631 includes fixes for breaking
changes, and the `create` method in the new mixin is backwards-compatible with
the `create` method from the old mixin. Given this, why should you care about
the change? You should care because the backwards compatibility will eventually
go away.

The `create` method currently returns a dictionary of attributes about the
just-created method. In the future, the `create` method will instead return an
object whose attributes have been populated. To illustrate the change and why
it's useful, here's some old code:

    org_id = Organization().create()['id']
    Organization(id=org_id).subscriptions()

And here's the equivalent upcoming code:

    Organization().create().subscriptions()

Any client code that depends on receiving a dictionary of attributes back
should be changed to call the `create_json` method instead. To illustrate,
here's the same code as above, but using the `create_json` method:

    org_id = Organization().create_json()['id']
    Organization(id=org_id).subscriptions()

For full details on the changes, please see [this blog
post](http://www.ichimonji10.name/blog/4/).
