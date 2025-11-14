# Robottelo - AI Agent Guide

**Project**: SatelliteQE Robottelo  
**Repository**: https://github.com/SatelliteQE/robottelo

---

## Project Overview

**Robottelo** is a comprehensive test suite for **Red Hat Satellite** (The Foreman). All tests are automated, data-driven, and designed for continuous integration environments.

### Purpose
- Automated testing of Red Hat Satellite across UI, CLI, and API interfaces
- Data-driven test design for comprehensive coverage
- Support for upgrade testing and performance validation
- Infrastructure provisioning and content management testing

### Key Technologies
- **pytest**: Test framework and runner
- **Airgun**: UI testing via Selenium/Widgetastic
- **Nailgun**: API testing via Python wrapper
- **Hussh**: CLI testing via SSH
- **Broker**: Infrastructure management for test hosts
- **Manifester**: Satellite manifest management

### Test Types

**UI Tests**: Use Airgun (Selenium/Widgetastic) for browser automation
- Location: `tests/foreman/ui/`
- Example: `tests/foreman/ui/test_activationkey.py`

**CLI Tests**: Use SSH to execute hammer commands
- Location: `tests/foreman/cli/`
- Example: `tests/foreman/cli/test_activationkey.py`

**API Tests**: Use Nailgun to interact with Satellite API
- Location: `tests/foreman/api/`
- Example: `tests/foreman/api/test_activationkey.py`

**Upgrade Tests**: Uses`SharedResource` for single-test upgrade scenarios:
- Location: 'tests/new_upgrades'
- Example: 'tests'new_upgrades/test_activation_key.py'

---

## Architecture

Robottelo follows a **layered testing architecture** that separates test logic, fixtures, and helper utilities:

### Layer 1: Test Layer
The top layer where actual test functions are written using pytest.

- **Purpose**: Define test scenarios and assertions
- **Location**: `tests/foreman/{api,cli,ui}/`
- **Example**: `def test_positive_create_activation_key(...)`
- **Responsibilities**:
  - Execute test steps
  - Assert expected outcomes
  - Use fixtures for setup/teardown

### Layer 2: Fixture Layer
The middle layer providing reusable test setup and teardown logic.

- **Purpose**: Provide test dependencies and resources
- **Location**: `pytest_fixtures/`
- **Types**:
  - **Core fixtures**: `pytest_fixtures/core/` (Satellite, Broker, ContentHost)
  - **Component fixtures**: `pytest_fixtures/component/` (per-feature fixtures)
- **Responsibilities**:
  - Provision infrastructure (Satellite, hosts)
  - Configure test prerequisites
  - Clean up resources after tests if needed

### Layer 3: Helper/Utility Layer
The bottom layer containing helper classes, utilities, and base implementations.

- **Purpose**: Provide reusable code for common operations
- **Location**: `robottelo/`
- **Components**:
  - **API helpers**: `robottelo/api/` (Nailgun entities)
  - **Host classes**:  `robottelo.hosts.py` (Base functionality for ContentHost, Capsule, Satellite interaction s)
  - **CLI helpers**: `robottelo/cli/` (Hammer command wrappers)
  - **Host helpers**: `robottelo/host_helpers/` (Satellite/ContentHost mixins)
  - **Utilities**: `robottelo/utils/` (decorators, data factories, etc.)

### Layer 4: Infrastructure Layer
External services and tools that tests depend on.

- **Broker**: VM/Container host provisioning
- **Manifester**: Subscription manifest generation
- **Report Portal**: Test result reporting
- **Vault**: Secret management

---

## Key Concepts

### 1. **Fixtures**

Pytest fixtures provide test dependencies and setup/teardown logic.

**Core Fixtures**:
- `target_sat`: A Satellite instance for the test
- `module_target_sat`: Module-scoped Satellite instance
- `function_sca_manifest`: Function-scoped SCA manifest
- `rhel_contenthost`: RHEL content host for testing

**Component Fixtures**:
- `module_ak_with_cv`: Activation key with content view
- `module_lce`: Lifecycle environment
- `module_org`: Organization

**Fixture Scopes**:
- `function`: Per test function (default)
- `module`: Per test module
- `session`: Per test session
- `class`: Per test session

Example:

```python
@pytest.fixture
def activation_key(module_org, module_target_sat):
    """Create an activation key for testing"""
    ak = module_target_sat.api.ActivationKey(
        organization=module_org,
        name='test-ak'
    ).create()
    return ak  # or yield when a cleanup step comes next
```

