# simple_checkboxes.py

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfform
from reportlab.lib.colors import magenta, pink, blue, green
import yaml
from pathlib import Path
import jsonschema

uischema = yaml.safe_load(Path("jsonforms-react-seed/src/uischema.json").read_text())
form_schema = yaml.safe_load(Path("jsonforms-react-seed/src/schema.json").read_text())
form_fields = jsonschema.RefResolver.from_schema(form_schema)

import pytest

from os.path import basename

FONT_SIZE = 10
LINE_FEED = 4 * FONT_SIZE
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


def csetup(name):
    c = canvas.Canvas(f"{name}.pdf")

    c.setFont("Courier", 20)
    c.drawCentredString(300, 800, "Pets")
    c.setFont("Courier", FONT_SIZE)
    return c


def test_layout_to_form():
    canvas = csetup("antani")
    layout_to_form(uischema, canvas.acroForm, canvas, (0, 800))
    canvas.save()


def layout_to_form(layout, form, canvas, point):
    assert "elements" in layout
    x, y = point
    if layout["type"] == "HorizontalLayout":
        y -= 10
        point = (x, y)
    for e in layout["elements"]:
        x, y = element_to_form(e, form, canvas, (x, y))
        if layout["type"] == "HorizontalLayout":
            x += 250
            y = point[1]
    if layout["type"] == "HorizontalLayout":
        return point[0], y - LINE_FEED
    return x, y - LINE_FEED


def render_string(form, name, schema, data=None):
    if schema["type"] in ("integer", "number"):

        def _render_number(**params):
            value = data.get(name)
            if value:
                params.update(
                    {
                        "value": str(value),
                        "width": FONT_SIZE * 5,
                        "height": FONT_SIZE,
                        "borderStyle": "inset",
                    }
                )
            return form.textfield(**params)

        return _render_number
    if "enum" in schema:

        def _render_enum(**params):
            options = [(x,) for x in schema["enum"]]
            params.update({"options": options, "value": schema["enum"][0]})
            return form.choice(**params)

        # return _render_enum

        def _render_enum_2(**params):
            x, y = params["x"], params["y"]
            for v in schema["enum"]:
                form.radio(
                    name=name,
                    tooltip="TODO",
                    value=v,
                    selected=False,
                    x=x,
                    y=y,
                    size=FONT_SIZE,
                    buttonStyle="check",
                    borderStyle="solid",
                    shape="square",
                    forceBorder=True,
                )
                form.canv.drawString(x + FONT_SIZE * 2, y, v)
                x += FONT_SIZE * len(v)
            return params["x"], y

        return _render_enum_2

    if schema["type"] == "boolean":

        def _render_bool(**params):
            params.update(
                {"buttonStyle": "check", "size": FONT_SIZE, "shape": "square"}
            )
            if data.get(name):
                params.update({"checked": "true"})
            return form.checkbox(**params)

        return _render_bool

    def _render_string(**params):
        value = data.get(name)
        params.update(
            {"width": FONT_SIZE * 5, "height": FONT_SIZE, "borderStyle": "inset"}
        )
        if value:
            if schema.get("format", "").startswith("date"):
                value = localize_date(value)
            params.update({"value": value})
        return form.textfield(**params)

    return _render_string


def element_to_form(element, form, canvas, point):
    x, y = point
    if "elements" in element:
        return layout_to_form(element, form, canvas, (x, y))
    assert "type" in element
    assert "scope" in element
    field_map = {
        "string": form.textfield,
        "number": form.textfield,
        "integer": form.textfield,
        "boolean": form.checkbox,
    }

    schema_url = element["scope"]
    schema_url, schema = form_fields.resolve(schema_url)
    field_type = schema["type"]
    property_name = basename(schema_url)
    if field_type not in field_map:
        raise NotImplementedError(field)
    render = render_string(form, property_name, schema, DATA)
    y -= LINE_FEED
    params = {
        "name": schema_url,
        "tooltip": "TODO",
        "x": x + FONT_SIZE * len(schema_url) // 1.4,
        "y": y,
        "forceBorder": True,
    }

    canvas.drawString(x, y, schema_url)
    render(**params)
    return x, y


def test_get_fields():
    import PyPDF2

    f = PyPDF2.PdfFileReader("form.pdf")
    ff = f.getFields()
    assert "#/properties/name" in ff


def test_text():
    c = canvas.Canvas("form.pdf")
    c.setFont("Courier", FONT_SIZE)
    c.drawCentredString(300, 700, "Pets")
    c.setFont("Courier", FONT_SIZE)
    form = c.acroForm

    x, y = 110, 645
    for v in "inizio cessazione talpazione donazione".split():
        form.radio(
            name="radio1",
            tooltip="Field radio1",
            value=v,
            selected=False,
            x=x,
            y=y,
            buttonStyle="check",
            borderStyle="solid",
            shape="square",
            forceBorder=True,
        )
        c.drawString(x + FONT_SIZE * 2, y, v)
        x += FONT_SIZE * len(v)

    y = 100
    # for e in uischema["elements"]:
    #     y = element_to_form(e, form, c, 100, y)

    c.save()
