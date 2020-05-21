# simple_checkboxes.py
import json
import logging
import shlex
import xml.etree.ElementTree as ET
from os import getcwd
from os.path import basename
from pathlib import Path
from subprocess import run
from markdown import markdown
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
        return b"<!DOCTYPE html>" + ET.tostring(self.root, method="html")

    @staticmethod
    def from_file(ui_path, schema_path):
        ui = yaml.safe_load(Path(ui_path).read_text())
        schema = yaml.safe_load(Path(schema_path).read_text())
        return HtmlRender(ui, schema)

    def layout_to_form(self, layout, parent=None, attrib=None):
        parent = parent or self.form
        log.warning("layout: %r, parent: %r", layout["type"], parent)

        if layout["type"] == "Control":
            child = self.element_to_form(layout, attrib)
            parent.append(child)
            return

        elements_attrib = {}
        if layout["type"] == "Group":
            pass
        elif layout["type"] == "VerticalLayout":
            pass
        elif layout["type"] == "HorizontalLayout":
            elements_attrib = {"class": "size-20"}
        else:
            raise NotImplementedError(layout["type"])

        child = ET.SubElement(
            parent,
            "div",
            attrib={"class": layout["type"], "label": layout.get("label", "")},
        )
        if "label" in layout:
            h1 = ET.SubElement(child, "h1")
            h1.text = layout["label"]
        else:
            ET.SubElement(child, "br")
        if "description" in layout:
            child.append(
                ET.fromstring(f"<div>" + markdown(layout["description"]) + "</div>")
            )

        for e in layout["elements"]:
            # import pdb; pdb.set_trace()
            log.warning(
                "adding %r.%r to %r.%r",
                e.get("type"),
                e.get("label"),
                child,
                child.attrib.get("label"),
            )
            self.layout_to_form(e, child, attrib=elements_attrib)

    def element_to_form(self, element, attrib=None):
        attrib = attrib or {}
        if "class" in attrib:
            attrib["class"] += " form-field"
        d = ET.Element("span", attrib=attrib)
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

        text = ET.SubElement(d, "text")
        text.text = field_label

        if schema.get("description"):
            params.update({"tooltip": schema.get("description")})
            text.text += f' ({schema.get("description")})'

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


@pytest.fixture(
    scope="module",
    params=[
        # "group", "simple", "person",
        "notifica"
    ],
)
def harn_form_render(request):
    label = request.param
    log.warning("Run test with, %r", label)
    yaml_file = Path(f"data/ui-{label}.yaml")
    if yaml_file.is_file():
        yaml_data = yaml.safe_load(yaml_file.read_text())
        json_data = json.dumps(yaml_data)
        Path(f"data/ui-{label}.json").write_text(json_data)
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