### 2. **Markers**

Pytest markers categorize and filter tests.

**Common Markers**:
- `@pytest.mark.e2e`: End-to-end workflow tests
- `@pytest.mark.rhel_ver_match()`: Filter by RHEL version
- `@pytest.mark.rhel_ver_list()`: FIlter by specific RHEL version
- `@pytest.mark.parametrize()`: Parameterize test inputs

Example:

```python
@pytest.mark.rhel_ver_match(r'^(9|10)')
def test_positive_create_ak(module_org, module_target_sat):
    """Test activation key creation"""
    ak = module_target_sat.api.ActivationKey(
        organization=module_org
    ).create()
```

### 3. **Host Helpers**

Mixins that provide common functionality for Satellite and ContentHost objects.

**Satellite Mixins** (`robottelo/host_helpers/satellite_mixins.py`):
- `api_factory`: API entity creation methods
- `cli_factory`: CLI entity creation methods
- `ui_session()`: Context manager for UI sessions

**ContentHost Mixins** (`robottelo/host_helpers/contenthost_mixins.py`):
- `register_contenthost()`: Register host to Satellite
- `install_katello_ca()`: Install Katello CA certificate
- `execute()`: Run commands on content host

Example:

```python
# Using Satellite API factory
ak = target_sat.api.ActivationKey(organization=org).create()

# Using UI session
with target_sat.ui_session() as session:
    session.organization.select('ORG_NAME')
	session.location.select('LOC_NAME')
    session.activationkey.create({'name': 'my-ak'})

# Using ContentHost methods
rhel_contenthost.register_contenthost(org, ak)
result = rhel_contenthost.execute('subscription-manager status')
```

### 4. **Data Factories**

Generate random test data using `robottelo.utils.datafactory`.

**Common Functions**:
- `gen_string()`: Generate random strings
- `gen_alpha()`: Generate alphabetic strings
- `gen_numeric_string()`: Generate numeric strings
- `gen_email()`: Generate email addresses

Example:

```python
from robottelo.utils.datafactory import gen_string

name = gen_string('alpha', 10)  # Random 10-char alphabetic string
email = gen_email()  # Random email
```
---

## Code Standards

### Import Ordering

1. **Standard library** imports
2. **Third-party** imports (alphabetical)
3. **Robottelo** imports (alphabetical)
4. Blank line between groups

```python
# Standard library
from robottelo.logging import logger
from datetime import datetime

# Third-party
import pytest
from box import Box
from nailgun.entities import ActivationKey

# Robottelo
from robottelo.config import settings
from robottelo.constants import DEFAULT_CV
from robottelo.utils.datafactory import gen_string
```

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| **Test Functions** | `test_{type}_{action}_{entity}` | `test_positive_create_activation_key` |
| **Fixtures** | `{scope}_{entity}` | `module_activation_key`, `function_org` |
| **Classes** | CamelCase | `ActivationKey`, `ContentView` |
| **Functions/Methods** | snake_case | `create()`, `delete()`, `register_contenthost()` |
| **Constants** | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT`, `OPENSSH_RECOMMENDATION` |
| **Private** | Leading underscore | `_helper()`, `_validate()` |

### Test Naming Pattern

Test names follow a specific pattern to indicate expected behavior:

- `test_positive_*`: Test should succeed (happy path)
- `test_negative_*`: Test should fail with expected error (error handling)
- `test_upgrade_*`: Upgrade scenario test

Examples:
- `test_positive_create_activation_key_with_cv()`
- `test_negative_create_ak_with_invalid_name()`
- `test_upgrade_content_view_promotion()`

### Docstring Style

Use **reStructuredText** format with required fields:

```python
def test_positive_create_activation_key(module_org, module_target_sat):
    """Create activation key with valid name
    
    :id: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d <uuid generated with 'uuidgen | tr "[:upper:]" "[:lower:]"'>
    
    :steps:
        1. Create organization
        2. Create activation key with valid name
        3. Verify activation key exists
    
    :expectedresults: Activation key is created successfully
    
    :CaseImportance: Critical
    
    :CaseAutomation: Automated
    """
    ak = module_target_sat.api.ActivationKey(
        organization=module_org,
        name=gen_string('alpha')
    ).create()
