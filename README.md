# json-forms-pdf
Convert jsonforms.io to PDF

Run with

```
pip install poetry
poetry run pytest
```


## Notes

The current setup uses python to generate a simple HTML form
from the ui-schema.

Then wkhtmltopdf with form support 
[available on docker hub](https://github.com/madnight/docker-alpine-wkhtmltopdf)
to convert the HTML to PDF.

```bash
docker run --rm -v $(pwd):/data madnight/docker-alpine-wkhtmltopdf /data/test.html /data/test.pdf
```