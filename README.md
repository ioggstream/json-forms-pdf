# json-forms-pdf
Convert jsonforms.io to PDF

Run with

```
pip install poetry
poetry run pytest
```

## How does it work?

This project aims at describing forms via jsonforms.io using [ui-schema](data/ui-notifica.yaml) and [schema](data/schema-notifica.yaml) so that forms data can be easily reused via API (eg. openapi).
General schemas (eg. person, location, ..) is provided via [definitions.yaml](data/definitions.yaml) based on the ongoing work on github.com/teamdigitale/openapi, so you don't have to redefine schemas.

NB: currently jsonforms doesn't support yaml and remote $ref's, but this project does the bundling and conversion for you.

To support legacy processes based on pdf files, this project provides:

- a static html serializer generating an HTML from the ui-schema
- an html to pdf converter based on the docker image of wkhtmltopdf

An example output is in [examples](examples)



## Notes

The current setup uses python to generate a simple HTML form
from the ui-schema.

Then wkhtmltopdf with form support 
[available on docker hub](https://github.com/madnight/docker-alpine-wkhtmltopdf)
to convert the HTML to PDF.

```bash
docker run --rm -v $(pwd):/data madnight/docker-alpine-wkhtmltopdf --enable-forms /data/test.html /data/test.pdf
```
