import functools

from bottle import abort, request

from librarian_content.library import metadata
from librarian_content.library.archive import Archive


def with_meta(abort_if_not_found=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(path, **kwargs):
            conf = request.app.config
            archive = Archive.setup(conf['library.backend'],
                                    request.app.supervisor.exts.fsal,
                                    request.db.content,
                                    contentdir=conf['library.contentdir'],
                                    meta_filenames=conf['library.metadata'])
            content = archive.get_single(path)
            if not content:
                if abort_if_not_found:
                    abort(404)
                return func(path=path, meta=None, **kwargs)

            meta = metadata.Meta(content)
            return func(path=path, meta=meta, **kwargs)
        return wrapper
    return decorator