```

**Required Fields**:
- `:id:` - Unique test UUID
- `:steps:` - Test execution steps
- `:expectedresults:` - Expected outcome

**Optional fields**
- `:Verifies:` - When the test verifies a Bug (Use as :Verifies: SAT-12345) (Formely there was :BZ: tag, don't use that anymore) 
---

## Testing Patterns

### Pattern 1: Basic CRUD Test (API)

```python
def test_positive_create_activation_key(module_org, module_target_sat):
    """Test activation key creation via API"""
    # Create
    ak = module_target_sat.api.ActivationKey(
        organization=module_org,
        name=gen_string('alpha')
    ).create()
    
    # Read
    ak_read = module_target_sat.api.ActivationKey(id=ak.id).read()
    assert ak_read.name == ak.name
    
    # Update
    new_name = gen_string('alpha')
    ak.name = new_name
    ak.update(['name'])
    assert ak.read().name == new_name
    
    # Delete
    ak.delete()
    with pytest.raises(HTTPError):
        ak.read()
```

### Pattern 2: UI Test with Session

```python
def test_positive_create_ak_via_ui(module_org, module_target_sat):
    """Test activation key creation via UI"""
    ak_name = gen_string('alpha')
    
    with module_target_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        
        # Create via UI
        session.activationkey.create({
            'name': ak_name,
            'lce': {'value': 'Library'}
        })
        
        # Verify in UI
        ak_values = session.activationkey.read(ak_name)
        assert ak_values['details']['name'] == ak_name
```

### Pattern 3: CLI Test

```python
def test_positive_create_ak_via_cli(module_org, module_target_sat):
    """Test activation key creation via CLI"""
    ak_name = gen_string('alpha')
    
    # Create via CLI
    result = module_target_sat.cli.ActivationKey.create({
        'name': ak_name,
        'organization-id': module_org.id,
        'lifecycle-environment': 'Library'
    })
    
    # Verify
    assert result['name'] == ak_name
    
    # Read via CLI
    ak_info = module_target_sat.cli.ActivationKey.info({
        'id': result['id']
    })
    assert ak_info['name'] == ak_name
```

### Pattern 4: Parametrized Test

```python
@pytest.mark.parametrize('name', [
    gen_string('alpha'),
    gen_string('numeric'),
    gen_string('alphanumeric'),
])
def test_positive_create_with_different_names(name, module_org, module_target_sat):
    """Test activation key creation with various name types"""
    ak = module_target_sat.api.ActivationKey(
        organization=module_org,
        name=name
    ).create()
    assert ak.name == name
```

### Pattern 5: End-to-End Test

```python
@pytest.mark.e2e
def test_positive_content_host_e2e(
    module_org,
    module_lce,
    module_cv,
    rhel_contenthost,
    module_target_sat
):
    """End-to-end content host registration and package installation"""
    # Create activation key
    ak = module_target_sat.api.ActivationKey(
        organization=module_org,
        environment=module_lce,
        content_view=module_cv
    ).create()
    
    # Register content host
    rhel_contenthost.register_contenthost(
        org=module_org,
        activation_key=ak.name
    )
    
    # Verify registration
    result = rhel_contenthost.execute('subscription-manager identity')
    assert result.status == 0
    
    # Install package
    result = rhel_contenthost.execute('yum install -y tree')
    assert result.status == 0
    
    # Verify package installed
    result = rhel_contenthost.execute('rpm -q tree')
    assert result.status == 0
```

---

## Fixture System

### Core Fixtures

**Satellite Fixtures** (`pytest_fixtures/core/sat_cap_factory.py`):

```python
# Function-scoped Satellite
@pytest.fixture
def target_sat(request):
    """Provides a Satellite instance for testing"""
    ...

# Module-scoped Satellite
@pytest.fixture(scope='module')
def module_target_sat(request):
    """Module-scoped Satellite instance"""
    ...

# Satellite with specific configuration
@pytest.fixture(scope='module')
def module_satellite_iop(request, satellite_factory):
    """Satellite with IoP (Insights on Prem) enabled"""
    ...
```

**ContentHost Fixtures** (`pytest_fixtures/core/contenthosts.py`):

```python
# RHEL ContentHost
@pytest.fixture
def rhel_contenthost(request):
    """Provides a RHEL content host"""
    ...

# Parametrized by RHEL version
@pytest.mark.rhel_ver_list([9, 10])
def test_with_rhel9_and_10(rhel_contenthost):
    ...
```

**Manifest Fixtures** (`pytest_fixtures/component/subscription.py`):

```python
@pytest.fixture(scope='module')
def module_sca_manifest():
    """Module-scoped SCA manifest"""
    ...

