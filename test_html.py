import json
import shlex
from os import getcwd
from pathlib import Path
from subprocess import run
import pytest
import logging
from pdfforms import pdf_get_fields, bundle_file, HtmlRender, render_array

log = logging.getLogger()


def test_get_fields():
    ff = pdf_get_fields("simple.pdf")
    assert "#/properties/given_name" in ff


@pytest.fixture(
    scope="module",
    params=[
        # "group", "simple", "person",
     #   "residenza",
        "anagrafe"
        #"array"
    ],
)
def harn_form_render(request):
    label = request.param
    log.warning("Run test with, %r", label)
    for ftype in ("ui", "schema"):
        yaml_file = Path(f"data/{ftype}-{label}.yaml")
        if yaml_file.is_file():
            json_data = json.dumps(bundle_file(fpath=yaml_file), indent=2)
            Path(f"data/{ftype}-{label}.json").write_text(json_data)

    fr = HtmlRender.from_file(f"data/ui-{label}.json", f"data/schema-{label}.json")
    return fr, label


def test_group(harn_form_render):
    fr, label = harn_form_render
    layout = fr.ui
    fr.layout_to_form(layout)
    dpath = f"test-{label}.html"
    Path(dpath).write_bytes(fr.dump())
    convert_command = (
        f"docker run --rm -v {getcwd()}:/data "
        f"madnight/docker-alpine-wkhtmltopdf --enable-forms "
        f"/data/{dpath} /data/{dpath}.pdf"
    )

    log.warning(convert_command)
    run(shlex.split(convert_command))
    run(shlex.split(f"xdg-open {dpath}.pdf"))


def test_array():
    ui = bundle_file(fpath="data/ui-array.yaml")
    schema = bundle_file(fpath="data/schema-array.yaml")
    render = HtmlRender(ui, schema)
    name, schema = render.resolver.resolve("#/properties/basic/properties/fields")
    r = render_array(name, schema)
    raise NotImplementedError
