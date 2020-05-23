# simple_checkboxes.py
import json
import logging
import shlex
import xml.etree.ElementTree as ET
from os import chdir, getcwd
from os.path import basename, dirname
from pathlib import Path
from subprocess import run

import jsonref
import jsonschema
import PyPDF2
import pytest
import yaml
from markdown import markdown
from openapi_resolver import OpenapiResolver

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
        schema_resolve_external = OpenapiResolver(schema).resolve()
        self.schema = jsonref.loads(json.dumps(schema_resolve_external))
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

    def layout_to_form(self, layout, parent=None, attrib=None, level=1):
        parent = parent or self.form
        log.warning("layout: %r, parent: %r", layout["type"], parent)

        if layout["type"] == "Control":
            schema_url, schema = self.resolver.resolve(layout["scope"])
            label = layout.get("label")

            if schema["type"] != "array":
                child = self.element_to_form2(schema_url, schema, label, attrib)
                parent.append(child)
                return
            child = render_array(schema_url, schema, label)
            parent.append(child)
            return
            raise NotImplementedError(schema["type"])

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
            heading = ET.SubElement(child, f"h{level}")
            heading.text = layout["label"]
        else:
            ET.SubElement(child, "br")
        if "description" in layout:
            child.append(
                ET.fromstring(f"<div>" + markdown(layout["description"]) + "</div>")
            )

        for e in layout.get("elements", []):
            # import pdb; pdb.set_trace()
            log.warning(
                "adding %r.%r to %r.%r",
                e.get("type"),
                e.get("label"),
                child,
                child.attrib.get("label"),
            )
            self.layout_to_form(e, child, attrib=elements_attrib, level=level + 1)

    @staticmethod
    def element_to_form2(schema_url, schema, label, attrib=None):
        attrib = attrib or {}

        if "class" in attrib:
            attrib["class"] += " form-field"
        supported_types = {"string", "number", "integer", "boolean"}
        field_type = schema["type"]
        if field_type not in supported_types:
            raise NotImplementedError(field_type)

        field_label = label or schema.get("title") or labelize(schema_url)

        params = {
            "name": schema_url,
        }
        d = ET.Element("span", attrib=attrib)
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

        ET.SubElement(
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
    ff = pdf_get_fields("simple.pdf")
    assert "#/properties/given_name" in ff


def pdf_get_fields(fpath):
    return PyPDF2.PdfFileReader("simple.pdf").getFields()


def bundle_file(schema=None, fpath=None):
    if not (schema or fpath):
        raise ValueError("Pass at least one of schema and fpath")
    yaml_data = schema or yaml.safe_load(Path(fpath).read_text())
    if fpath:
        chdir(dirname(fpath))
    try:
        yaml_resolved = OpenapiResolver(yaml_data).resolve()
    finally:
        if fpath:
            chdir("..")
    return yaml_resolved


@pytest.fixture(
    scope="module",
    params=[
        # "group", "simple", "person",
        # "notifica",
        "array"
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
    ui_array(name, schema)


def ui_array(name, schema):
    assert "array" == schema.get("type")
    item_schema = schema["items"]
    vl = {"type": "VerticalLayout", "elements": []}
    for i in range(2):
        hl = {"type": "HorizontalLayout", "elements": []}
        vl["elements"].append(hl)
        if "properties" in item_schema:
            for k in item_schema["properties"]:
                hl["elements"].append(
                    {"type": "Control", "scope": f"{name}_{i}/properties/{k}"}
                )

        else:
            hl["elements"].append({"type": "Control", "scope": f"{name}_{i}"})

    return vl


def render_array(schema_url, schema, label):
    assert "array" == schema.get("type")
    item_schema = schema["items"]
    vl = ET.Element("div", attrib={"class": "VerticalLayout array"})
    for i in range(2):
        hl = ET.SubElement(vl, "div", attrib={"class": "HorizontalLayout array"})
        if "properties" in item_schema:
            for k, property_schema in item_schema["properties"].items():
                property_url = f"{schema_url}_{i}/properties/{k}"
                hl.append(
                    HtmlRender.element_to_form2(property_url, property_schema, label)
                )

        else:
            property_url = f"{schema_url}_{i}"
            hl.append(HtmlRender.element_to_form2(property_url, item_schema, label))

    return vl