@pytest.fixture
def function_sca_manifest():
    """Function-scoped SCA manifest"""
    ...
```

### Component Fixtures

**Activation Key Fixtures** (`pytest_fixtures/component/activationkey.py`):

```python
@pytest.fixture(scope='module')
def module_ak_with_cv(module_org, module_lce, module_cv, module_target_sat):
    """Activation key with content view attached"""
    return module_target_sat.api.ActivationKey(
        organization=module_org,
        environment=module_lce,
        content_view=module_cv
    ).create()
```

**Organization Fixtures** (`pytest_fixtures/component/taxonomy.py`):

```python
@pytest.fixture(scope='module')
def module_org(module_target_sat):
    """Module-scoped organization"""
    return module_target_sat.api.Organization().create()

@pytest.fixture
def function_org(target_sat):
    """Function-scoped organization"""
    return target_sat.api.Organization().create()
```

### Fixture Best Practices

**DO ✅**:
- Use `module` scope for expensive fixtures (Satellite, manifests)
- Use `function` scope for test-specific fixtures
- Clean up resources in fixture teardown (use `yield`)
- Parametrize fixtures using `@pytest.fixture(params=[...])` when prompted

**DON'T ❌**:
- Don't create new Satellite instances per test (use `module_target_sat`)
- Don't hard-code values in fixtures (use `gen_string()`)
- Don't skip fixture cleanup (always delete created resources)
- Don't create new fixtures unless prompted to

---

## Markers and Pytest Plugins

### Built-in Markers

**Test Type Markers**:
```python
@pytest.mark.e2e              # End-to-end tests
@pytest.mark.stubbed          # Not yet implemented
@pytest.mark.destructive      # Modifies Satellite config and needs satellite teardown
@pytest.mark.skip_if_open()   # Skip if BZ/issue open
```

**Infrastructure Markers**:
```python
@pytest.mark.pit_server       # Requires PIT Satellite
@pytest.mark.pit_client       # Requires PIT content host
@pytest.mark.no_containers    # Cannot run in containers
```

### RHEL Version Markers

**`@pytest.mark.rhel_ver_match()`**: Match RHEL versions by regex

```python
# Match RHEL 9 and 10 (exclude 7 and 8)
@pytest.mark.rhel_ver_match(r'^(9|10)')

# Match only non-FIPS versions
@pytest.mark.rhel_ver_match(r'^[\d]+$')

# Match RHEL 9 including FIPS
@pytest.mark.rhel_ver_match(r'^9')  # Matches 9, 9_fips
```

**`@pytest.mark.rhel_ver_list()`**: Specify exact RHEL versions

```python
# Test on RHEL 9 and 10 only
@pytest.mark.rhel_ver_list([9, 10])

# Test on RHEL 9, 10, and their FIPS variants
@pytest.mark.rhel_ver_list([9, '9_fips', 10, '10_fips'])
```

### Custom Plugins

**Issue Handlers** (`pytest_plugins/issue_handlers.py`):
- `@pytest.mark.skip_if_open('SAT-12345')`: Skip if Jira is open

**Fixture Markers** (`pytest_plugins/fixture_markers.py`):
- Automatically parametrizes fixtures based on markers
- Handles RHEL version selection

**Factory Collection** (`pytest_plugins/factory_collection.py`):
- Collects and reports factory usage statistics

---

## Upgrade Testing

Robottelo supports two upgrade testing patterns:

### New Upgrade Pattern (Recommended)

**Location**: `tests/new_upgrades/`

Uses `SharedResource` for single-test upgrade scenarios:

```python
from robottelo.utils.shared_resource import SharedResource

def setup_scenario(sat_instance):
    """Setup logic before upgrade"""
    org = sat_instance.api.Organization().create()
    return {'org_id': org.id}

@pytest.mark.content_upgrades
def test_content_view_upgrade(upgrade_shared_satellite):
    """Test content view survives upgrade"""
    
    # Setup before upgrade
    with SharedResource(
        "cv_upgrade_setup",
        action=setup_scenario,
        sat_instance=upgrade_shared_satellite,
    ) as setup_data:
        setup_result = setup_data.ready()
        
        # Verify after upgrade
        org = upgrade_shared_satellite.api.Organization(
            id=setup_result['org_id']
        ).read()
        assert org.id == setup_result['org_id']
