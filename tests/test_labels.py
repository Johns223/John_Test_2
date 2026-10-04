from shipping import labels

ADDRESS = {
    "name": "jane smith",
    "line1": "14 Bridge Street",
    "city": "Manchester",
    "postcode": "M1 4AB",
    "country": "GB",
}


def test_name_is_titled():
    assert labels.normalise_name("jane smith") == "Jane Smith"


def test_a_short_field_is_padded_to_width():
    field = labels.render_field("Bristol", labels.CITY_WIDTH)
    assert len(field) == labels.CITY_WIDTH
    assert field.rstrip() == b"Bristol"


def test_a_long_field_is_trimmed():
    field = labels.render_field("x" * 80, labels.CITY_WIDTH)
    assert len(field) == labels.CITY_WIDTH


def test_a_label_is_the_sum_of_its_slots():
    payload = labels.build_label(ADDRESS)
    expected = (
        labels.NAME_WIDTH
        + labels.ADDRESS_WIDTH * 2
        + labels.CITY_WIDTH
        + labels.POSTCODE_WIDTH
    )
    assert len(payload) == expected


def test_uk_postcodes_validate():
    assert labels.valid_postcode("M1 4AB") is True
    assert labels.valid_postcode("SW1A 1AA") is True


def test_an_empty_postcode_is_rejected():
    assert labels.valid_postcode("") is False


def test_the_same_address_twice_is_a_duplicate():
    other = dict(ADDRESS, name="Jane Smith")
    assert labels.is_duplicate(ADDRESS, other) is True


def test_overflow_is_reported():
    long_name = dict(ADDRESS, name="x" * 60)
    assert "name" in labels.overflows(long_name)


def test_manifest_groups_by_country():
    rows = [
        dict(ADDRESS, name="Adams"),
        dict(ADDRESS, name="Baker"),
        dict(ADDRESS, name="Clark", country="IE"),
    ]
    grouped = labels.manifest(rows)
    assert sorted(grouped) == ["GB", "IE"]
    assert [a["name"] for a in grouped["GB"]] == ["Adams", "Baker"]
