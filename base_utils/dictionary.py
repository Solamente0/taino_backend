from typing import Any, List


def get_bool(param_value: str | bool) -> bool:
    """
    Ctainoert query parameter string to a boolean value.

    Args:
        param_value (str | bool): The query parameter value.

    Returns:
        bool: The boolean representation of the query parameter.
    """
    if type(param_value) == bool:
        return param_value

    return param_value.strip().lower() in ["true", "1", "t", "yes", "y"]


def get_argument_from_request(view, name, default=None):
    if name in view.request.query_params:
        return view.request.query_params.get(name, default)
    return view.kwargs.get(name, view.request.data.get(name, default))


def get_model_object(model, f: dict[str, Any] = None):
    if not f:
        return model.objects.all()
    return model.objects.filter(**f)


def bulk_replace_keys_in_dict(dic, old_keys, new_keys):
    print(f"{old_keys=}")
    print(f"{new_keys=}")
    for x in range(0, len(new_keys)):
        dic[new_keys[x]] = dic.pop(old_keys[x])
    return dic


def bulk_replace_keys(dictionary, key_mapping):
    """
    Replace keys in a dictionary based on a key mapping.

    :param dictionary: The original dictionary with keys to be replaced.
    :param key_mapping: A dictionary where keys are old keys and values are new keys.
    :return: A new dictionary with keys replaced.
    """
    return {key_mapping.get(k.strip(), k.strip()): v for k, v in dictionary.items()}


def json_extract(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


class BaseDictMapperConfig(object):
    MAPPING_ITEMS: dict = None

    def __init__(self, data: dict[str, Any] | List[dict[str, Any]], *args, **kwargs) -> None:
        self.data = data
        if isinstance(data, list):
            self.old_keys = list(data[0].keys())
        else:
            self.old_keys = list(data.keys())
        self.new_keys = list(self.MAPPING_ITEMS.values())

        super().__init__(*args, **kwargs)

    def map_data(self) -> dict[str, Any] | list[dict[str, Any]]:
        keys_to_replace = {"old_keys": self.old_keys, "new_keys": self.new_keys}

        if isinstance(self.data, list):
            # new_list = [bulk_replace_keys_in_dict(dic=d, **keys_to_replace) for d in self.data]
            # return [bulk_replace_keys_in_dict(dic=d, **keys_to_replace) for d in self.data]
            return [bulk_replace_keys(d, self.MAPPING_ITEMS) for d in self.data]

        # changed_data = bulk_replace_keys_in_dict(dic=self.data, **keys_to_replace)
        # return bulk_replace_keys_in_dict(dic=self.data, **keys_to_replace)
        return bulk_replace_keys(self.data, self.MAPPING_ITEMS)

    # def map_list_data(self) -> list[dict[str, Any]]:
    #     keys_to_replace = dict(old_keys=self.old_keys, new_keys=self.new_keys)
    #     # changed_data = bulk_replace_keys_in_dict(dic=self.data, old_keys=self.old_keys, new_keys=self.new_keys)
    #     new_list = [bulk_replace_keys_in_dict(dic=d, **keys_to_replace) for d in self.data]
    #     return new_list
