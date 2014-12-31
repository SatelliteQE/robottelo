---
layout: post
title: "What's New"
date: 2014-10-09 16:13:58
categories: update
author: Og Maciel
---

First off, we're starting a brand, spanking new blog to keep anyone
using **Robottelo** up to date with what is happening as well as to
provide information about new features, code standards and best
practices, and even examples of how to use certain features of the
framework itself.

So here are the highlights for this week:

* Please make sure to update your [FauxFactory][faux] and
 [Requests][request] packages.

A newer version of **FauxFactory** is required to support the
generation of ``netmask`` values:

{% highlight python %}
from fauxfactory import gen_netmask

gen_netmask()
u'255.255.255.252'

gen_netmask(min_cidr=4)
u'255.255.255.252'

gen_netmask(min_cidr=4, max_cidr=10)
u'252.0.0.0'
{% endhighlight %}

A new version of **Requests** will help you avoid seeing errors such
as this:

{% highlight bash %}
TypeError: post() takes at most 2 arguments (6 given)
{% endhighlight %}

* Make sure to check our new
[Code Standards](http://robottelo.readthedocs.org/en/latest/code_standards.html)
and instructions for
[committing](http://robottelo.readthedocs.org/en/latest/committing.html)
and
[reviewing](http://robottelo.readthedocs.org/en/latest/reviewing_PRs.html)
pull requests!!!

... and that is about it for now.

[faux]: http://fauxfactory.readthedocs.org/en/latest/
[request]: http://docs.python-requests.org/en/latest/
