========
SETTINGS
========

`server`:
---------
* `hostname` - required.
* `scheme` - optional.
  - Suggested values are "http" and "https". (default: https)
* `port` - optional.

`robottelo`:
------------
* `project` - Enter only 'sat' for Satellite and 'sam' for SAM.
* `upstream` - Update upstream=0 for downstream run.
* `screenshots.base_path` - The directory where screenshots will be saved. Note
  that content under /tmp may be deleted after a reboot.
* `virtual_display` - controls if PyVirtualDisplay should be used to run UI
  tests.  When setting this to 1, make sure to install required dependencies
* `window_manager_command` - If virtual_display=1 and window_manager_command is
  set, the window manager command will be run before opening any browser window

`tests`:
-------- 
The values in this section is used to run/skip related tests

`manifest`:
-----------
For testing with fake manifests, zipfile containing valid manifest is required,
as well as key/cert pair. All of these settings are urls.

`clients`:
----------
* `provisioning_server`: Provisioning server hostname where the clients will be
  created
* `image_dir`: Path on the provisioning server where the virtual images will be
  stored. If not specified in the configuration, the default libvirt path will
  be used "/var/lib/libvirt/images/". Make sure that the path exists on the
  provisioning server.
* `rhel6_repo` / `rhel7_repo`: Provide link to rhel6/7 repo here, as puppet rpm
  would require packages from RHEL 6/7 repo and syncing the entire repo on the
  fly would take longer for tests to run. Specify the repo link to an
  internal repo for tests to execute properly.

`docker`:
---------
* `exernal_url`: External docker URL in the format http[s]://<server>:<port>.
  The {server_hostname} variable can be used and will be replaced by
  main.server.hostname value. An external docker is a docker daemon accessed
  using http, for testing purposes accessing localhost via http will be the
  same as accessing an external instance. Make sure that the target daemon can
  be accessed via http, in other words, the daemon is initialized with 
  `--host tcp://0.0.0.0:<port>`.

`insights`:
-----------
Provide link to el6/el7 repo to fetch the redhat-access-insights client rpm
(if required)

`transitions`:
--------------
* `export_tar.url`: URL of the exported data archive (typically a .tgz
  containing a bunch of CSV files together with repo data)

`performance`:
-------------- 
* `test.foreman.perf`: Control whether or not to time on hammer commands in
  robottelo/cli/base.py.  Default set to be 0, i.e. no timing of performance is
  measured and thus no interference to original robottelo tests.

  Following entries are used for preparation of performance tests after a
  fresh install. They will be used by
  `test/foreman/performance/test_standard_prep.py`, which supports::

    1. downloading manifest,
    2. uploading manifest to subscription,
    3. updating Red Hat CDN URL,
    4. enabling key repositories: rhel6-rpms, rhel7-rpms,
       rhel6-kickstart-rpms, rhel7-kickstart-rpms, rhel6-optional-rpms,
       rhel7-optional-rpms, rhel6-optional-source-rpms,
       rhel7-optional-source-rpms, rhel6-optional-debug-rpms,
       r7-optional-debug-rpms

  * `test.cdn.address`: Note that this preparation step is not required as long
    as satellite server is already configured.
  * `test.virtual_machines_list`: A list of VM IP addresses or hostnames. Each
    system should already be provisioned. They will be used in concurrent
    system subscription tests.

  Savepoint utility to restore the database. For example, after conducting
  5,000 concurrent subscription by activation-key using 10 clients, in order to
  start next 5k test case of subscription by register and attach, the
  performance test would restore the database back to the state where there's
  no client registered. All performance test cases would use this setting.

  * `test.savepoint1_fresh_install`: User should create savepoint-1 immediately
    after a fresh installation of Satellite.
  * `test.savepoint2_enabled_repos`: User should create savepoint-2 after
    enabling repositories, but before any system subscription or repository
    synchronization.
  * `csv.num_buckets`: Parameter for number of buckets to be sliced by csv
    generating function Class `ConcurrentTestCase` and its subclasses use this
    setting when computing statistics of each performance test case, grouped in
    buckets.
  * `test.target_repos`: Target repository names to be synchronized by Pulp.
    Target repositories are subset of all enabled repositories. Real repository
    names should be referred by `h repository list --organization-id=1`
  * `test.num_sync`: Number of times to repeat synchronization on each
    repository
  * `test.sync_type`: Parameter for deciding whether conduct initial sync or 
    resync. 'resync' denotes resync; 'sync' denotes initial sync