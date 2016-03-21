from __future__ import unicode_literals

import os
import itertools
import logging

from bottle import request

from librarian_core.exts import ext_container as exts

from .facets import Facets
from ...tasks import generate_facets
from .archive import FacetsArchive, split_path
from .processors import (get_facet_processors,
                         split_name,
                         is_html_file,
                         HtmlFacetProcessor)


def get_facets(paths, partial=True, facet_type=None):
    supervisor = request.app.supervisor
    fsal = exts.fsal
    archive = FacetsArchive(fsal, exts.databases.facets,
                            config=supervisor.config)
    schedule_paths = []
    for path in paths:
        facets = archive.get_facets(path, facet_type=facet_type)
        if not facets:
            logging.debug("Facets not found for '{}'."
                          " Scheduling generation".format(path))
            schedule_paths.append(path)
            if partial:
                facets = generate_partial_facets(path, supervisor, fsal)
        yield facets
    if schedule_paths:
        schedule_facets_generation(supervisor.config, paths=schedule_paths,
                                   archive=archive)
    return


def find_html_index(paths):
    first_html_file = None
    best_html_file, best_html_index = (None, 10000)
    for path in paths:
        fname = os.path.basename(path)
        name, ext = split_name(fname)
        if is_html_file(ext):
            first_html_file = first_html_file or fname
            for i, index_name in enumerate(HtmlFacetProcessor.INDEX_NAMES):
                if name in index_name and i < best_html_index:
                    best_html_file = fname
                    best_html_index = i
    return best_html_file or first_html_file

def get_facet_types(paths):
    facet_types = ['generic']
    for path in paths:
        types = [p.name for p in get_facet_processors(path)]
        facet_types.extend(types)
    return list(set(facet_types))


def filter_by_facet_type(paths, facet_type):
    return itertools.ifilter(lambda path: is_facet_valid(path, facet_type),
                             paths)


def is_facet_valid(path, facet_type):
    processors = get_facet_processors(path)
    for p in processors:
        if p.name == facet_type:
            return True
    return False


def generate_partial_facets(path, supervisor, fsal):
    success, fso = fsal.get_fso(path)
    if not success:
        return None

    parent, name = split_path(path)
    facets = {'path': parent, 'file': name}
    for processor in get_facet_processors(path):
        processor.process_file(facets, path, partial=True)
    return Facets(supervisor, path, facets)


def schedule_facets_generation(config, *args, **kwargs):
    delay = config.get('facets.ondemand_delay', 0)
    exts.tasks.schedule(generate_facets,
                        args=args,
                        kwargs=kwargs,
                        delay=delay)


# TODO: Remove this after facets become stable
def log_facets(prefix, facets):
    import pprint
    import logging
    logging.debug('{} {}'.format(prefix, pprint.pformat(dict(facets))))
