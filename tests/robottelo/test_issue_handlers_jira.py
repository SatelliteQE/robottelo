"""Tests for module ``robottelo.utils.issue_handlers.jira``."""

from unittest import mock

import pytest

from robottelo.config import settings
from robottelo.constants import JIRA_WONTFIX_RESOLUTIONS
from robottelo.utils.issue_handlers import jira


def _flat_issue(key='SAT-123', status='Open', resolution=''):
    """Build flat issue dict (key, status, resolution) as stored in pytest.issue_data / cache."""
    return {'key': key, 'status': status, 'resolution': resolution or ''}


def _issue_data(issue_dict):
    """Pytest.issue_data issue: flat issue dict plus used_in (consistent with jira handler)."""
    return {**issue_dict, 'used_in': []}


class TestJiraIssueHandler:
    """Core scenarios for Jira issue handler."""

    def test_issue_to_flat_dict_uses_dot_access(self):
        """_issue_to_flat_dict extracts fields from Issue object via .key, .fields.*."""
        mock_issue = mock.Mock()
        mock_issue.key = 'SAT-456'
        mock_issue.fields.status.name = 'Closed'
        mock_issue.fields.labels = ['bug']
        mock_issue.fields.resolution.name = 'Done'
        out = jira._issue_to_flat_dict(mock_issue, jira.common_jira_fields)
        assert out['key'] == 'SAT-456'
        assert out['status'] == 'Closed'
        assert out['resolution'] == 'Done'
        assert out['labels'] == ['bug']

    def test_is_open_jira_open_vs_closed(self, monkeypatch):
        """is_open_jira returns True for open status, False for closed."""
        monkeypatch.setattr(pytest, 'issue_data', {'SAT-1': _issue_data(_flat_issue(status='New'))})
        assert jira.is_open_jira('SAT-1') is True

        monkeypatch.setattr(
            pytest,
            'issue_data',
            {'SAT-1': _issue_data(_flat_issue(status='Closed', resolution='Done'))},
        )
        assert jira.is_open_jira('SAT-1') is False

    def test_are_all_jira_open_any_closed_returns_false(self, monkeypatch):
        """are_all_jira_open returns False when any issue is closed."""
        monkeypatch.setattr(
            pytest,
            'issue_data',
            {
                'SAT-1': _issue_data(_flat_issue(key='SAT-1', status='New')),
                'SAT-2': _issue_data(_flat_issue(key='SAT-2', status='Closed', resolution='Done')),
            },
        )
        assert jira.are_all_jira_open(['SAT-1', 'SAT-2']) is False

    def test_are_any_jira_open_all_closed_returns_false(self, monkeypatch):
        """are_any_jira_open returns False when all issues are closed."""
        monkeypatch.setattr(
            pytest,
            'issue_data',
            {'SAT-1': _issue_data(_flat_issue(key='SAT-1', status='Closed', resolution='Done'))},
        )
        assert jira.are_any_jira_open(['SAT-1']) is False

    def test_should_deselect_jira_closed_wontfix_returns_true(self, monkeypatch):
        """should_deselect_jira returns True for closed + WONTFIX resolution."""
        resolution = next(iter(JIRA_WONTFIX_RESOLUTIONS))
        monkeypatch.setattr(
            pytest,
            'issue_data',
            {'SAT-1': _issue_data(_flat_issue(status='Closed', resolution=resolution))},
        )
        assert jira.should_deselect_jira('SAT-1') is True

    def test_follow_duplicates_returns_leaf_issue(self):
        """follow_duplicates follows nested dupe_data to the leaf."""
        leaf = {'key': 'SAT-3', 'status': 'Closed'}
        mid = {'key': 'SAT-2', 'dupe_data': leaf}
        top = {'key': 'SAT-1', 'dupe_data': mid}
        assert jira.follow_duplicates(top) is leaf

    def test_get_default_jira_returns_expected_structure(self):
        """get_default_jira returns dict with key, is_open True, error message."""
        out = jira.get_default_jira('SAT-999')
        assert out['key'] == 'SAT-999'
        assert out['is_open'] is True
        assert out['is_deselected'] is False
        assert 'missing jira email/api_key' in out['error']

    def test_jira_status_cache_update_and_get(self, tmp_path):
        """JiraStatusCache stores and returns issue data by id."""
        with (
            mock.patch(
                'robottelo.utils.issue_handlers.jira.settings.jira.cache_file',
                str(tmp_path / 'cache.json'),
            ),
            mock.patch(
                'robottelo.utils.issue_handlers.jira.settings.jira.cache_ttl_days',
                7,
            ),
        ):
            cache = jira.JiraStatusCache()
        data = {'key': 'SAT-1', 'status': 'Open'}
        cache.update('SAT-1', data)
        assert cache.get('SAT-1') == data | {'timestamp': mock.ANY}
        assert cache.get('SAT-2') is None

    def test_get_jira_returns_issue_objects_from_search(self):
        """get_jira returns list of Issue objects (mocked client)."""
        mock_issues = [mock.Mock(key='SAT-1'), mock.Mock(key='SAT-2')]
        with mock.patch.object(jira, '_jira_client') as m_client:
            m_jira = mock.Mock()
            m_jira.search_issues.return_value = mock_issues
            m_client.return_value = m_jira
            result = jira.get_jira('id = SAT-1 OR id = SAT-2', ['key', 'status'])
        assert result == mock_issues
        m_jira.search_issues.assert_called_once_with(
            jql_str='id = SAT-1 OR id = SAT-2', fields='key,status'
        )

    def test_get_data_jira_empty_ids_returns_empty_list(self):
        """get_data_jira with empty issue_ids returns []."""
        assert jira.get_data_jira([]) == []

    def test_get_data_jira_missing_credentials_returns_default(self):
        """get_data_jira without email/api_key returns default issue data."""
        jira.CACHED_RESPONSES['get_data'].clear()
        with (
            mock.patch('robottelo.utils.issue_handlers.jira.settings.jira.email', None),
            mock.patch('robottelo.utils.issue_handlers.jira.settings.jira.api_key', None),
        ):
            result = jira.get_data_jira(['SAT-999'])
        assert len(result) == 1
        assert result[0]['key'] == 'SAT-999'
        assert result[0].get('error')
        assert result[0]['is_open'] is True


