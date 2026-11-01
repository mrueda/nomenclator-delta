import hashlib
from nomenclator_delta.cli import build_dist


def test_dist_versions_assets_and_updates_html(tmp_path):
    site = tmp_path / "site"
    data = tmp_path / "data"
    site.mkdir()
    data.mkdir()
    (site / "index.html").write_text('<link href="styles.css"><script src="app.js"></script>')
    (site / "app.js").write_text("const version = 1;")
    (site / "styles.css").write_text("body { color: black; }")
    output = tmp_path / "dist"

    build_dist(site, data, output)
    first_html = (output / "index.html").read_text()
    for name in ("app.js", "styles.css"):
        asset = site / name
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:16]
        versioned = f"{asset.stem}.{digest}{asset.suffix}"
        assert f'"{versioned}"' in first_html
        assert (output / versioned).read_bytes() == asset.read_bytes()
        assert not (output / name).exists()

    build_dist(site, data, output)
    assert (output / "index.html").read_text() == first_html
    (site / "app.js").write_text("const version = 2;")
    build_dist(site, data, output)
    assert (output / "index.html").read_text() != first_html
