# Helpers Best Practices - Guide
Welcome to the **Helpers Best Practices Guide**! This comprehensive guide is designed to assist contributors in locating existing helpers and adding new ones to the right place, making them accessible through appropriate objects, fixtures, and importables. By following these best practices, we aim to improve the organization of helpers within the framework, enhance the discovery of helpful tools, and minimize the duplication of helper definitions and maintenance efforts.

## Introduction
The scattered and misaligned placement of helpers within the framework can lead to challenges in discovering and managing helpers, resulting in duplicated definitions and increased maintenance overhead. To address these issues, we have outlined best practices for defining helper functions, modules, classes and fixtures. These guidelines will help you make informed decisions about where to place different types of helpers within the framework.


## General Practices
Here are some general best practices for helper management:
- **Prefer API Calls**: When creating test setups, prioritize using API calls (nailgun methods) over UI and CLI interactions, as they tend to be faster and more efficient, unless there is a specific need for specific endpoint based setups. UI setups should be the last resort.
- **Utilize `target_sat` Fixtures**: Ensure that all tests make use of target satellite fixtures to access a wide range of helper methods provided by the satellite object.
- **Non-Reusable helpers**: If helper/fixture is not reusable, keep them closer to test in test module itself.
- **No one liner functions**: If the helper function is just a one-liner, It's recommended to directly replace the function code where it's used.

## Python Packages and Modules:

### pytest_fixtures

In the `pytest_fixtures` Python package, we provide globally accessible fixtures for use in all tests and fixtures. These fixtures are cached by scopes, making them highly reusable without the need for reimplementation. There are two types of fixtures within this package:

#### Components
- Component fixtures serve as setup and teardown utilities for component tests.
- Each individual fixture module in this package contains and represents fixtures for specific components.

#### Core
- Core fixtures are framework-level fixtures that serve as setup and teardown for component tests.
- Several special fixture modules deserve mention here:
    - `broker.py`: Contains all the `target_sat` fixtures, scoped by usage, which should be used in every functional test in `robottelo`. These fixtures return the same satellite instance for all scoped fixtures, provided that the calling test does not have a destructive marker. For tests with destructive markers, they return a new satellite instance from an image.
    - `contenthosts.py`: Houses all content host creation fixtures. All fixture markers for content hosts should be added here since the `fixture_markers` pytest plugin operates on these fixtures, adding markers and user properties to tests that use them.
    - `sat_cap_factory.py`: Contains fixtures that create satellites/capsules from scratch without using the xDist satellite. These fixtures should be placed here, as the `factory_collection` pytest plugin operates on them, adding markers to tests that use these fixtures.
    - `xdist.py`: Includes the xDist distribution session-scoped fixture, which distributes and generates satellites for running Robottelo tests. The behavior of xDist is based on the `xdist_behavior` set in the `server.yaml` configuration file.

### Robottelo

#### host_helpers
- `api_factory.py`
  - This module contains the `APIFactory` class. Helpers within this class facilitate integrated operations between components of the satellite object using satellite API calls.
  - Since we favor API test setups, this class is the preferred location for adding generic helpers that can be used across UI, CLI, and API tests.
  - Helpers added to this class or inherited by this class can be accessed as `sat_obj.api_factory.helper_func_name()`.

- `cli_factory.py`
  - This module contains the `CLIFactory` class. Helpers within this class enable integrated operations between components of the satellite object using satellite CLI hammer commands.
  - While it is not our primary choice to add more CLI-based helpers, this class is the appropriate place to add them if the test demands it.
  - Helpers added to this class or inherited by this class can be accessed as `sat_obj.cli_factory.helper_func_name()`.

- `ui_factory.py`
  - This module contains a `UIFactory` class that accepts a session object as a parameter. Helpers within this class enable integrated operations between components of the satellite object using the satellite UI.
  - Although adding more UI-based helpers is not our preference, this class is suitable for adding them if the test demands it.
  - Helpers added to this class or inherited by this class can be accessed as `sat_obj.ui_factory(session).helper_func_name()`.
  - The session object provided here is the existing session object from the test case where the helper is being accessed.
  - One can use different session object when session is created for different user parameters if needed.

- `*_mixins.py`
  - Classes in mixin modules are inherited by the `Satellite`, `Capsule`, and `Host` classes in the `robottelo/hosts.py` module. Refer to the `hosts.py` module section for more details on that class.
  - Mixin classes in these mixin modules and their methods extend functionalities for the host classes in `robottelo/hosts.py` mentioned on above line.
  - Unlike methods in `robottelo/hosts.py`, these methods do not pertain to the hosts themselves but perform operations on those hosts and integration between host components.

#### utils
  - Helpers/Utilities which are not directly related to any host object (that does not need operations on hosts) should be added to utils package.
  - We have special utility modules for a specific subject. One can add utility helpers in those modules if the helper relates to any of the utlity modules or create new module for new specific subject.
  - If the helper does not fit into any of the existing utils modules or subject of helper(s) is not big enough to create new , then add in `robottelo/utils/__init__.py` as a standalone helper.

#### hosts.py
The `hosts.py` module primarily contains three main classes that represent RedHat Satellite's hosts. Each higher ordered class here inherits the behavior of the previous host class.:

