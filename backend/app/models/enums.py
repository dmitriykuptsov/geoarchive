from enum import Enum


class DocumentType(str, Enum):

    TECHNICAL_REPORT = "technical_report"
    EXPLORATION_REPORT = "exploration_report"
    RESOURCE_ESTIMATE = "resource_estimate"
    FEASIBILITY_STUDY = "feasibility_study"
    ENVIRONMENTAL_REPORT = "environmental_report"
    GEOLOGICAL_MAP = "geological_map"
    OTHER = "other"


class DocumentStatus(str, Enum):

    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ExtractionMethod(str, Enum):

    NATIVE_PDF = "native_pdf"
    OCR = "ocr"
    MANUAL = "manual"


class MapType(str, Enum):

    GEOLOGICAL = "geological"
    TOPOGRAPHIC = "topographic"
    SATELLITE = "satellite"
    GEOPHYSICAL = "geophysical"
    OTHER = "other"


class MapFileType(str, Enum):

    ORIGINAL = "original"
    GEOTIFF = "geotiff"
    TILE = "tile"
    PREVIEW = "preview"


class LayerType(str, Enum):

    CONTOURS = "contours"
    FAULTS = "faults"
    BOREHOLES = "boreholes"
    GEOLOGICAL_UNITS = "geological_units"
    MINERALIZATION = "mineralization"
    OTHER = "other"


class GeometryType(str, Enum):

    POINT = "Point"
    LINESTRING = "LineString"
    POLYGON = "Polygon"
