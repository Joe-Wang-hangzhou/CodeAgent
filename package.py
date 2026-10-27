"""打包源码、项目文档和测试。"""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent


def main():
    destination = ROOT / "2403080546王超浩.zip"
    files = [p for p in ROOT.iterdir() if p.is_file() and (
        p.suffix == ".py" or p.name in {
            "README.md", "Design.md", "requirements.txt", ".env.example", ".gitignore"
        }
    )]
    files.append(ROOT / "examples" / "sample_code.py")
    files.extend((ROOT / "tests").glob("test_*.py"))
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, Path("Homework2") / path.relative_to(ROOT))
    print(f"已生成：{destination}\n大小：{destination.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
