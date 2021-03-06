import mock
import pytest

from librarian_core.contrib.databases.squery import Database

import librarian_content.library.backends.embedded.archive as mod


MOD = mod.__name__


@pytest.fixture
def archive():
    mocked_fsal = mock.Mock()
    mocked_db = mock.Mock()
    mocked_db.sqlin = Database.sqlin
    return mod.EmbeddedArchive(mocked_fsal,
                               mocked_db,
                               contentdir='contentdir',
                               meta_filenames=['metafile.ext'])


def mock_cursor(func):
    def _mock_cursor(archive, *args, **kwargs):
        mocked_cursor = mock.Mock()
        ctx_manager = mock.MagicMock()
        ctx_manager.__enter__.return_value = mocked_cursor
        archive.db.transaction.return_value = ctx_manager
        return func(mocked_cursor, archive, *args, **kwargs)
    return _mock_cursor


@mock_cursor
def test_remove_meta_from_db(cursor, archive):
    cursor.rowcount = 1
    path = 'relpath'
    sql = 'proper delete query'
    archive.db.Delete.return_value = sql

    assert archive.remove_meta_from_db(path) == 1

    delete_calls = [
        mock.call('content', where="path = ?"),
        mock.call('taggings', where="path = ?")
    ]
    archive.db.Delete.assert_has_calls(delete_calls)

    query_calls = [
        mock.call(sql, path),
        mock.call(sql, path)
    ]
    archive.db.query.assert_has_calls(query_calls)


@mock_cursor
@mock.patch.object(mod.EmbeddedArchive, '_serialize')
@mock.patch.object(mod.EmbeddedArchive, '_write')
def test_add_meta_to_db(cursor, archive, write, serialize):
    delete_sql = 'proper delete query'
    archive.db.Delete.return_value = delete_sql
    metadata = {
        "url": "http://en.wikipedia.org/wiki/Sweden",
        "title": "content title",
        "timestamp": "2014-08-10 20:35:17 UTC",
        "path": "13b320accaae7ae35b51e79fcebaea05",
        "replaces": "1fa7b8c2430bb75642d062f08f00a115",
        "content": {
            "html": {
                "index": "test.html",
                "keep_formatting": True
            }
        }
    }
    assert archive.add_meta_to_db(metadata) == 1
    archive.db.Delete.assert_called_once_with('content', where='path = ?')
    query_calls = [mock.call(delete_sql, "1fa7b8c2430bb75642d062f08f00a115")]
    archive.db.query.assert_has_calls(query_calls)
    serialize.assert_called_once_with(metadata, archive.transformations)
    write.assert_called_once_with('content',
                                  metadata,
                                  shared_data={'path': metadata['path']})


def test_needs_formatting(archive):
    # FIXME: This needs to be an integration test for full cov
    archive.db.result = {'keep_formatting': True}
    ret = archive.needs_formatting('foo')
    assert archive.db.query.called
    assert ret is False
    archive.db.result = {'keep_formatting': False}
    ret = archive.needs_formatting('foo')
    assert ret is True


def test__serialize(archive):
    metadata = {
        "url": "http://en.wikipedia.org/wiki/Sweden",
        "title": "content title",
        "timestamp": "2014-08-10 20:35:17 UTC",
        "path": "13b320accaae7ae35b51e79fcebaea05",
        "replaces": "1fa7b8c2430bb75642d062f08f00a115",
        "content": {
            "html": {
                "main": "test.html",
                "keep_formatting": True
            },
            "audio": {
                "description": "desc",
                "playlist": [{
                    "file": "audio.mp3",
                    "title": "my song",
                    "duration": 350
                }]
            }
        }
    }
    archive._serialize(metadata, archive.transformations)
    assert metadata == {
        "url": "http://en.wikipedia.org/wiki/Sweden",
        "title": "content title",
        "timestamp": "2014-08-10 20:35:17 UTC",
        "path": "13b320accaae7ae35b51e79fcebaea05",
        "html": {
            "main": "test.html",
            "keep_formatting": True
        },
        "audio": {
            "description": "desc",
            "playlist": [{
                "file": "audio.mp3",
                "title": "my song",
                "duration": 350
            }]
        }
    }


def test__write(archive):
    import collections
    OD = collections.OrderedDict
    metadata = OD({
        "url": "http://en.wikipedia.org/wiki/Sweden",
        "title": "content title",
        "timestamp": "2014-08-10 20:35:17 UTC",
        "path": "13b320accaae7ae35b51e79fcebaea05",
        "html": OD({
            "entry_point": "test.html",
            "keep_formatting": True
        }),
        "audio": OD({
            "description": "desc",
            "playlist": [OD({
                "file": "audio.mp3",
                "title": "my song",
                "duration": 350
            })]
        })
    })
    archive._write('content',
                   metadata,
                   shared_data={'path': '13b320accaae7ae35b51e79fcebaea05'})
    replace_calls = [
        mock.call('html', cols=['entry_point', 'keep_formatting', 'path']),
        mock.call('playlist', cols=['duration', 'path', 'file', 'title']),
        mock.call('audio', cols=['path', 'description']),
        mock.call('content', cols=['url', 'timestamp', 'path', 'title'])
    ]
    # this fails for no obvious reasons
    archive.db.Replace.assert_has_calls(replace_calls, any_order=True)
