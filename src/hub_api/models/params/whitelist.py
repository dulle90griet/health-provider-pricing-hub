from hub_api.exceptions import InvalidParameterError


def filter_by_whitelist(
    list_to_filter: list, whitelist: list, mode: str = "strict"
) -> list:
    """
    Check the provided list against the provided whitelist,
    returning a list containing only accepted values and raising
    errors for invalid values based on the specified error mode.

    Args:
        list_to_filter: The list of values to be checked for inclusion
            in the whitelist. May also be a single non-list value.
        whitelist: The list of all accepted values.
        error_mode: If None, no errors are raised. If "lax", an
            InvalidParameterError is raised only if all values in
            list_to_filter are invalid. In "strict" mode, an
            InvalidParameterError is raised if any value is invalid.
    """
    if not list_to_filter or not whitelist:
        return None
    if not isinstance(list_to_filter, list):
        list_to_filter = [list_to_filter]

    if mode == "strict":
        set_to_check = set(list_to_filter)
        whitelist_set = set(whitelist)
        if set_to_check <= whitelist_set:
            return list_to_filter
        else:
            raise InvalidParameterError(
                "Invalid value encountered. For any values to be accepted, only whitelisted values must be provided."
            )
    elif mode == "lax":
        valid_items = []
        for item in list_to_filter:
            if item in whitelist:
                valid_items.append(item)

        if not valid_items:
            raise InvalidParameterError(
                "Expected at least one whitelisted value, got none."
            )
        return valid_items
    else:
        raise ValueError("Invalid mode name.")