```

**Key Concepts**:
- `SharedResource`: Manages setup/verification in single test
- `action=`: Function to run before upgrade
- `.ready()`: Returns setup data after upgrade
- Markers: `@pytest.mark.{feature}_upgrades`

### Old Upgrade Pattern (Legacy)

**Location**: `tests/upgrades/`

Uses separate pre/post tests with `@pytest.mark.pre_upgrade` and `@pytest.mark.post_upgrade`:

```python
@pytest.mark.pre_upgrade
def test_cv_pre_upgrade(save_test_data):
    """Setup before upgrade"""
    org = entities.Organization().create()
    save_test_data({'org_id': org.id})

@pytest.mark.post_upgrade(depend_on=test_cv_pre_upgrade)
def test_cv_post_upgrade(pre_upgrade_data):
    """Verify after upgrade"""
    org_id = pre_upgrade_data['org_id']
    org = entities.Organization(id=org_id).read()
    assert org.id == org_id
```

**Run Commands**:
```bash
# Pre-upgrade stage
pytest -m "pre_upgrade" tests/upgrades/

# Perform upgrade

# Post-upgrade stage
pytest -m "post_upgrade" tests/upgrades/
```

---

## Common Patterns

### Pattern 1: Wait for Task Completion

```python
from robottelo.constants import DEFAULT_TIMEOUT

# Wait for Satellite task
task = target_sat.api.ForemanTask(id=task_id).wait()
assert task.result == 'success'

# Wait for CLI task
result = target_sat.cli.Task.progress({
    'id': task_id,
    'timeout': DEFAULT_TIMEOUT
})
assert result['result'] == 'success'
```

### Pattern 2: Content Host Registration

```python
# Register with activation key
rhel_contenthost.install_katello_ca(target_sat)
rhel_contenthost.register_contenthost(
    org=module_org,
    activation_key=ak.name
)

# Verify registration
result = rhel_contenthost.execute('subscription-manager status')
assert result.status == 0
assert module_org.label in result.stdout
```

### Pattern 3: Repository Sync

```python
# Create and sync repository
repo = target_sat.api.Repository(
    product=product,
    url=settings.repos.yum_3.url
).create()

# Trigger sync
repo.sync()

# Wait for sync to complete
repo = repo.read()
assert repo.content_counts['packages'] > 0
```

### Pattern 4: Publishing Content View

```python
# Create content view
cv = target_sat.api.ContentView(
    organization=module_org
).create()

# Add repository
cv.repository = [repository]
cv.update(['repository'])

# Publish
cv.publish()

# Get latest version
cv = cv.read()
assert len(cv.version) == 1
```

### Pattern 5: Assert Multiple Conditions

```python
# Using assertions
assert result.status == 0, f"Command failed: {result.stderr}"
assert 'Success' in result.stdout
assert result.return_code == 0

# Using pytest.raises
with pytest.raises(HTTPError) as excinfo:
    deleted_entity.read()
assert '404' in str(excinfo.value)
```

---

## Troubleshooting

### Common Issues

#### 1. **Fixture Not Found**

**Problem**: `fixture 'xyz' not found`

**Solution**:
- Check fixture is defined in `conftest.py` or fixture file
- Ensure fixture scope matches test scope
- Verify pytest plugin is loaded in `conftest.py`

```python
# Check if fixture is in pytest_plugins list
pytest_plugins = [
    'pytest_fixtures.component.activationkey',  # Make sure this is loaded
]
```

#### 2. **Test Hangs During Execution**

**Problem**: Test hangs indefinitely

**Solution**:
- Add timeout to long-running operations
- Use `wait_for()` with proper timeout
- Check for blocking I/O operations

```python
from wait_for import wait_for

# Add timeout to wait conditions
wait_for(
    lambda: condition_check(),
    timeout=300,  # 5 minutes
    delay=10,
    logger=logger
)
```

#### 3. **Broker Checkout Failure**

**Problem**: `BrokerError: No hosts available`

**Solution**:
- Check Broker configuration in `broker_settings.yaml`
- Verify inventory has available hosts
- Check host requirements match available inventory

```bash
# Check Broker inventory
broker inventory

# Check specific host requirements
broker checkout --workflow deploy-rhel --rhel-version 9
```

#### 4. **Content Host Registration Fails**

**Problem**: Registration fails with certificate errors

**Solution**:
- Verify Katello CA is installed
- Check Satellite hostname is resolvable
- Ensure correct activation key is used

```python
# Install CA certificate first
rhel_contenthost.install_katello_ca(target_sat)

# Verify hostname resolution
result = rhel_contenthost.execute(f'ping -c 1 {target_sat.hostname}')
assert result.status == 0

