# simple_checkboxes.py
import logging

from reportlab.pdfgen import canvas

# from reportlab.pdfbase import pdfform
import yaml
from pathlib import Path
import jsonschema

uischema = yaml.safe_load(Path("jsonforms-react-seed/src/uischema.json").read_text())
form_schema = yaml.safe_load(Path("jsonforms-react-seed/src/schema.json").read_text())
form_fields = jsonschema.RefResolver.from_schema(form_schema)

import pytest

from os.path import basename

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


def csetup(name, font_size=12):
    c = canvas.Canvas(f"{name}.pdf")
    c.setFont("Courier", font_size)
    return c


class FormRender(object):
    def __init__(self, ui, schema, font_size=11, font_size_form=None, data=DATA):
        """

        :param ui: object containing ui-schema
        :param schema:  structure containing the schema

        """
        self.ui = ui
        self.schema = schema
        self.resolver = jsonschema.RefResolver.from_schema(schema)
        self.font_size = font_size
        self.font_size_form = font_size_form or font_size
        self.data = data or {}
        self.line_feed = 5 * self.font_size

    @staticmethod
    def from_file(ui_path, schema_path):
        ui = yaml.safe_load(Path(ui_path).read_text())
        schema = yaml.safe_load(Path(schema_path).read_text())
        return FormRender(ui, schema)

    def layout_to_form(self, layout, form, canvas, point):
        assert "elements" in layout
        x, y = point
        if layout["type"] == "Group":
            canvas.setFont("Courier", int(self.font_size * 1.5))
            canvas.drawString(x, y, layout["label"])
            canvas.setFont("Courier", self.font_size)
            y -= 2 * self.line_feed
        if layout["type"] == "HorizontalLayout":
            y -= 10
            point = (x, y)
        for e in layout["elements"]:
            x, y = self.element_to_form(e, form, canvas, (x, y))
            if layout["type"] == "HorizontalLayout":
                x += 250
                y = point[1]
        if layout["type"] == "HorizontalLayout":
            return point[0], y - self.line_feed
        return x, y - self.line_feed

    def element_to_form(self, element, form, canvas, point):
        x, y = point
        if "elements" in element:
            return self.layout_to_form(element, form, canvas, (x, y))
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

        render = self.render_function(form, property_name, schema, self.data)
        y -= self.line_feed
        params = {
            "name": schema_url,
            "x": x + self.font_size * len(field_labeltest_pdf.py) // 1.4,
            "y": y,
            "forceBorder": True,
        }
        if schema.get("description"):
            params.update({"tooltip": schema.get("description")})

        canvas.drawString(x, y, field_label)
        render(**params)
        return x, y

    def render_function(self, form, name, schema, data=None):
        if schema["type"] in ("integer", "number"):

            def _render_number(**params):
                params.update(
                    {
                        "width": self.font_size_form * 5,
                        "height": self.font_size_form * 1.5,
                    }
                )
                value = data.get(name)
                if value:
                    params.update(
                        {"value": str(value), "borderStyle": "inset",}
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
                        size=self.font_size_form,
                        buttonStyle="check",
                        borderStyle="solid",
                        shape="square",
                        forceBorder=True,
                    )
                    form.canv.drawString(x + self.font_size_form * 2, y, v)
                    x += self.font_size * len(v)
                return params["x"], y

            return _render_enum_2

        if schema["type"] == "boolean":

            def _render_bool(**params):
                params.update(
                    {
                        "buttonStyle": "check",
                        "size": self.font_size_form,
                        "shape": "square",
                    }
                )
                if data.get(name):
                    params.update({"checked": "true"})
                return form.checkbox(**params)

            return _render_bool

        def _render_string(**params):
            value = data.get(name) or schema.get("default")
            params.update(
                {
                    "width": self.font_size_form * 10,
                    "height": self.font_size_form * 1.5,
                    "fontSize": self.font_size_form,
                    "borderStyle": "inset",
                }
            )
            if schema.get("format", "").startswith("date"):
                params.update(
                    {"width": self.font_size_form * 8,}
                )
            if value:
                if schema.get("format", "").startswith("date"):
                    value = localize_date(value)
                params.update({"value": value})
            return form.textfield(**params)

        return _render_string


def labelize(s):
    return basename(s).replace("_", " ").capitalize()


def test_get_fields():
    import PyPDF2

    f = PyPDF2.PdfFileReader("simple.pdf")
    ff = f.getFields()
    assert "#/properties/given_name" in ff


@pytest.fixture(scope="module", params=["group", "simple"])
def harn_form_render(request):
    label = request.param
    log.warning("Run test with, %r", label)
    fr = FormRender.from_file(f"data/ui-{label}.json", f"data/schema-{label}.json")
    canvas = csetup(label)
    return fr, canvas


def test_group(harn_form_render):
    point = (0, 800)
    fr, canvas = harn_form_render
    layout = fr.ui
    fr.layout_to_form(layout, canvas.acroForm, canvas, point)
    canvas.save()


def test_text():
    c = canvas.Canvas("form.pdf")
    c.setFont("Courier", 12)
    c.drawCentredString(300, 700, "Pets")
    c.setFont("Courier", 11)
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
        c.drawString(x + 11 * 2, y, v)
        x += 11 * len(v)

    c.save()
