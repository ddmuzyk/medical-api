def create_placeholder_data(data_dict, allowed_columns):
    filtered_data = {k: v for k, v in data_dict.items() if k in allowed_columns and v is not None}

    if not filtered_data:
        raise ValueError("No valid columns provided")

    columns = ','.join(filtered_data.keys())
    placeholders = ','.join(['%s'] * len(filtered_data))
    return columns, placeholders, tuple(filtered_data.values())

def get_set_clause_and_values(data_dict, allowed_columns):
    set_clauses = []
    values = []
    for key in allowed_columns:
        if key in data_dict:
            set_clauses.append(f"{key} = %s")
            values.append(data_dict[key])
    set_clause_str = ", ".join(set_clauses)
    return set_clause_str, values