# Register with proper parameters
rhel_contenthost.register_contenthost(
    org=org,
    activation_key=ak.name,
    target=target_sat
)
```

#### 5. **UI Test Element Not Found**

**Problem**: `NoSuchElementException` in UI tests

**Solution**:
- Add `wait_for` before interacting with elements
- Use `browser.plugin.ensure_page_safe()`
- Check if element is in an iframe

```python
from wait_for import wait_for

with target_sat.ui_session() as session:
    # Wait for page to load
    wait_for(lambda: session.activationkey.is_displayed, timeout=30)
    
    # Ensure page is stable
    session.browser.plugin.ensure_page_safe(timeout='10s')
    
    # Interact with element
    session.activationkey.create({'name': 'test-ak'})
```

---

## Development Conventions

### Linting and Code Quality

*   **Linting:** The project uses `ruff` for linting and formatting. The configuration is in `pyproject.toml`.
    - Line length: 100 characters
    - Quote style: Preserved (transitioning to single quotes)
    - Run manually: `ruff check .` or `ruff format .`

*   **Pre-commit Hooks:** The project can use `pre-commit` to run checks before committing.
    - Run manually: `pre-commit run --all-files`

### Configuration

*   **Test Configuration:** The application uses multiple YAML files for configuration:
    - `robottelo.yaml`: Main test configuration
    - `broker_settings.yaml`: Broker/VM configuration
    - `conf/*.yaml`: Feature-specific configurations

*   **Settings Access:** Use `robottelo.config.settings` to access configuration:

```python
from robottelo.config import settings

# Access Satellite URL
sat_url = settings.server.hostname

# Access repository URLs
repo_url = settings.repos.yum_3.url
```

### Test Organization

*   **Test Modules:** Tests are organized by interface type (API, CLI, UI) and feature area.
    - Naming: `test_{feature}.py` (e.g., `test_activationkey.py`)
    - Location: `tests/foreman/{interface}/test_{feature}.py`

*   **Test Functions:** Follow the naming convention `test_{type}_{action}_{entity}`
    - Example: `test_positive_create_activation_key`
    - Type: `positive`, `negative`, `upgrade`
    - Action: `create`, `update`, `delete`, `list`

*   **Test Documentation:** Every test must have:
    - Unique `:id:` UUID generated with 'uuidgen | tr "[:upper:]" "[:lower:]"'
    - Clear `:steps:`
    - Expected `:expectedresults:`

### Version Control

*   **Commit Messages:** Use clear, descriptive commit messages
    - Start with action verb (Add, Fix, Update, Remove)

---

## Best Practices

### DO ✅

- **Use fixtures for setup/teardown** - Avoid duplicating setup code in tests
- **Use markers to categorize tests** - Makes test selection easier
- **Clean up resources** - Delete entities after test completion
- **Use `gen_string()` for names** - Avoid hard-coded names
- **Add docstrings to all tests** - Include required fields (id, steps, expectedresults)
- **Use `module` scope for expensive fixtures** - Satellite, manifests, etc.
- **Wait for async operations** - Use `wait_for()` or `task.wait()`
- **Assert accurate messages** - reference similar tests for assert messages
- **Prioritize readability over complexity** - Avoid complex hard to read code
- **Write flat code structures over nested code structures**

### DON'T ❌

- **Don't skip cleanup** - Always delete created resources
- **Don't use `time.sleep()`** - Use `wait_for()` instead
- **Don't hard-code credentials** - Use `settings` or Vault
- **Don't copy-paste tests** - Use parametrization or fixtures
- **Don't create Satellite per test** - Use `module_target_sat`
- **Don't test Satellite UI in CLI tests** - Keep interfaces separate
- **Don't assume test order** - Tests should be independent
- **Don't write assertions within for loops** - Assertions should be easy to read
- **Don't add too many assertions in a row** - Write your assertions with intent

---

## Additional Resources

- **Documentation**: https://robottelo.readthedocs.io/
- **Repository**: https://github.com/SatelliteQE/robottelo
- **Issues**: https://github.com/SatelliteQE/robottelo/issues
- **Airgun (UI Library)**: https://github.com/SatelliteQE/airgun
- **Nailgun (API Library)**: https://github.com/SatelliteQE/nailgun
- **Broker (Infrastructure)**: https://github.com/SatelliteQE/broker
- **pytest Documentation**: https://docs.pytest.org/

---

**Last Updated**: 2025-11-11  
**Maintainers**: Cole Higgins
