from robottelo.common import conf, records


class SmartProxy(records.Record):
    name = records.StringField()
    url = records.StringField(
        default=conf.properties['main.server.hostname'])
