from django.contrib.admin import SimpleListFilter


class JSONFieldFilter(SimpleListFilter):
    """
    Base JSONFilter class to use by individual attribute filter classes.
    """

    model_json_field_name = None  # name of the json field column in the model
    json_data_property_name = None  # name of one attribute from json data

    def get_child_value_from_json_field_data(self, json_field_data):
        key_list = self.json_data_property_name.split('__')
        for key in key_list:
            if isinstance(json_field_data, dict):
                json_field_data = json_field_data[key]
        return json_field_data

    def lookups(self, request, model_admin):
        field_value_set = set()

        for json_field_data in model_admin.model.objects.values_list(self.model_json_field_name, flat=True):
            field_value_set.add(self.get_child_value_from_json_field_data(json_field_data))

        return [(v, v) for v in field_value_set]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value provided in
        the query string & retrievable via `self.value()`
        """
        if self.value():
            json_field_query = {f'{self.model_json_field_name}__{self.json_data_property_name}': self.value()}
            return queryset.filter(**json_field_query)
        else:
            return queryset


class LanguageTagFilter(JSONFieldFilter):
    model_json_field_name = 'data'  # Name of the column in the model
    json_data_property_name = 'language'  # property/field name in json data
    title = 'Language'  # A label for this filter for admin sidebar
    parameter_name = 'js_language'  # Parameter for the filter that will be used in the URL query
