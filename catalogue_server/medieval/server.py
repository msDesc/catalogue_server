from typing import Dict, List
import asyncio
import logging
import yaml
import pysolr

import uvloop
from sanic import Sanic, response, request, exceptions
from jinja2 import Environment, PackageLoader, select_autoescape
from catalogue_server.helpers.solr import facet_by_field_name, CatalogueRequest

app = Sanic("medieval")

config = yaml.safe_load(open('catalogue_server/medieval/configuration.yml', 'r'))

debug_mode: bool = config['common']['debug']
solr_server: str = config['solr']['server']

# Indent levels in the JSON response can make a big difference in download size, but at the expense of making
# the output readable. Set to indent only in Debug mode.
if debug_mode:  # pragma: no cover
    LOGLEVEL = logging.DEBUG
    JSON_INDENT: int = 4
else:
    LOGLEVEL = logging.WARNING
    JSON_INDENT: int = 0
    # In production mode, use uvloop for a faster event loop.
    asyncio.set_event_loop(uvloop.new_event_loop())

logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)",
                    level=LOGLEVEL)

log = logging.getLogger(__name__)

template_env = Environment(
    loader=PackageLoader('catalogue_server.medieval', 'templates'),
    autoescape=select_autoescape(['xml']),
    enable_async=True
)

index_template = template_env.get_template("index.html")
about_template = template_env.get_template("about.html")
contact_template = template_env.get_template("contact.html")
help_template = template_env.get_template("help.html")
terms_template = template_env.get_template("terms.html")
accessibility_template = template_env.get_template("accessibility.html")
advanced_template = template_env.get_template("advanced.html")
search_template = template_env.get_template("search.html")
record_template = template_env.get_template("record.html")
not_found_template = template_env.get_template("not-found.html")

app.static('/static/medieval', 'catalogue_server/medieval/static')
app.static('/static/shared', 'catalogue_server/static')


async def not_found_handler(req: request.Request, exc: exceptions.SanicException) -> response.HTTPResponse:
    rendered_template = await not_found_template.render_async()

    return response.html(rendered_template, status=404)

app.error_handler.add(exceptions.NotFound, not_found_handler)
solr_conn: pysolr.Solr = pysolr.Solr(solr_server)


@app.route("/")
async def root(req: request.Request) -> response.HTTPResponse:
    collections: Dict = facet_by_field_name("ms_collection_s", solr_conn)

    tmpl_vars = {
        "collections": collections
    }

    rendered_template = await index_template.render_async(**tmpl_vars)
    return response.html(rendered_template)


@app.route("/about")
async def about(req: request.Request) -> response.HTTPResponse:
    rendered_template = await about_template.render_async()
    return response.html(rendered_template)


@app.route("/help")
async def site_help(req: request.Request) -> response.HTTPResponse:
    rendered_template = await help_template.render_async()
    return response.html(rendered_template)


@app.route("/contact")
async def contact(req: request.Request) -> response.HTTPResponse:
    rendered_template = await contact_template.render_async()
    return response.html(rendered_template)


@app.route("/accessibility")
async def accessibility(req: request.Request) -> response.HTTPResponse:
    rendered_template = await accessibility_template.render_async()
    return response.html(rendered_template)


@app.route("/terms")
async def terms(req: request.Request) -> response.HTTPResponse:
    rendered_template = await terms_template.render_async()
    return response.html(rendered_template)


@app.route("/advanced")
async def advanced(req: request.Request) -> response.HTTPResponse:
    rendered_template = await advanced_template.render_async()
    return response.html(rendered_template)


@app.route("/search")
async def search(req: request.Request) -> response.HTTPResponse:
    c_req: CatalogueRequest = CatalogueRequest(solr_conn, config, req)
    resp: Dict = c_req.search()
    results: List = resp["results"]
    facets: Dict = resp["facets"]

    # Facets is Dict[facet_name: str, Dict[facet_value: str, facet_count: int]]
    # Transform the blacklight search string
    expanded_facets = {outer_k: {inner_k: (inner_v,f"[{outer_k}][]={inner_k}") for inner_k, inner_v in outer_v.items()} for outer_k, outer_v in facets.items()}
    pagination = resp["pagination"]
    result_type: str = req.args.get('f[type][]')

    tmpl_vars: Dict = {
        "facets": expanded_facets,
        "results": results,
        "result_type": result_type if result_type and len(result_type) > 0 else None,
        "facet_config": config['solr']['facet_fields'],
        "pagination": pagination,
        "current_url": req.url
    }

    rendered_template = await search_template.render_async(**tmpl_vars)

    return response.html(rendered_template)


@app.route("/catalog/<doc_id>")
async def catalog(req: request.Request, doc_id: str) -> response.HTTPResponse:
    catalogue: CatalogueRequest = CatalogueRequest(solr_conn, config, req)
    record: Dict = catalogue.get(doc_id)

    if not record:
        raise exceptions.NotFound("Resource not found")

    tmpl_vars = {
        "record": record
    }

    rendered_template = await record_template.render_async(**tmpl_vars)

    return response.html(rendered_template)
