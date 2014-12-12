---
layout: post
title: "Automatic Code Profiling"
date: 2014-12-12 17:08:00
categories: update
---

[Pull request #1766](https://github.com/SatelliteQE/robottelo/pull/1766) added
automatic code profiling to Robottelo. As a result of this change, profiling
data is automatically collected whenever one of the following commands is run:

* `make test-robottelo`
* `make test-foreman-api`
* `make test-foreman-api-threaded`
* `make test-foreman-cli`
* `make test-foreman-cli-threaded`
* `make test-foreman-ui`
* `make test-foreman-smoke`

This profiling data is stored in "pstats" files. A file named
`test-robottelo.pstats` is created when `make test-robottelo` is executed, and
so on for the other make targets. This profiling data is collected by the
cProfile Python module, which is a C extension available in the [Python
2](https://docs.python.org/2/library/profile.html) and [Python
3](https://docs.python.org/3/library/profile.html) standard libraries.

This information can be manipulated in a variety of ways. For example,
"[RunSnakeRun](http://www.vrplumber.com/programming/runsnakerun/) is a small
GUI utility that allows you to view (Python) cProfile or Profile profiler
dumps." This data can be converted to a format that KCacheGrind (or
QCacheGrind) understands with the pyprof2calltree utility.

An especially easy method of visualizing these "pstats" files is with GProf2Dot
and Graphviz. GProf2Dot converts data dumps to
[DOT](https://en.wikipedia.org/wiki/DOT_%28graph_description_language%29), and
Graphviz converts DOT text to an image. For example:

    gprof2dot --format pstats test-robottelo.pstats \
    | dot -Tsvg -o test-robottelo.svg

The above will probably produce a very verbose graph, as any function that
consumes more than 0.5% of the total program runtime is included. Here's an
example that produces a PNG image that only includes functions that consume
more than 5% of the total program runtime:

    gprof2dot --format pstats --node-thres 5 test-robottelo.pstats \
    | dot -Tpng -o test-robottelo.png

And that's it! For an example of what the results look like, see [this
image](http://i.imgur.com/5ohMVaS.png) (beware, it's large), and for help
interpreting the graph, see the
[Output](https://code.google.com/p/jrfonseca/wiki/Gprof2Dot#Output) section of
the Gprof2Dot wiki page.

Pro tip: An arbitrary Python program can be profiled with a command like this:

    python -m cProfile -o foo.pstats foo.py

Pro tip 2: pstats files contain pickled Python data. As a result, they can only
be unpickled by a Python version that is identical (or, if you're lucky,
similar) to the Python version that produced the file. If you've produced a
pstats file with a Python 3 program, make sure to manipulate it with the Python
3 version of GProf2Dot or pyprof2calltree, and so on.
