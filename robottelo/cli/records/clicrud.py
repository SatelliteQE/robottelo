import re

from robottelo.common.records.fields import load_from_data, convert_to_data
from robottelo.cli.domain import Domain

def cli_data_transform(instance_cls, data, to_cli = False):

    def replace_id_suffix(key, to_cli):
        if to_cli:
            return key.replace("_","-")
        else:
            return key.replace("-","_")
        return key

    def replace_empty_none(val):
        return None if val == '""' else val

    return {replace_id_suffix(k, to_cli):replace_empty_none(v) for k,v in data.items()}

class CliCrud:

    def __init__(self):
        pass

    @classmethod
    def get_cli_object(cls):
        if hasattr(cls, 'cli_object'):
            return cls.cli_object
        raise NotImplementedError("Cli object needs to be defined")

    @classmethod
    def parse_create_stdout(cls, stdout):
        result = re.search("\[.*\]", stdout[0])
        if result:
            name = result.group(0)[1:-1]
            return {"name":name}
        return {}

    @classmethod
    def record_resolve(cls, instance):
        if cls != instance._meta.cli_class:
            return instance._meta.cli_class.record_resolve(instance)

        r = None
        if hasattr(instance,"id"):
            r = cls.cli_object.info({"id":instance.id})

        if r.return_code == 0:
            ninstance = load_from_data(instance.__class__, r.stdout, cli_data_transform)
            return ninstance
        else:
            raise Exception(r.return_code, r.stderr)

    @classmethod
    def record_exists(cls, instance):
        if cls != instance._meta.cli_class:
            return instance._meta.cli_class.record_exists(instance)

        r = cls.cli_object.exists(("name", instance.name))

        if r:
            return True
        else:
            return False

    @classmethod
    def record_remove(cls, instance):
        if cls != instance._meta.cli_class:
            return instance._meta.cli_class.record_remove(instance)

        r = cls.cli_object.delete({"name":instance.name})
        if r.return_code == 0:
            ninstance = load_from_data(instance.__class__, cls.parse_create_stdout(r.stdout), cli_data_transform)
            return ninstance
        else:
            raise Exception(r.return_code, r.stderr)

    @classmethod
    def record_create(cls, instance):
        if cls != instance._meta.cli_class:
            return instance._meta.cli_class.record_create(instance)

        data = convert_to_data(instance)
        if hasattr(cls,"create_fields"):
                       data = {name:field for name, field in data.items() if name in cls.create_fields}
        data = cli_data_transform(instance.__class__,data,True)


        r = cls.cli_object.create(data)
        if r.return_code == 0:
            ninstance = load_from_data(instance.__class__,cls.parse_create_stdout(r.stdout),cli_data_transform)
            return ninstance
        else:
            raise Exception(r.return_code, r.stderr)

    @classmethod
    def record_update(cls, instance):
        if cls != instance._meta.cli_class:
            return instance._meta.cli_class.record_update(instance)

        data = convert_to_data(instance)
        if hasattr(cls,"create_fields"):
                       data = {name:field for name, field in data.items() if name in cls.create_fields}
        data = cli_data_transform(instance.__class__,data,True)

        r = cls.cli_object.update(data)
        if r.return_code == 0:
            ninstance = load_from_data(instance.__class__,cls.parse_create_stdout(r.stdout), cli_data_transform)
            return ninstance
        else:
            raise Exception(r.return_code, r.stderr)



