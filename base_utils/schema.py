def generate_example(serializer_class):
    example_instance = serializer_class.Meta.model.objects.first()
    if example_instance:
        serializer = serializer_class(example_instance)
        return serializer.data
    return {}
