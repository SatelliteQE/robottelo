from robottelo.common import records


class Domain(records.Record):
    name = records.StringField(format=r"domain\d\d\d\d")
