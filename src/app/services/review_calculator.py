def calculate_average(
    current_average: float,
    current_count: int,
    new_rating: int,
) -> tuple[float, int]:
    new_count = current_count + 1

    new_average = (
        current_average * current_count + new_rating
    ) / new_count

    return round(new_average, 2), new_count