
"""Validate dataset keys, relationships, and business rules."""

import pandas as pd

from data_loader import DatasetBundle


def validate_datasets(datasets: DatasetBundle) -> tuple[int, int]:
    """Validate the loaded datasets and return (passed, total)."""

    journey = datasets.customer_journey
    airport = datasets.airport
    schedule = datasets.flight_schedule
    cases = datasets.service_case

    passed = 0
    total = 0

    def check(title: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, total

        total += 1
        condition = bool(condition)

        if condition:
            passed += 1

        status = "PASS" if condition else "CHECK"
        print(f"[{status}] {title}")

        if detail:
            print(f"       {detail}")

    print("\n" + "=" * 70)
    print("DATA RELATIONSHIP AND BUSINESS-RULE VALIDATION")
    print("=" * 70)

    # 1. Primary-key uniqueness
    check("Journey IDs are unique", journey["journey_id"].is_unique)
    check("Airport codes are unique", airport["airport_code"].is_unique)
    check(
        "Flight instance IDs are unique",
        schedule["flight_instance_id"].is_unique,
    )
    check("Service case IDs are unique", cases["case_id"].is_unique)

    # 2. Airport references
    valid_airports = set(airport["airport_code"].dropna())

    invalid_origins = ~journey["origin_airport"].isin(valid_airports)
    invalid_destinations = ~journey["destination_airport"].isin(
        valid_airports
    )

    check(
        "All journey origin airports exist",
        not invalid_origins.any(),
        f"Invalid rows: {invalid_origins.sum():,}",
    )
    check(
        "All journey destination airports exist",
        not invalid_destinations.any(),
        f"Invalid rows: {invalid_destinations.sum():,}",
    )

    # 3. Route consistency
    expected_route = (
        journey["origin_airport"].astype("string")
        + "-"
        + journey["destination_airport"].astype("string")
    )

    route_mismatches = journey["route"].astype("string") != expected_route

    check(
        "Routes match origin and destination",
        not route_mismatches.any(),
        f"Mismatched rows: {route_mismatches.sum():,}",
    )

    # 4. Match journeys to scheduled flights.
    # Use date, flight number, route, origin, and destination.
    join_columns = [
        "flight_date",
        "flight_number",
        "route",
        "origin_airport",
        "destination_airport",
    ]

    journey_keys = journey[join_columns].copy()
    schedule_keys = schedule[join_columns].copy()

    # Normalise dates so Excel timestamps compare consistently.
    for frame in (journey_keys, schedule_keys):
        frame["flight_date"] = pd.to_datetime(
            frame["flight_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    duplicate_schedule_keys = schedule_keys.duplicated(
        subset=join_columns,
        keep=False,
    )

    check(
        "Schedule composite keys are unique",
        not duplicate_schedule_keys.any(),
        f"Rows involved in duplicate keys: "
        f"{duplicate_schedule_keys.sum():,}",
    )

    schedule_key_set = set(
        schedule_keys.drop_duplicates().itertuples(
            index=False, name=None
        )
    )

    journey_key_rows = list(
        journey_keys.itertuples(index=False, name=None)
    )

    matched = pd.Series([
        key in schedule_key_set for key in journey_key_rows
    ], index=journey.index)

    check(
        "Every journey matches a scheduled flight",
        matched.all(),
        f"Matched: {matched.sum():,}; "
        f"unmatched: {(~matched).sum():,}",
    )

    # 5. Service-case relationships
    valid_journey_ids = set(journey["journey_id"].dropna())
    orphan_cases = ~cases["journey_id"].isin(valid_journey_ids)

    check(
        "Every service case references a journey",
        not orphan_cases.any(),
        f"Unmatched cases: {orphan_cases.sum():,}",
    )

    multi_case_count = int(
        (cases["journey_id"].value_counts() > 1).sum()
    )
    print(
        "[INFO] Journeys with multiple service cases: "
        f"{multi_case_count:,}"
    )

    # 6. Binary flags must contain only 0 or 1.
    flag_columns = [
        "disruption_flag",
        "baggage_issue_flag",
        "check_in_issue_flag",
        "boarding_issue_flag",
        "complaint_flag",
    ]

    for column in flag_columns:
        invalid = ~journey[column].isin([0, 1])

        check(
            f"{column} contains only 0 and 1",
            not invalid.any(),
            f"Invalid values: {invalid.sum():,}",
        )

    # 7. Service and satisfaction scores must be between 1 and 5.
    score_columns = [
        "cabin_service_score",
        "airport_experience_score",
        "digital_experience_score",
        "baggage_experience_score",
        "staff_service_score",
        "overall_satisfaction_score",
    ]

    for column in score_columns:
        values = pd.to_numeric(journey[column], errors="coerce")
        valid = values.between(1, 5)

        check(
            f"{column} is within 1-5",
            valid.all(),
            f"Invalid or out-of-range values: {(~valid).sum():,}",
        )

    recommendation = pd.to_numeric(
        journey["recommendation_score"], errors="coerce"
    )
    recommendation_valid = recommendation.between(0, 10)

    check(
        "Recommendation scores are within 0-10",
        recommendation_valid.all(),
        f"Invalid or out-of-range values: "
        f"{(~recommendation_valid).sum():,}",
    )

    # 8. Review service-case resolution durations.
    # These checks assume closed cases have positive durations
    # and non-closed cases have no duration recorded.
    status = (
        cases["case_status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )
    is_closed = status.eq("closed").fillna(False)

    duration = pd.to_numeric(
        cases["case_resolution_days"], errors="coerce"
    )
    duration_missing = cases["case_resolution_days"].isna()

    closed_missing = is_closed & duration_missing
    closed_nonpositive = is_closed & duration.le(0).fillna(False)
    nonclosed_with_duration = (~is_closed) & (~duration_missing)
    negative_duration = duration.lt(0).fillna(False)

    check(
        "Closed cases have resolution durations",
        not closed_missing.any(),
        f"Missing durations: {closed_missing.sum():,}",
    )
    check(
        "Closed cases have positive durations",
        not closed_nonpositive.any(),
        f"Non-positive durations: {closed_nonpositive.sum():,}",
    )
    check(
        "Non-closed cases have no resolution duration",
        not nonclosed_with_duration.any(),
        f"Non-closed cases with durations: "
        f"{nonclosed_with_duration.sum():,}",
    )
    check(
        "Resolution durations are not negative",
        not negative_duration.any(),
        f"Negative durations: {negative_duration.sum():,}",
    )

    print("\n" + "=" * 70)
    print(f"VALIDATION SUMMARY: {passed}/{total} checks passed")

    if passed == total:
        print("All defined validation checks passed.")
    else:
        print(f"{total - passed} check(s) require investigation.")

    print("=" * 70)

    return passed, total
