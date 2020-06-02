# Experimental Catalogue Server

This project is an experimental replacement for the Blacklight setup 
for the TEI Catalogues. It was started to address two main issues with the
Blacklight application:

 1. Blacklight requires a database backend, even though the data it stores in the database is never used
 2. The Rails application stack is relatively memory intensive and has a negative impact on the speed of some of the catalogues.
 
This project addresses these problems by changing the application server to Sanic and removing the database component.
It also (currently) coalesces all the catalogue code into a single shared repo, meaning that they can also share some 
code. While this might make deploying a bit more difficult, it removes the maintenance cost of keeping nine separate projects
up-to-date.

## Installation

The project uses [Python Poetry](https://python-poetry.org) to manage dependencies. This must be installed first. 

Once installed, change to the project directory and run `poetry install`. This will install the project dependencies. 

After these dependencies are installed you will be able to run `gunicorn` to serve the individual services. For example, 
to run the Medieval catalogue on localhost port 9001, run:

    $> gunicorn --reload  catalogue_server.medieval.server:app --worker-class sanic.worker.GunicornWorker -b localhost:9001
    
(This is used for development -- the '--reload' flag will automatically reload the application when changes are detected.)

## Structure and Operations

Each catalogue has a folder within the 'catalogue_server' folder. In each of these lives a `server.py` file where the URL
routes, and their responses, are specified. These are typically quite simple. Also within the folder are a `templates` folder
and a `static` folder. These are, perhaps unsurprisingly, where the Jinja2 templates and static files for each catalogue live. 

There is also a `static` folder within the catalogue folder. This is where static files shared across all catalogues can
be stored. Static files are served by the catalogue server, at `/static/[catalogue name]` for the custom resources
and `/static/shared` for the shared resources.

There is also a `configuration.yml` file for each catalogue. This controls some custom settings for each catalogue, like
which fields can be used as facets. 

The heart of the application is the `helpers/solr.py` file. This is a shared module that all catalogues can use to query
Solr, both for searching and for retrieving individual records. It also performs some mappings between Blacklight URLs 
and this application, meaning that the URLs will stay the same if or when this application replaces Blacklight.

## Status (June 2020)

There are a number of holes and design decisions that are still outstanding for this application. The biggest are:

 1. At present only the Medieval catalogue is implemented. There is a stub for Fihrist but the templates and server code has not been brought over.
 2. It is unclear what parts of each catalogue can be shared, and what needs to be unique. At present there is no mechanism
 for shared templates, for example. This is because, while some catalogues share some templates, not all catalogues share
 templates. So maximally uncoupled templates were chosen, even though this will mean significant duplication. 
 3. There are still some rough edges in the Solr code. Not all query parameters are yet handled completely.
 4. These are large holes in the JavaScript functionality on the front end, particularly around sorting and pagination of results.
 5. All the "little things", like contact forms, do not work.
 6. There is no advanced search
 
 That said, there are some things that work really well:

 1. Querying and loading pages is much faster than Blacklight
 2. The templates for displaying records is almost identical to the existing site
 3. The templates are much easier to modify and more directly related to the output
 4. The code for serving pages and adding new sections of the catalogues is more straightforward