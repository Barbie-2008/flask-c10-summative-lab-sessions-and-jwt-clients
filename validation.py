def workout_error(data, partial=False):
    fields = {'exercise', 'duration_minutes', 'calories_burned', 'date'}
    if not isinstance(data, dict):
        return 'A JSON object is required'
    if not data:
        return 'At least one workout field is required'

    extra = set(data) - fields
    missing = fields - data.keys() if not partial else set()
    if extra:
        return f'Unsupported field(s): {", ".join(sorted(extra))}'
    if missing:
        return f'Missing field(s): {", ".join(sorted(missing))}'

    for key in ('exercise', 'date'):
        if key in data and (
            not isinstance(data[key], str) or not data[key].strip()
        ):
            return f'{key} must be a non-empty string'
    for key in ('duration_minutes', 'calories_burned'):
        if key in data and (type(data[key]) is not int or data[key] < 0):
            return f'{key} must be a non-negative integer'
    return None
