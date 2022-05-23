# Experimental Catalogue Server

This is an experimental replacement for the Blacklight setup used by the Bodleian Libraries for the following TEI catalogues:

 * https://medieval.bodleian.ox.ac.uk/
 * https://www.fihrist.org.uk/
 * https://karchak.bodleian.ox.ac.uk/
 * https://hebrew.bodleian.ox.ac.uk/
 * https://genizah.bodleian.ox.ac.uk/
 * https://armenian.bodleian.ox.ac.uk/
 * https://georgian.bodleian.ox.ac.uk/
 * https://senmai.bodleian.ox.ac.uk/

It was started by @ahankinson to address two main issues with the Blacklight application:

 1. Blacklight requires a database backend, even though the data it stores in the database isn't used in the above 
    implementations.
 2. The Rails application stack is relatively memory intensive and has a negative impact on the speed when multiple 
    catalogues are hosted on the same server.

This project addresses these problems by changing the application server to Sanic and removing the database component.
It also (currently) coalesces all the catalogue code into a single shared repo, meaning that they can also share some 
code. While this might make deploying a bit more difficult, it removes the maintenance cost of keeping nine separate projects
up-to-date.

## Installation

Sanic is a Python 3.7+ web server and web framework. Ensure the correct version of Python is used, either using a tool
like pyenv (e.g. `pyenv local 3.8.11`) or by modifying the `/usr/bin/python` symlink.

This project uses [Python Poetry](https://python-poetry.org) to manage dependencies. First run:

```shell
pip3 install poetry
poetry install
````

Now you will be able to run `gunicorn` to serve the individual services. For example, to run the Medieval catalogue on 
localhost port 9001, run:

```shell
poetry run gunicorn --reload  catalogue_server.medieval.server:app --worker-class sanic.worker.GunicornWorker -b localhost:9001
```

This is used for development -- the '--reload' flag will automatically reload the application when changes are detected.

Just like Blacklight, it provides a web interface to query Solr, but the Solr server needs to be set up independently. 
In production, that is likely to be on a dedicated server, but for development the following assumes it is on localhost. 
Included in this repository is a `solr` folder, containing the configuration files to create a core for the Medieval 
catalogue (which should be named `medieval-mss`), and a `sample_data` folder, containing Solr XML documents ready to be 
loaded into it. To do so, run:

```shell
cd sample_data
curl -fsS "http://localhost:8983/solr/medieval-mss/update?commit=true" --data-binary @manuscripts_index.xml -H "Content-Type: text/xml"
curl -fsS "http://localhost:8983/solr/medieval-mss/update?commit=true" --data-binary @works_index.xml -H "Content-Type: text/xml"
curl -fsS "http://localhost:8983/solr/medieval-mss/update?commit=true" --data-binary @persons_index.xml -H "Content-Type: text/xml"
curl -fsS "http://localhost:8983/solr/medieval-mss/update?commit=true" --data-binary @places_index.xml -H "Content-Type: text/xml"
```

## Structure and Operations

Each catalogue has a folder within the `catalogue_server` folder. It contains a `server.py` file where the URL
routes, and their responses, are specified. These are typically quite simple. Also a `configuration.yml` file which
controls some custom settings for each catalogue, including which Solr server and core to query, which fields to retrieve
for display in search results, and the facets to use to allow users to filter results. The `templates` subfolder contains
Jinja2 templates (which are equivalent to the ERB templates used in Blacklight.)

The `static` subfolder holds images, stylesheets and JavaScript files which are unique to the catalogue.
There is also a `static` folder on the same level as the catalogue folders. This is where files shared across all catalogues 
can be stored. Static files are served by the catalogue server, at `/static/[catalogue name]` for the custom resources
and `/static/shared` for the shared resources.

The heart of the application is the `helpers/solr.py` file. This is a shared module that all catalogues use to query
Solr, both for searching the indexes and for retrieving individual records. It also performs some mappings between Blacklight URLs
and this application, meaning that the URLs will stay the same if or when this application is used as a replacement for Blacklight.

## Status (May 2022)

There are a number of holes and design decisions that are still outstanding for this application. The biggest are:

 1. At present only the Medieval catalogue is implemented. There is a stub for Fihrist but the templates and server code 
    has not been brought over.
 2. It is unclear what parts of each catalogue can be shared, and what needs to be unique. At present there is no mechanism
    for shared templates, for example. This is because, while some catalogues share some templates, not all catalogues share
    templates. So maximally uncoupled templates were chosen, even though this will mean significant duplication. 
 3. There are still some rough edges in the Solr code. Not all query parameters are yet handled completely.
 4. These are large holes in the JavaScript functionality on the front end, particularly around sorting and pagination of results.
 5. A build process is needed to automate conversion of SCSS to CSS.
 6. All the "little things", like contact forms or the on-screen keyboard, do not work.
 7. There is no advanced search yet.
 
That said, there are some things that work really well:

 1. Querying and loading pages is much faster than Blacklight.
 2. The templates for displaying records are mostly identical to the existing site (although not the mobile view.)
 3. The templates are much easier to modify and more directly related to the output.
 4. The code for serving pages and adding new sections of the catalogues is more straightforward.