class TestTryFromCache:
    """Focused tests for try_from_cache lookup order and fallback."""

    def test_returns_pytest_issue_data_when_present(self, monkeypatch):
        """When issue_id is in pytest.issue_data with issue fields, return it; no cache or API."""
        flat = _flat_issue(key='SAT-1', status='Open')
        monkeypatch.setattr(pytest, 'issue_data', {'SAT-1': _issue_data(flat)})
        cache_get = mock.Mock()
        get_single = mock.Mock()
        with (
            mock.patch.object(jira.jira_cache, 'get', cache_get),
            mock.patch.object(jira, 'get_single_jira', get_single),
        ):
            result = jira.try_from_cache('SAT-1')
        assert result == {**flat, 'used_in': []}
        cache_get.assert_not_called()
        get_single.assert_not_called()

    def test_returns_jira_cache_when_no_issue_data(self, monkeypatch):
        """When pytest.issue_data has no entry, return jira_cache.get result if present."""
        monkeypatch.setattr(pytest, 'issue_data', {})
        cached = {'key': 'SAT-2', 'status': 'Closed', 'resolution': 'Done'}
        with mock.patch.object(jira.jira_cache, 'get', return_value=cached):
            result = jira.try_from_cache('SAT-2')
        assert result == cached

    def test_falls_back_to_get_single_jira_when_neither_has_entry(self, monkeypatch):
        """When neither pytest.issue_data nor jira_cache has the issue, call get_single_jira."""
        monkeypatch.setattr(pytest, 'issue_data', {})
        api_result = {'key': 'SAT-3', 'status': 'New'}
        with (
            mock.patch.object(jira.jira_cache, 'get', return_value=None),
            mock.patch.object(jira, 'get_single_jira', return_value=api_result) as get_single,
        ):
            result = jira.try_from_cache('SAT-3')
        assert result == api_result
        get_single.assert_called_once_with('SAT-3')


