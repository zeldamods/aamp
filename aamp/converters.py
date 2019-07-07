# Utils for converting AAMP to a YAML representation and vice versa.
import aamp
import io
import typing
import yaml
import aamp.yaml_util as yu

def aamp_to_yml(input_data: bytes) -> bytes:
    dumper = yaml.CDumper
    yu.register_representers(dumper)
    reader = aamp.Reader(input_data, track_strings=True)
    root = reader.parse()
    dumper.__aamp_reader = reader
    return yaml.dump(root, Dumper=dumper, allow_unicode=True, encoding='utf-8', default_flow_style=None)

def yml_to_aamp(input_data: bytes) -> bytes:
    loader = yaml.CSafeLoader
    yu.register_constructors(loader)

    root = yaml.load(input_data, Loader=loader)
    buf = io.BytesIO()
    aamp.Writer(root).write(buf)
    buf.seek(0)
    return buf.getvalue()
