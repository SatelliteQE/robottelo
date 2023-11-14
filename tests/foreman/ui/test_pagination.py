"""Test class for Locations UI

:Requirement: Location

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: OrganizationsandLocations

:Team: Endeavour

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


@pytest.mark.tier2
def test_pagination(session):
    """Dummy test for pagination

    Args:
        session (_type_): _description_
    """
    with session:

        # Pagination in SatTable
        view = session.task.navigate_to(session.task, 'All')
        assert view.table.pagination.is_enabled is True
        assert view.table.pagination.current_page == 1
        view.table.pagination.next_page()
        assert view.table.pagination.current_page == 2
        view.table.pagination.previous_page()
        assert view.table.pagination.current_page == 1
        assert view.table.pagination.total_pages > 0

        # Pagination in a view with Table, Pagination disabled
        view = session.location.navigate_to(session.location, 'All')
        assert view.pagination.is_enabled is False
        assert view.pagination.current_page == 1
        assert view.pagination.total_pages > 0

        # Create dummy locations to fill table
        for i in range(0, 21):
            session.location.create({'name': f'location{i}'})

        # Pagination in a view with Table, Pagination enabled
        view = session.location.navigate_to(session.location, 'All')
        assert view.pagination.is_enabled is True
        assert view.pagination.current_page == 1
        view.pagination.next_page()
        assert view.pagination.current_page == 2
        view.pagination.previous_page()
        assert view.pagination.current_page == 1
        assert view.pagination.total_pages > 0
