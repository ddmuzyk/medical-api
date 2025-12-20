def create_placeholder_data(data_dict, allowed_columns):
    filtered_data = {k: v for k, v in data_dict.items() if k in allowed_columns}

    if not filtered_data:
        raise ValueError("No valid columns provided")

    columns = ','.join(filtered_data.keys())
    placeholders = ','.join(['%s'] * len(filtered_data))
    return columns, placeholders, tuple(filtered_data.values())