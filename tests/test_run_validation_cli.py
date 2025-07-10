import run_validation


def test_main_invokes_steps(monkeypatch, tmp_path):
    calls = {}

    def fake_compare(m1, m2, out):
        calls["compare"] = (m1, m2, out)
        out.write_text("[]")
        return []

    def fake_resolve(cmp_path, *, auto=None):
        calls["resolve"] = (cmp_path, auto)
        res_path = tmp_path / "res.json"
        res_path.write_text("[]")
        return res_path

    def fake_merge(m1, m2, res, out_dir):
        calls["merge"] = (m1, m2, res, out_dir)
        return out_dir / "master.json", out_dir / "meta.json"

    monkeypatch.setattr(run_validation.compare_masters, "compare", fake_compare)
    monkeypatch.setattr(run_validation.resolver, "resolve", fake_resolve)
    monkeypatch.setattr(run_validation.writer, "merge_masters", fake_merge)

    m1 = tmp_path / "v1.json"
    m2 = tmp_path / "v2.json"
    m1.write_text("[]")
    m2.write_text("[]")

    code = run_validation.main(
        [str(m1), str(m2), "--auto", "2", "--out_dir", str(tmp_path)]
    )
    assert code == 0
    assert "compare" in calls and "resolve" in calls and "merge" in calls
    assert calls["resolve"][1] == "2"
