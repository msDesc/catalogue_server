import logging
import re
from typing import Dict, List, Optional, Tuple, Pattern
import math
import pysolr
from urllib.parse import urlparse, parse_qs, urlencode
import copy

log = logging.getLogger(__name__)

CLEAN_QSTRING_REGEX: Pattern = re.compile(r"[\[\]]+")


def facet_by_field_name(facet_field: str, solr_conn: pysolr.Solr) -> Dict:
    fq: List = ["type:manuscript"]
    rows: int = 0
    facet: Dict = {
        "facet.field": facet_field,
        "facet.sort": "index",
        "facet": "on"
    }

    docs = solr_conn.search("*:*", fq=fq, rows=rows, **facet)
    facet_values = docs.facets.get('facet_fields')
    collection_facets = facet_values.get(facet_field)

    i = iter(collection_facets)
    facet_dict: Dict = dict(zip(i, i))

    return facet_dict


class CatalogueRequest:
    """
    This class mimics the Blacklight search logic for handling URLs and provides several
    helper functions for parsing Blacklight-compatible query strings.
    """

    def __init__(self, conn: pysolr.Solr, config: Dict, req) -> None:
        self._conn: pysolr.Solr = conn
        self._request = req
        self._res: Optional[pysolr.Results] = None
        self._q: Optional[str] = None
        self._config: Dict = config

        facet_config = self._config["solr"]["facet_fields"]
        self._fields = self._config["solr"]["search_fields"]
        self._facet_fields = facet_config.keys()
        self._results_per_page = self._config["solr"]["results_per_page"]

        self._q_kwargs: Dict = {
            "defType": "edismax",
            "facet": "on",
            "facet.field": self._facet_fields,
            "facet.mincount": 1,
            "fl": self._fields,
            "rows": self._results_per_page
        }

        # set some default variables.
        self._facets: Dict = {}
        self._pnum: int = 1
        self._hits: int = 0

    def search(self) -> Dict:
        parsed_q, parsed_args = self._blacklight_compat(self._request.args)
        self._q = parsed_q
        self._q_kwargs.update(parsed_args)

        self._res = self._conn.search(self._q, **self._q_kwargs)
        self._hits = self._res.hits
        self._facets = self._res.facets.get("facet_fields")

        return {
            "results": self._res.docs,
            "facets": self._facet_response(),
            "pagination": self.pagination()
        }

    def hits(self) -> int:
        return self._hits

    def get(self, record_id: str) -> Optional[Dict]:
        """
        Returns a single record with a given record ID. Internally implemented as a
        Solr request, returning the first result from a given query.
        :param record_id:
        :return:
        """
        self._res = self._conn.search("*:*", fq=[f"pk:{record_id}"], rows=1)

        if self._res.hits != 1:
            return None

        return self._res.docs[0]

    def pagination(self) -> Dict:
        """
        Returns information about the number of results, the number
        of pages, and links to the pages for use in a pager.

        :return: A dictionary of pagination results
        """
        num_responses: int = self._hits
        start: int = self._res.raw_response['response']['start']
        # the number of pages can be found by rounding up responses / num results per page.
        # max(1, pages) is used to ensure that even with zero results we still return 1 page.
        num_pages: int = max(1, int(math.ceil(num_responses / self._results_per_page)))
        current_page: int = (start // self._results_per_page) + 1  # human-friendly pages are indexed from 1, not 0.
        next_page: Optional[int] = current_page + 1 if current_page < num_pages else None
        prev_page: Optional[int] = current_page - 1 if current_page > 1 else None

        req_args: Dict = self._request.args
        next_args: Dict = copy.deepcopy(req_args)
        prev_args: Dict = copy.deepcopy(req_args)
        next_args["page"] = str(next_page) if next_page else ""
        prev_args["page"] = str(prev_page) if prev_page else ""

        next_url: Optional[str] = f"{self._request.path}?{urlencode(next_args, doseq=True)}" if next_page else None
        prev_url: Optional[str] = f"{self._request.path}?{urlencode(prev_args, doseq=True)}" if prev_page else None

        return {
            "hits": num_responses,
            "pages": num_pages,
            "start": start + 1,  # because human-readable results are 1-indexed, not 0!
            "end": start + self._results_per_page,
            "current": current_page,
            "next_page_url": next_url,
            "prev_page_url": prev_url
        }

    def _facet_response(self) -> Dict:
        """
        Solr returns facets as a list of value, number; this turns them into a dict
        of {value: number}.

        :return: Dictionary of facet values
        """
        # If a search has not been done, return the facets immediately; this should be
        # an empty dictionary.
        if not self._res:
            return self._facets

        facets = self._facets

        for facet, values in facets.items():
            i = iter(values)
            v = dict(zip(i, i))
            facets[facet] = v

        return facets

    def _blacklight_compat(self, query_dict: Dict) -> Tuple[str, Dict]:
        """
            Parses an incoming Blacklight-formatted query and returns
            the appropriate Solr-formatted query.
        """
        qstring: str = "*:*"
        qargs: Dict = {}
        _filter_queries: List = []

        for k, v in query_dict.items():
            if k == 'q':
                qstring = query_dict[k[0]]
            elif k == 'sort':
                qargs.update({
                    "sort": v[0]
                })
            elif k == 'page':
                try:
                    self._pnum = int(v[0])
                except ValueError:
                    # ignore any incorrect page numbers, assuming that the page number is 1
                    continue

                start: int = 0
                if self._pnum > 1:
                    start = (self._pnum - 1) * self._results_per_page

                qargs.update({
                    "start": start
                })
            elif k == "per_page":
                qargs.update({
                    "rows": v[0]
                })
            elif k.startswith("f"):
                # Clean the filter query; remove the 'f' from the beginning before passing it along to be cleaned.
                for facet in ';'.join(v).split(';'):
                    use_key = k[1:]
                    use_value = [facet]
                    multi = facet.split('=')
                    if len(multi) != 1:
                        use_key = multi[0][1:]
                        use_value = [multi[1]]
                    cleaned_filters = self._format_qstring(use_key, use_value)
                    _filter_queries += cleaned_filters

        qargs.update({
            "fq": _filter_queries
        })

        if "sort" not in qargs:
            qargs.update({
                "sort": "score desc, sort_title asc"
            })

        return qstring, qargs

    def _format_qstring(self, qkey: str, qvalues: List) -> List:
        cleaned_field: str = re.sub(CLEAN_QSTRING_REGEX, "", qkey)
        ret: List = []

        for val in qvalues:
            ret.append(f"{cleaned_field}:\"{val}\"")

        return ret
