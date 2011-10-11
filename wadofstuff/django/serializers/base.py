"""New base serializer class to handle full serialization of model objects."""
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.serializers import base

def get_subclass(object):
    for related in object._meta.get_all_related_objects():
        if type(object) in related.model._meta.get_parent_list():
            if hasattr(object,related.var_name):
                return get_subclass(getattr(object, related.var_name))
    return object

class Serializer(base.Serializer):
    """Serializer for Django models inspired by Ruby on Rails serializer.

    """

    def __init__(self, *args, **kwargs):
        """Declare instance attributes."""
        self.options = None
        self.stream = None
        self.fields = None
        self.excludes = None
        self.relations = None
        self.extras = None
        self.use_natural_keys = None
        self.subclass = False
        super(Serializer, self).__init__(*args, **kwargs)

    def serialize(self, queryset, **options):
        """Serialize a queryset with the following options allowed:
            fields - list of fields to be serialized. If not provided then all
                fields are serialized.
            excludes - list of fields to be excluded. Overrides ``fields``.
            relations - list of related fields to be fully serialized.
            extras - list of attributes and methods to include.
                Methods cannot take arguments.
            subclass - binary variable set to true if you want to get the 
                subclass before serializing.
        """
        self.options = options
        self.stream = options.pop("stream", StringIO())
        self.fields = options.pop("fields", [])
        self.excludes = options.pop("excludes", [])
        self.relations = options.pop("relations", [])
        self.extras = options.pop("extras", [])
        self.use_natural_keys = options.pop("use_natural_keys", False)
        self.subclass = options.pop("subclass", False)

        self.start_serialization()
        for obj in queryset:
            if self.subclass is True:
                obj = get_subclass(obj)
            self.start_object(obj)
            for field in obj._meta.fields:
                attname = field.attname
                if field.serialize:
                    if field.rel is None:
                        if attname not in self.excludes:
                            if not self.fields or attname in self.fields:
                                self.handle_field(obj, field)
                    else:
                        if attname[:-3] not in self.excludes:
                            if not self.fields or attname[:-3] in self.fields:
                                self.handle_fk_field(obj, field)
            for field in obj._meta.many_to_many:
                if field.serialize:
                    if field.attname not in self.excludes:
                        if not self.fields or field.attname in self.fields:
                            self.handle_m2m_field(obj, field)
            for extra in self.extras:
                self.handle_extra_field(obj, extra)
            self.end_object(obj)
        self.end_serialization()
        return self.getvalue()

    def handle_extra_field(self, obj, extra):
        """Called to handle 'extras' field serialization."""
        raise NotImplementedError
