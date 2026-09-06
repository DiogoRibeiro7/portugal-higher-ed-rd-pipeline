from pathlib import Path

import pytest

from scripts.build_study_a_2025_cna_universe import EXPECTED_PAIR_COUNT, build_universe


def _index_html(pair_count: int) -> str:
    anchors = []
    for index in range(pair_count):
        institution = f"{index // 10000:04d}"[-4:]
        course = f"{index % 10000:04d}"[-4:]
        anchors.append(
            f'<p>{institution} Institution {institution}</p>'
            f'<a href="ec25_{institution}{course}.pdf">Course {course} [Licenciatura]</a>'
        )
    return "<html><body>" + "".join(anchors) + "</body></html>"


def test_build_universe_requires_frozen_pair_count(tmp_path: Path) -> None:
    path = tmp_path / "index.htm"
    path.write_text(_index_html(EXPECTED_PAIR_COUNT - 1), encoding="utf-8")

    with pytest.raises(ValueError, match="pair universe mismatch"):
        build_universe(path)


def test_build_universe_derives_unique_courses_from_pairs(tmp_path: Path) -> None:
    anchors = []
    for index in range(EXPECTED_PAIR_COUNT):
        institution = f"{index:04d}"[-4:]
        course = "9119" if index < 2 else f"{index:04d}"[-4:]
        anchors.append(
            f'<p>{institution} Institution {institution}</p>'
            f'<a href="ec25_{institution}{course}.pdf">Course {course} [Licenciatura]</a>'
        )
    path = tmp_path / "index.htm"
    path.write_text("<html><body>" + "".join(anchors) + "</body></html>", encoding="utf-8")

    pairs, courses = build_universe(path)

    assert len(pairs) == EXPECTED_PAIR_COUNT
    assert not pairs.duplicated(["institution_id", "course_id"]).any()
    assert courses["course_id"].is_unique
    assert (courses["course_id"] == "9119").sum() == 1
    assert pairs["index_source_sha256"].str.len().eq(64).all()
