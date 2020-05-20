# simple_checkboxes.py
import json
import logging
import shlex
import xml.etree.ElementTree as ET
from os import getcwd
from os.path import basename
from pathlib import Path
from subprocess import run

import jsonref
import jsonschema
import pytest
import yaml

log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

DATA = {
    "name": "foo",
    "description": "Confirm if you have passed the subject\nHereby ...",
    "done": True,
    "recurrence": "Daily",
    "rating": "3",
    "due_date": "2020-05-21",
    "recurrence_interval": 421,
}


def localize_date(date_string):
    try:
        from dateutil.parser import parse as dateparse
        import locale

        locale.nl_langinfo(locale.D_FMT)
        d = dateparse(date_string)
        return d.strftime(locale.nl_langinfo(locale.D_FMT))
    except:
        return date_string


class HtmlRender(object):
    def __init__(self, ui, schema, font_size=11, font_size_form=None, data=DATA):
        """

        :param ui: object containing ui-schema
        :param schema:  structure containing the schema

        """
        self.ui = ui
        # Use jsonref.loads to resolve $ref in schema. If we want to use external
        # references we need external resolver.
        self.schema = jsonref.loads(json.dumps(schema))
        self.resolver = jsonschema.RefResolver.from_schema(self.schema)
        self.font_size = font_size
        self.font_size_form = font_size_form or font_size
        self.data = data or {}
        self.line_feed = 5 * self.font_size
        self.root = ET.Element("html")
        head = ET.SubElement(self.root, "head")
        style = ET.SubElement(head, "link", {"href": "form.css", "rel": "stylesheet"})
        self.body = ET.SubElement(self.root, "body")
        self.form = ET.SubElement(
            self.body, "form", attrib={"action": "", "method": "post"}
        )

    def dump(self):
        return b"<!DOCTYPE html>" + ET.tostring(self.root)

    @staticmethod
    def from_file(ui_path, schema_path):
        ui = yaml.safe_load(Path(ui_path).read_text())
        schema = yaml.safe_load(Path(schema_path).read_text())
        return HtmlRender(ui, schema)

    def layout_to_form(self, layout, parent=None):
        parent = parent or self.form
        log.warning("layout: %r, parent: %r", layout["type"], parent)
        assert "elements" in layout
        # import pdb; pdb.set_trace()
        if layout["type"] == "Group":
            child = ET.SubElement(parent, "div", attrib={"class": layout["type"]})
            h1 = ET.SubElement(child, "h1")
            h1.text = layout["label"]
            for e in layout["elements"]:
                form_data = self.element_to_form(e)
                d = ET.SubElement(
                    child, "div", attrib={"style": "background-color: blue"}
                )
                if "elements" not in e:
                    d.append(form_data)
        elif layout["type"] == "HorizontalLayout":
            child = ET.SubElement(parent, "div", attrib={"class": layout["type"]})
            for e in layout["elements"]:
                form_data = self.element_to_form(e)
                d = ET.SubElement(child, "div", attrib={"class": "#side-10"})
                if "elements" not in e:
                    d.append(form_data)
        elif layout["type"] == "VerticalLayout":
            child = ET.SubElement(parent, "div", attrib={"class": layout["type"]})
            for e in layout["elements"]:
                d = ET.SubElement(child, "div")
                form_data = self.element_to_form(e)
                if "elements" not in e:
                    d.append(form_data)
        else:
            raise NotImplementedError(layout["type"])
        d = None
        return child

    def element_to_form(self, element):
        d = ET.Element("div")
        if "elements" in element:
            return self.layout_to_form(element, d)
        assert "type" in element
        assert "scope" in element

        supported_types = {
            "string",
            "number",
            "integer",
            "boolean",
        }

        schema_url, schema = self.resolver.resolve(element["scope"])
        field_type = schema["type"]
        if field_type not in supported_types:
            raise NotImplementedError(field_type)

        property_name = basename(schema_url)
        field_label = element.get("label") or labelize(schema_url)

        # render = self.render_function(property_name, schema, self.data)
        params = {
            "name": schema_url,
            "forceBorder": True,
        }
        if schema.get("description"):
            params.update({"tooltip": schema.get("description")})

        text = ET.SubElement(d, "text")
        text.text = field_label

        if field_type == "boolean":
            ET.SubElement(
                d,
                "input",
                attrib={"type": "checkbox", "name": schema_url, "id": schema_url},
            )
            return d

        if "enum" in schema:
            for v in schema["enum"]:
                ET.SubElement(
                    d,
                    "input",
                    attrib={
                        "type": "radio",
                        "name": schema_url,
                        "id": schema_url,
                        "value": v,
                    },
                )
                label = ET.SubElement(d, "label", attrib={"for": v})
                label.text = v
            return d

        input = ET.SubElement(
            d,
            "input",
            attrib={
                "name": schema_url,
                "id": schema_url,
                "value": schema.get("default", ""),
                "type": "text",
            },
        )
        return d


def labelize(s):
    return basename(s).replace("_", " ").capitalize()


def test_get_fields():
    import PyPDF2

    f = PyPDF2.PdfFileReader("simple.pdf")
    ff = f.getFields()
    assert "#/properties/given_name" in ff


@pytest.fixture(scope="module", params=["group", "simple", "person", "notifica"])
def harn_form_render(request):
    label = request.param
    log.warning("Run test with, %r", label)
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
    # run(shlex.split(f"xdg-open {dpath}.pdf"))