- **ContentHost**:
  - This class represents the ContentHost or Client, including crucial properties and methods that describe these hosts.
  - Properties like `hostname` specify details about specific ContentHosts.
  - The `nailgun_host` property returns the API/nailgun object for the ContentHost.
  - Methods within this class manage operations on ContentHosts, particularly for reconfiguring them. Other operational methods are part of the ContentHost mixins.
  - This class inherits methods from `Brokers` modules `Host` class, hence methods from that class are available with this class objects.
- **Capsule**:
  - This class represents the Capsule host and includes essential properties and methods that describe the Capsule host.
  - Properties like `url` and `is_stream` specify details about the specific Capsule host.
  - The `satellite` property returns the satellite object to which the Capsule is connected.
  - Methods within this class manage operations related to the Capsule, especially for reconfiguring it via installation processes. Other operational methods are part of the Capsule mixins. e.g `sat.restart_services()`
  - This class inherits methods from ContentHost class, hence methods from these classes are available with this class objects.
- **Satellite**:
  - This class serves as the representation of the Satellite host and includes essential properties and methods that describe the Satellite host.
  - Properties like `hostname` and `port` specify specific details about the Satellite host.
  - Properties like `api`, `cli`, and `ui_session` provide access to interface objects that expose satellite components through various endpoints. For example, you can access these components as `sat.api.ActivationKey`, `sat.cli.ActivationKey`, or `sat.ui_session.ActivationKey`.
  - Methods within this class handle satellite operations, especially for reconfiguring the satellite via installation processes etc. Other operational methods are part of the Satellite mixins, including factories. e.g `sat.capsule_certs_generate()`
  - This class inherits methods from ContentHost and Capsule classes, hence methods from those classes are available with this class objects.

By adhering to these best practices, you'll contribute to the efficient organization and accessibility of helpers within the framework, enhancing the overall development experience and maintainability
 of the project. Thank you for your commitment to best practices!


## FAQs:

_**Question. When should I prefer/not prefer fixtures over to helper function when implementing a new helper ?**_

_Answer:_ The answers could be multiple. Fixture over functions are preferred when:
   - A new helper function should be cached based on scope of the function usage.
   - A new helper has dependency on other fixtures.
   - A new helper provides the facility of setup and teardown in the helper function itself.
   - A new helper as a fixture accept parameters, allowing you to create dynamic test scenarios.

_**Question. Where should I implement the fixture that could be used by all tests from all endpoints?**_

  _Answer:_ The global package `pytest_fixtures` is the recommended place. Choose the right subpackage `core` if framework fixture `component` if component fixture.

_**Question. Where should we implement the helper functions needed by fixtures ?**_

  _Answer:_ It is preferred to use reusable helper function in utils modules but if the function is not reusable, it should live in the fixture own module.

_**Question. Whats the most preferred user interface for writing helper that could be used across all three interfaces tests ?**_

  _Answer:_ API helpers are preferred but if test demands setup from UI/CLI interfaces then the helper should be added in those interfaces.

_**Question. I want to create a property / method to describe satellite/capsule/host, where should I add that property ?**_

  _Answer:_ Satellite/Caspule/ContentHost classes (but not in their mixins) are the best to add properties/methods that describe those.

_**Question. I want to perform operations on Satellite/Capsule/ContentHost like execute CLI commands, read conf files etc, where should I add a method for that?**_

  _Answer:_ Add into existing mixin classes in mixin modules in `robottelo/host_helpers/*_mixins.py` or create a new targeted mixin class and inherit than in host classes of `robottelo/hosts.py` module

_**Question. I have new CLI or UI or API entity or operation to implement, should it be in factory object or endpoint object.**_

  _Answer:_ New entity/subcommand/operations added in satellite product should be added to be accessed by endpoint onjects. e.g `target_sat.api.ComponentNew()`. The factory objects are just for adding helpers.

_**Question. When should I prefer helper function as a host object method over utils function ?**_

  _Answer:_ When the new function is dependent on existing host methods or attributes then its good implement such helper function in host classes as it makes to access those host methods and attributes easier.

_**Question. What helper functions goes into `robottelo/utils/__init__.py` module?**_

  _Answer:_ If the helper does not fit into any of the existing utils modules or subject of helper(s) is not big enough to create new , then add in `robottelo/utils/__init__.py` as a standalone helper.

_**Question. I have a helper function that applies to all Satellite, Capsule, ContentHost classes. Which class should I choose to add it?**_

  _Answer:_ The recommeded class in such cases is always the highest parent class. Here ContentHost class is the highest parent class where this function should be added as a class method or a mixin method.

_**Question. I have some upgrade scenario helpers to implement, where should I add them?**_

  _Answer:_ Upgrade scenarios are not special in this case. All helpers/function except framework should be same as being used in foreman tests and hence all rules are applied.

_**Question. Where should a non-reusable helper function reside?**_

  _Answer:_ The preffered place is the test module where its being used.

_**Question. I need to extend the functionality of third party library methods/objects, should I do it in robottelo?**_

  _Answer:_ Its recommended to extend the functionality of third library methods in that library itself if its being maintained by SatelliteQE like airgun,nailgun, manifester or is active community like widgetastic, wrapanapi. Else extend that appropriately in utils, host methods or fixtures.

_**Question. What if I see two helper methods/functions almost doing equal operations with a little diff ?**_

  _Answer:_ See if this could be merged in one function with optional parameters else leave them separated. E.g provisioning functions using API calls with minimum difference and being used in API, UI and CLI tests then merge them. But if two provisioning helpers one for CLI and API tests and tests demands it then good to keep it separate.
