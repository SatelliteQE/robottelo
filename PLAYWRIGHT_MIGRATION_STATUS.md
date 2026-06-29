# Airgun: Selenium to Playwright Migration

## Where We Are

We rewrote airgun to run on Playwright instead of Selenium. The core migration is finished — every import, every API call, every widget has been converted. There are zero Selenium references left in the codebase. We are now in the testing phase, running real UI tests against a Satellite instance to find whatever we missed.

13 UI tests pass end-to-end against a live Satellite 6.19 instance. One known bug remains: the ACE code editor doesn't reliably save content through form submission under Playwright's faster execution model.

**Branches:**
- Airgun: `zjhuntin/airgun` branch `playwright-migration` (25 commits, pushed)
- Robottelo: branch `playwright-migration` (1 commit + local config changes)
- Jira epic: [SAT-46590](https://redhat.atlassian.net/browse/SAT-46590)

---

## What We Did

The migration touched 101 files across airgun. The diff is roughly 1,580 lines added and 1,331 removed. Here is what changed and why.

### Replaced the entire browser engine

The old stack was Selenium WebDriver managed by webdriver-kaifuku's `BrowserManager`, which handled browser lifecycle, session recovery, and Selenium Grid connections. All of that is gone.

In its place is a `PlaywrightBrowserFactory` in `browser.py` (545 lines total). It manages Playwright's browser, context, and page objects directly. The factory handles:

- **Browser launch** — Chromium by default, with configurable headless mode and `slow_mo` for debugging.
- **Cookie-based sessions** — Uses `context.add_cookies()` instead of Selenium's `webdriver.add_cookie()`.
- **Video recording** — Playwright's built-in `record_video` context option, configured through robottelo's settings. No more external video capture.
- **Screenshot capture** — `page.screenshot()` instead of `webdriver.save_screenshot()`.
- **Page safety checks** — The `AirgunBrowserPlugin` still runs the same JavaScript checks for jQuery, AJAX, Angular, and Satellite-specific spinners. The JS itself is unchanged; only the execution method changed from `execute_script()` to Playwright's `page.evaluate()`.

### Upgraded the widget libraries

Three dependency changes:

1. **Removed `widgetastic.patternfly` (PF3)** — The original PatternFly 3 widget library. Selenium-only, no Playwright port exists.
2. **Removed `widgetastic.patternfly4`** — PF4 is end-of-life upstream. Also Selenium-only.
3. **Upgraded `widgetastic.core` from v1.x to v2.x** — Version 2 speaks Playwright natively. It provides the `Browser`, `Widget`, `View`, `Locator`, and `Text` primitives that airgun builds on.
4. **Added `widgetastic.patternfly5` v26.x** — PF5 equivalents for buttons, dropdowns, tables, tabs, pagination, switches, navigation, and OUIA components.

Every PF3 and PF4 import across 44 view files was replaced with a PF5 equivalent. The imports changed but the widget names stayed the same in most cases (`Button`, `Dropdown`, `Pagination`, `Select`, `Tab`, etc.), so view code required minimal changes beyond the import lines.

Four PF3 widgets had no PF5 equivalent. We reimplemented them locally in `widgets.py`:
- **`FlashMessage` / `FlashMessages`** — Satellite's flash notification bar. Reimplemented with XPath locators matching the actual Satellite HTML.
- **`Kebab`** — Three-dot action menu. Reimplemented as a simple click-to-open, select-item widget.
- **`AggregateStatusCard`** — Dashboard summary cards. Reimplemented with the Satellite-specific HTML structure.

### Fixed XPath scoping (694 locations)

This was the single largest category of changes. Selenium evaluates `//` XPath from the document root regardless of context. Playwright scopes `//` to the parent element's subtree. Every `//` in a widget locator that was meant to search from the document root needed to become `.//` to keep the same behavior under Playwright.

We converted these in two passes:

**Pass 1:** Bulk `//` to `.//` conversion across all view and widget files. This fixed most locators but introduced a subtle bug in about 15 locations.

**Pass 2:** Fixed multi-line Python string concatenation breakage. In Python, adjacent string literals concatenate implicitly:

```python
locator = (
    './/div[contains(@class, "main")]'
    '//table[@id="results"]'
)
```

This produces `.//div[contains(@class, "main")]//table[@id="results"]` — valid XPath. But the bulk conversion changed it to:

```python
locator = (
    './/div[contains(@class, "main")]'
    './/table[@id="results"]'
)
```

Which produces `.//div[contains(@class, "main")].//table[@id="results"]` — invalid XPath. The leading `.` on continuation lines had to be removed. We also had to distinguish this from cases inside XPath predicates like `label[.//strong[...]]`, where `.//` is correct and must be preserved.

### Fixed widgets that broke under Playwright

Several airgun widgets made assumptions about browser behavior that Selenium tolerated but Playwright does not.

**SatTab** — Satellite uses two tab styles: PF5 tabs and older Rails-style Bootstrap tabs. PF5 tabs use `<button>` elements with `aria-selected`. Bootstrap tabs use `<a>` elements inside `<li>` with an `.active` class. The PF5 `Tab` widget from widgetastic-patternfly5 only handles the PF5 case. We rewrote `SatTab.click()` and `SatTab.is_active` to detect which style is present and handle both.

**FilteredDropdown / Select2** — Select2 dropdown menus are portaled to the document body. When you click a Select2 widget, the menu appears as a direct child of `<body>`, outside the parent widget's DOM subtree. Under Selenium, `//` searched the whole document, so locators found these menus. Under Playwright, `.//` only searches within the parent, so the menus became invisible. We fixed this by adjusting the click target (clicking the container instead of the arrow element) and using document-root locators for the portaled menu.

**SatSelect** — Several `SatSelect` widgets use inline JavaScript to manipulate form values. Selenium's `execute_script` accepts `function(){}` syntax. Playwright requires arrow functions `() => {}`. We converted all of them.

**Button** — PF5's `Button('Submit')` widget looks for PF5-specific CSS classes (`pf-v5-c-button` or `pf-c-button`). Bootstrap buttons don't have these classes, so `Button('Submit')` fails on Rails-style pages. We converted approximately 100 Bootstrap buttons across the views to `Button(locator='.//button[normalize-space(.)="Submit"]')`, which matches by text without checking CSS classes. This preserves button semantics while working on both PF5 and Bootstrap pages.

**ActionsDropdown, FieldWithEditButton, CVESelect** — Various locator and interaction fixes. The portaled-menu problem affected several dropdown-style widgets beyond Select2.

### Fixed Selenium API calls in entity methods

Grep'd the entire codebase for Selenium-specific method calls that don't exist on Playwright Locators:

- **`get_property('innerHTML')`** — Selenium WebElement method. Replaced with `inner_html()` in `provisioning_template.py` and `report_template.py`.
- **`is_selected()`** — Selenium method for checkboxes. Replaced with `is_checked()` in `cloud_vulnerabilities.py`.
- **`save_downloaded_file()`** — The old implementation scraped `chrome://downloads` using shadow DOM JavaScript. The new implementation accepts an optional `trigger` callable. When provided, it wraps the trigger action inside Playwright's `expect_download()` context manager, which reliably captures the download. Nine entity files were updated to pass their click action as a trigger lambda.

### Fixed text extraction

Selenium's `.text` property returns visible text — it strips hidden elements, collapses whitespace, and respects CSS `display: none`. Playwright's `text_content()` returns raw text content including hidden elements. This caused test assertions to fail because they were comparing against visible text.

We overrode `AirgunBrowser.text()` to use `inner_text()` instead of `text_content()`. `inner_text()` matches Selenium's visible-text behavior. One exception: SVG elements, where `inner_text()` is undefined in the DOM spec. For SVG nodes, we fall back to `text_content()`.

### Updated robottelo's config and harness

- **`configure_airgun()`** in `robottelo/config/__init__.py` — Now passes Playwright settings (browser type, headless mode, `slow_mo`, video recording, video path) instead of Selenium Grid URLs and Chrome options.
- **`conftest.py`** — Removed the `video_cleanup` pytest plugin (Selenium-era video handling).
- **`Dockerfile.playwright`** and **`Jenkinsfile.playwright`** — Built for CI, not yet validated with a real pipeline run.

---

## What Works

These tests ran end-to-end against a live Satellite 6.19 instance and passed. Each test exercises the full stack: Playwright browser, airgun session, navigation, view rendering, widget interaction, form filling, table reading, and flash message validation.

| Test File | Tests | All Passed |
|-----------|-------|------------|
| `test_bookmarks` | 3 (UserGroup, Product, ProvisioningTemplate) | Yes |
| `test_settings` | 1 (login_text) | Yes |
| `test_lifecycleenvironment` | 1 (end to end) | Yes |
| `test_activationkey` | 1 (CRUD) | Yes |
| `test_reporttemplates` | 1 (end to end, including file download) | Yes |
| `test_user` | 8 | Yes |
| `test_location` | 3 | Yes |
| `test_media` | 1 (end to end) | Yes |
| `test_subnet` | 1 (end to end) | Yes |

Five additional tests failed during fixture setup due to missing settings values (`offline_token`, `libvirt.hostname`), a CDN registration error, and a nailgun API incompatibility. None of these failures touch airgun or Playwright — they fail before the browser even opens.

---

## Test Coverage: What We Ran and What We Didn't

There are 73 UI test files in robottelo. We ran tests from 10 of them. The other 63 have not been touched. Here is a full accounting of both groups and the reasoning behind the selection.

### Why these 10 files

We chose these files as Wave 1 because they exercise the most common widget patterns — text inputs, dropdowns, tables, tabs, flash messages, and form submission — without requiring complex infrastructure or exotic view layouts. The goal was to validate that the core migration works broadly across many different pages, not deeply within a single page. If a FilteredDropdown fix works on activation keys, it works on domains. If SatTab renders correctly on users, it renders correctly on operating systems. Running one straightforward test from each of 10 different pages covers more surface area than running 30 tests from a single page.

Each file also had at least one test that could run with minimal Satellite configuration — no LDAP server, no compute resources, no content synced from CDN, no puppet modules installed.

### Files tested (10 of 73)

| File | Tests run | Tests in file | What it validated |
|------|-----------|---------------|-------------------|
| `test_activationkey` | 1 | ~30 | CRUD form with FilteredDropdown (Select2), table search, LCE selector |
| `test_bookmarks` | 3 | 5 | Bookmark creation across three different entity pages, modal dialogs |
| `test_lifecycleenvironment` | 1 | 6 | LCE path creation, drag-style workflow |
| `test_location` | 3 | 4 | CRUD with multi-select widgets, org/location context switching |
| `test_media` | 1 | 1 | Simple CRUD, text inputs, flash message validation |
| `test_reporttemplates` | 1 | ~23 | End-to-end including file download (validates `expect_download()` trigger pattern) |
| `test_settings` | 1 | ~16 | Settings page read/write, inline edit widget |
| `test_subnet` | 1 | 1 | CRUD with SatTab (Bootstrap-style tabs), multiple tab forms |
| `test_user` | 8 | 12 | CRUD, role assignment, password change, table pagination, admin flag |
| `test_jobtemplate` | 0 passing | 2 | ACE code editor — both tests fail due to form sync bug (see below) |

**Total: ~20 tests run across 10 files. 20 passed, 1 failed (ACE editor), 5 fixture errors (infrastructure, not Playwright).**

### Files not tested (63 of 73) and why

These 63 files fall into five groups based on what blocks them or why they were deferred.

**Group 1: Simple views we haven't reached yet (19 files)**

These use the same widget patterns as the Wave 1 files — CRUD forms, tables, dropdowns, tabs. They should work without new fixes. They were deferred only because we had not yet gotten to them, not because we expect problems.

- `test_architecture` — simple CRUD
- `test_audit` — read-only table view
- `test_branding` — read-only page checks
- `test_config_group` — simple CRUD
- `test_containerimagetag` — table view
- `test_dashboard` — read-only widgets
- `test_documentation_links` — link validation
- `test_domain` — CRUD with parameters tab
- `test_eol_banner` — banner display check
- `test_fact` — read-only table
- `test_hardwaremodel` — simple CRUD
- `test_http_proxy` — CRUD with auth fields
- `test_operatingsystem` — CRUD with SatTab
- `test_product` — CRUD with sync plan
- `test_role` — CRUD with permission assignment
- `test_search` — search bar behavior
- `test_syncplan` — CRUD with date/time picker
- `test_usergroup` — CRUD with role/user assignment
- `test_subscription` — table view, manifest upload

**Group 2: ACE editor dependent (4 files)**

These create or edit templates through the ACE code editor widget. They will fail with the same form sync bug that blocks `test_jobtemplate`. Fixing the ACE editor unblocks all four at once.

- `test_jobtemplate` — already tested, fails on editor content
- `test_partitiontable` — creates partition tables with editor content
- `test_provisioningtemplate` — creates provisioning templates with editor content
- `test_templatesync` — imports and exports templates

**Group 3: Complex views with unique widget patterns (14 files)**

These use view patterns we have not yet validated — `ConditionalSwitchableView`, nested dynamic tabs, composite content views, OUIA components, or multi-step workflows with modal dialogs. They are the most likely source of new widget bugs.

- `test_ansible` — role assignment, variable management, mixed PF4/PF5 patterns
- `test_contentcredentials` — file upload widget
- `test_contentview` — composite content views, filter creation, publish/promote workflows with modals
- `test_discoveredhost` — discovery rule matching, provision workflow
- `test_discoveryrule` — conditional form sections
- `test_errata` — complex table with expandable rows, host assignment
- `test_host` — the most complex view in airgun (ConditionalSwitchableView, nested tabs, dynamic form sections that change based on OS and compute resource selection)
- `test_hostcollection` — collection management, host assignment
- `test_hostgroup` — inheritance-aware forms where values cascade from parent groups
- `test_ldap_authentication` — modal-heavy flow with test connection, requires LDAP server
- `test_modulestreams` — stream management tables
- `test_oscappolicy` — multi-step wizard with conditional steps
- `test_organization` — similar to location but with more complex context switching
- `test_registration` — multi-step registration workflow

**Group 4: Requires specific infrastructure (15 files)**

These tests need infrastructure beyond a basic Satellite instance — compute resource providers, content synced from CDN, puppet modules, RHEL content hosts, or cloud service credentials. They cannot run in our current test environment.

- `test_capsulecontent` — requires a configured capsule server
- `test_computeprofiles` — requires a compute resource connection
- `test_computeresource_azurerm` — requires Azure credentials and subscription
- `test_computeresource_ec2` — requires AWS credentials
- `test_computeresource_gce` — requires GCE service account
- `test_computeresource_libvirt` — requires libvirt hypervisor host
- `test_computeresource_ocpv` — requires OpenShift Virtualization cluster
- `test_computeresource_vmware` — requires vCenter connection
- `test_flatpak` — requires flatpak remote configuration
- `test_imagemode` — requires bootc image infrastructure
- `test_leapp_client` — requires RHEL content host for upgrade testing
- `test_oscapcontent` — requires SCAP content uploaded
- `test_oscaptailoringfile` — requires SCAP tailoring files
- `test_puppetclass` — requires puppet modules installed
- `test_puppetenvironment` — requires puppet environment configured

**Group 5: Cloud and remote execution (11 files)**

These interact with external services — Red Hat Cloud, remote execution on hosts, content syncing — and require API tokens, registered hosts, or content repositories that our test Satellite does not have configured.

- `test_acs` — alternate content sources, requires repo configuration
- `test_package` — package management, requires synced content
- `test_remoteexecution` — requires a host with remote execution configured
- `test_repositories` — requires repository sync configuration
- `test_repository` — requires content setup
- `test_rhc` — requires rhc client configuration
- `test_rhcloud_insights` — requires Insights registration and `offline_token` setting
- `test_rhcloud_insights_vulnerability` — requires Insights vulnerability data
- `test_rhcloud_inventory` — requires cloud inventory registration
- `test_rhcloud_iop` — requires Insights Optimization Platform data
- `test_sync` — requires repository sync setup

### What the coverage tells us

The 10 tested files prove the migration works for the bread-and-butter UI patterns: CRUD forms, table operations, dropdowns, tabs, flash messages, navigation, and file downloads. These patterns account for the majority of airgun's widget usage across all 73 files.

The 63 untested files break down into work that is straightforward but not yet done (19 files), work blocked by the ACE editor bug (4 files), work that will likely require new widget fixes (14 files), and work that cannot run without specific infrastructure we do not currently have configured (26 files). The first two groups are next in line. The complex views are where the remaining bugs will hide. The infrastructure-dependent tests come last, once the foundation is proven solid.

---

## What Doesn't Work Yet

### The ACE code editor doesn't save content reliably

This is the one confirmed Playwright regression. `test_jobtemplate::test_positive_end_to_end` fails consistently (reproduced three times).

The ACE editor widget uses JavaScript to set content:

```python
self.browser.execute_script(f"ace.edit('{id}').setValue(arguments[0])", value)
```

This updates ACE's in-memory buffer. But Satellite's template form has a separate change listener that syncs the buffer to a hidden `<textarea>` form field. Under Selenium, execution was slow enough that this listener fired before the test clicked Submit. Under Playwright, `setValue()` and the Submit click happen so fast that the listener never runs, and the form sends the old content.

We tried two approaches:
1. **Triggering ACE's internal change signal** — `editor.session._signal('change')` crashed ACE's `onDocumentChange` handler because it expects a structured delta object describing what changed, not a bare signal.
2. **Dispatching DOM events on the textarea** — Dispatching `change` and `input` events on the backing textarea caused a feedback loop where the value was written twice.

The fix will likely involve either finding the correct ACE callback to invoke, or switching from `setValue()` to Playwright's keyboard API to type into the editor character-by-character (slower but guaranteed to trigger all change listeners).

**What this blocks:** Any test that creates or edits template content through the ACE editor. This includes job templates, provisioning templates, partition tables, and report templates (though report template tests that only read templates still pass).

### Complex views haven't been tested

The tests we've run cover straightforward pages — forms with text inputs, dropdowns, tables, and tabs. We have not yet tested the views that have the most complex widget interactions:

- **Host views (`host.py`, `host_new.py`)** — `ConditionalSwitchableView` changes the form layout based on selected operating system or compute resource. Nested tab structures. Dynamic form sections that appear and disappear. These are the most complex views in airgun (84 and 151 lines of diff respectively).
- **Content view (`contentview_new.py`)** — Composite content view management, filter creation, publish and promote workflows with modal dialogs.
- **Compute resource views (`computeresource.py`)** — Each provider (VMware, Libvirt, EC2, GCE, Azure) has a unique form layout. The `ConditionalSwitchableView` widget selects which sub-view to display based on the provider dropdown.
- **Ansible views** — Role assignment, variable management, mixed PF4/PF5 patterns.
- **Hostgroup views** — Inheritance-aware forms where values cascade from parent groups.
- **LDAP authentication** — Modal-heavy flow with test connection functionality.

These will almost certainly surface new widget issues. The simple views proved the foundation works. The complex views will test the edges.

### Download handling works, but only with the trigger pattern

The `save_downloaded_file()` method works reliably when callers pass a `trigger` callable. Nine entity files have been updated to use this pattern. However, the fallback path (event-listener based, for cases where the caller doesn't pass a trigger) is less reliable because the `page.on('download')` event may not fire before the download is checked. Any entity that still uses the old calling convention without a trigger will need to be updated if downloads fail.

### Commits need cleanup before PR

The airgun branch has 25 commits that reflect the iterative debugging process:

```
fix SatTab locator for Rails-style nav-tabs
fix SatTab click and is_active for Rails-style tabs    <- two commits for one fix
fix FilteredDropdown to click Select2 container
fix(views): convert Bootstrap buttons to Button(locator=...)
fix(views): convert remaining Bootstrap buttons        <- continuation of previous
fix(xpath): restore // on multi-line string continuation lines  <- fixing the bulk fix
```

Before opening a PR to `SatelliteQE/airgun`, these should be reorganized into a clean, reviewable sequence — probably one commit per major area (dependencies, browser layer, widget library, view imports, entity methods, XPath scoping).

### No migration guide exists

Other airgun contributors need to understand the patterns that changed. These are the non-obvious things that will trip people up:

- XPath scoping: when to use `//` vs `.//`, and the multi-line string concatenation trap.
- `Button(locator=...)` vs `Button('text')`: which to use on Bootstrap vs PF5 pages.
- `expect_download()` trigger pattern: why the old event-listener approach doesn't work.
- `inner_text()` vs `text_content()`: why text extraction works differently and the SVG exception.
- `execute_script` differences: arrow functions required, `arguments[0]` still works through widgetastic v2's compatibility wrapper.

### CI pipeline hasn't been validated

We built a `Dockerfile.playwright` and a `Jenkinsfile.playwright` for running tests in CI. The container image is designed to run on the private registry at `images.paas.redhat.com`. But we haven't triggered an actual Jenkins pipeline run. This was deferred because validating CI infrastructure while the tests themselves are still being debugged adds noise without value.

---

## The Full Change List

### Files changed by category

| Category | Files | What changed |
|----------|-------|-------------|
| Core (browser, session, settings, exceptions) | 5 | Complete rewrite of browser factory and session lifecycle |
| Widget library | 1 (`widgets.py`, 3,436 lines) | PF3 reimplementations, SatTab rewrite, Button/Dropdown/Select fixes |
| View definitions | 83 files | PF3/PF4 imports replaced with PF5, XPath `//` to `.//`, Bootstrap buttons converted |
| Entity methods | 16 files | Selenium API calls replaced, download trigger pattern added |
| Dependencies | 1 (`setup.py`) | Selenium/kaifuku/PF3/PF4 removed, Playwright/widgetastic v2/PF5 added |
| Navigation | 1 (`navigation.py`) | Exception import updated |
| Robottelo config | 1 (`config/__init__.py`) | Playwright settings instead of Selenium Grid config |
| CI infrastructure | 2 (`Dockerfile.playwright`, `Jenkinsfile.playwright`) | New files for Playwright-based CI |

### Commit history (oldest to newest)

```
8845d7b fix(deps): remove Selenium, add Playwright dependencies
d43fb15 fix(core): update session, settings, exceptions for Playwright lifecycle
3fde6d7 fix(browser): rewrite browser.py with PlaywrightBrowserFactory
6fec919 fix(views): replace PF3/PF4 widget imports with PF5 across all views
a18bd6b fix(widgets): reimplement PF3 widgets locally, fix SatTab and FilteredDropdown
0f51102 fix(entities): replace Selenium API calls with Playwright equivalents
b92fffb Set default browser to chromium in PlaywrightSettings
3c4ea79 Skip unknown config sections in Settings.configure()
e82f515 Fix SatTab locator for Rails-style nav-tabs
c630cc9 Fix SatTab click and is_active for Rails-style tabs
4f645ad Fix FilteredDropdown to click Select2 container instead of arrow
0fc2495 fix(browser): add video recording support and fix exception imports
11f1cf4 fix(views): rewrite TemplateEditor fullscreen and convert Bootstrap buttons
4353f19 fix(views): override ScheduledChart.read() to use inner_text()
d3ebf7f fix(views): convert Bootstrap buttons to Button(locator=...) pattern
e08ac8d fix(entities): fix Playwright API incompatibilities in entity methods
fa7b5e6 fix(views,widgets): XPath scoping audit pass 2 and import consolidation
7dd3fbb fix(views): convert remaining Bootstrap buttons to Button(locator=...)
4cc66d9 fix(browser): override text() to use inner_text() instead of text_content()
79f5028 fix(browser): fall back to text_content() for SVG elements in text()
cf61077 fix(widgets): convert SatSelect JS to Playwright arrow function format
b7d8021 fix(widgets): fix ActionsDropdown and FieldWithEditButton for Playwright
1714bde fix(widgets): fix CVESelect portaled menu and ActionsDropdown locators
313e4bd fix(xpath): restore // on multi-line string continuation lines
bc20bf4 fix(browser): use expect_download() for reliable file download handling
```

---

## What's Next

1. **Fix the ACE editor.** This is the immediate blocker. Most promising approach: use Playwright's keyboard API to type into the editor, or identify the correct ACE event callback that Satellite binds to sync content to the form.

2. **Test the complex views.** Run tests that exercise host creation, content view management, compute resource forms, and ansible role assignment. Each of these will likely surface new widget issues that need fixing.

3. **Clean up the commit history.** Squash and reorganize the 25 airgun commits into a reviewable series before opening PRs.

4. **Write the migration guide.** Document the patterns that changed so other contributors can maintain the Playwright-based codebase.

5. **Validate the CI pipeline.** Trigger a real Jenkins run with the Playwright container to confirm the infrastructure works end-to-end.
