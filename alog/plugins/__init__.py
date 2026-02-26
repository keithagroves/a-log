# Copyright © 2012-2023 alog contributors
# License: https://www.gnu.org/licenses/gpl-3.0.html

from typing import Type

from alog.plugins.calendar_heatmap_exporter import CalendarHeatmapExporter
from alog.plugins.dates_exporter import DatesExporter
from alog.plugins.fancy_exporter import FancyExporter
from alog.plugins.alog_importer import ALOGImporter
from alog.plugins.json_exporter import JSONExporter
from alog.plugins.markdown_exporter import MarkdownExporter
from alog.plugins.tag_exporter import TagExporter
from alog.plugins.text_exporter import TextExporter
from alog.plugins.xml_exporter import XMLExporter
from alog.plugins.yaml_exporter import YAMLExporter

__exporters = [
    CalendarHeatmapExporter,
    DatesExporter,
    FancyExporter,
    JSONExporter,
    MarkdownExporter,
    TagExporter,
    TextExporter,
    XMLExporter,
    YAMLExporter,
]
__importers = [ALOGImporter]

__exporter_types = {name: plugin for plugin in __exporters for name in plugin.names}
__exporter_types["pretty"] = None
__exporter_types["short"] = None
__importer_types = {name: plugin for plugin in __importers for name in plugin.names}

EXPORT_FORMATS = sorted(__exporter_types.keys())
IMPORT_FORMATS = sorted(__importer_types.keys())


def get_exporter(format: str) -> Type[TextExporter] | None:
    for exporter in __exporters:
        if hasattr(exporter, "names") and format in exporter.names:
            return exporter
    return None


def get_importer(format: str) -> Type[ALOGImporter] | None:
    for importer in __importers:
        if hasattr(importer, "names") and format in importer.names:
            return importer
    return None