class TestAddCommentOnJira:
    """Tests for add_comment_on_jira: disabled path, labels PUT, and comment POST."""

    def test_disabled_comments_warns_and_returns_none_no_http(self, monkeypatch):
        """When enable_comment != jira_comments (e.g. config off or option not set), warn and return None; no HTTP."""
        monkeypatch.setattr(pytest, 'jira_comments', True)  # so enable_comment False != True
        mock_client = mock.Mock()
        with (
            mock.patch('robottelo.utils.issue_handlers.jira.settings.jira.enable_comment', False),
            mock.patch.object(jira, '_jira_client', return_value=mock_client),
        ):
            result = jira.add_comment_on_jira('SAT-1', 'comment text')
        assert result is None
        mock_client._session.put.assert_not_called()
        mock_client._session.post.assert_not_called()

    def test_disabled_comments_when_jira_comments_falsy(self, monkeypatch):
        """When pytest.jira_comments is falsy, return None and make no HTTP calls."""
        monkeypatch.setattr(pytest, 'jira_comments', False)
        mock_client = mock.Mock()
        with (
            mock.patch('robottelo.utils.issue_handlers.jira.settings.jira.enable_comment', True),
            mock.patch.object(jira, '_jira_client', return_value=mock_client),
        ):
            result = jira.add_comment_on_jira('SAT-1', 'comment text')
        assert result is None
        mock_client._session.put.assert_not_called()
        mock_client._session.post.assert_not_called()

    def test_comments_enabled_with_labels_puts_labels_then_posts_comment(self, monkeypatch):
        """When labels are provided, PUT to issue with labels update, then POST comment."""
        labels = [{'add': 'tests_passed'}, {'remove': 'tests_failed'}]
        mock_session = mock.Mock()
        mock_session.put.return_value.raise_for_status = mock.Mock()
        mock_session.post.return_value.raise_for_status = mock.Mock()
        mock_session.post.return_value.json.return_value = {'id': '123'}
        mock_client = mock.Mock(_session=mock_session)
        monkeypatch.setattr(pytest, 'jira_comments', True)
        with (
            mock.patch('robottelo.utils.issue_handlers.jira.settings.jira.enable_comment', True),
            mock.patch(
                'robottelo.utils.issue_handlers.jira.settings.jira.url', 'https://jira.example'
            ),
            mock.patch.object(jira, '_jira_client', return_value=mock_client),
        ):
            result = jira.add_comment_on_jira('SAT-42', 'Done', labels=labels)
        assert result == {'id': '123'}
        mock_session.put.assert_called_once()
        put_url, put_kw = mock_session.put.call_args[0][0], mock_session.put.call_args[1]
        assert put_url == 'https://jira.example/rest/api/latest/issue/SAT-42'
        assert put_kw['json'] == {'update': {'labels': labels}}
        mock_session.post.assert_called_once()
        post_url = mock_session.post.call_args[0][0]
        assert post_url == 'https://jira.example/rest/api/latest/issue/SAT-42/comment'

    def test_comments_enabled_labels_none_only_posts_comment(self, monkeypatch):
        """When labels is None, only POST to comment endpoint; no PUT."""
        mock_session = mock.Mock()
        mock_session.post.return_value.raise_for_status = mock.Mock()
        mock_session.post.return_value.json.return_value = {'id': '456'}
        mock_client = mock.Mock(_session=mock_session)
        monkeypatch.setattr(pytest, 'jira_comments', True)
        with (
            mock.patch('robottelo.utils.issue_handlers.jira.settings.jira.enable_comment', True),
            mock.patch(
                'robottelo.utils.issue_handlers.jira.settings.jira.url', 'https://jira.example'
            ),
            mock.patch.object(jira, '_jira_client', return_value=mock_client),
        ):
            result = jira.add_comment_on_jira('SAT-99', 'Comment body', labels=None)
        assert result == {'id': '456'}
        mock_session.put.assert_not_called()
        mock_session.post.assert_called_once()
        call_kw = mock_session.post.call_args[1]
        assert call_kw['json']['body'] == 'Comment body'
        assert call_kw['json']['visibility'] == {
            'type': settings.jira.comment_type,
            'value': settings.jira.comment_visibility,
        }

    def test_post_payload_has_body_and_visibility(self, monkeypatch):
        """POST payload includes body and visibility with comment_type and comment_visibility."""
        mock_session = mock.Mock()
        mock_session.post.return_value.raise_for_status = mock.Mock()
        mock_session.post.return_value.json.return_value = {}
        mock_client = mock.Mock(_session=mock_session)
        monkeypatch.setattr(pytest, 'jira_comments', True)
        with (
            mock.patch('robottelo.utils.issue_handlers.jira.settings.jira.enable_comment', True),
            mock.patch(
                'robottelo.utils.issue_handlers.jira.settings.jira.url', 'https://jira.example'
            ),
            mock.patch.object(jira, '_jira_client', return_value=mock_client),
        ):
            jira.add_comment_on_jira(
                'SAT-1',
                'Verification comment',
                comment_type='role',
                comment_visibility='Internal',
            )
        mock_session.post.assert_called_once()
        url = mock_session.post.call_args[0][0]
        assert url == 'https://jira.example/rest/api/latest/issue/SAT-1/comment'
        payload = mock_session.post.call_args[1]['json']
        assert payload['body'] == 'Verification comment'
        assert payload['visibility'] == {'type': 'role', 'value': 'Internal'}
