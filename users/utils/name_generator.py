def generate_unique_name(model_class, owner_filter, base_name):
    if not model_class.objects.filter(**owner_filter, name=base_name).exists():
        return base_name

    i = 1
    while True:
        name = f"{base_name} #{i}"
        if not model_class.objects.filter(**owner_filter, name=name).exists():
            return name
        i += 1
