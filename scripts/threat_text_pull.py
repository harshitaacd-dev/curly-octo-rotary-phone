"""Download openly licensed, human-annotated text datasets that label threats,
sexual / rape threats or gendered abuse, for text mining.

Files land in data/text_threats/raw/<dataset>/. Only the labelled files are
kept (e.g. EDOS's 2M unlabelled posts are skipped). Civil Comments (~420 MB of
parquet) is downloaded to data/text_threats/raw/civil_comments/ but is
git-ignored; build_threat_corpus.py keeps only the threat-relevant subset.

Datasets that need a request form (AMI, Let-Mi, MAMI, EXIST, ...) cannot be
pulled automatically; see data/text_threats/README.md.

Usage: python scripts/threat_text_pull.py [--skip-civil]
"""
import argparse
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "text_threats" / "raw"

# name -> (git url, [paths inside repo to keep])
GIT = {
    "edos": ("https://github.com/rewire-online/edos.git",
             ["data/edos_labelled_aggregated.csv",
              "data/edos_labelled_individual_annotations.csv", "LICENSE", "README.md"]),
    "comma": ("https://github.com/kmi-linguistics/comma.git",
              ["train_test_dev", "LICENSE", "README.md"]),
    "uli": ("https://github.com/tattle-made/Uli_Dataset.git",
            ["training", "testing", "LICENSE", "README.md"]),
    "dynahate": ("https://github.com/bvidgen/Dynamically-Generated-Hate-Speech-Dataset.git",
                 ["Dynamically Generated Hate Dataset v0.2.3.csv", "README.md"]),
    "hatecheck": ("https://github.com/paul-rottger/hatecheck-data.git",
                  ["test_suite_cases.csv", "test_suite_annotations.csv", "LICENSE", "README.md"]),
    "ethos": ("https://github.com/intelligence-csd-auth-gr/Ethos-Hate-Speech-Dataset.git",
              ["ethos/ethos_data/Ethos_Dataset_Multi_Label.csv",
               "ethos/ethos_data/Ethos_Dataset_Binary.csv", "LICENSE", "README.md"]),
    # Hindi / Hinglish (Romanised Hindi-English code-mixed)
    "trac1": ("https://github.com/kmi-linguistics/trac-1.git", ["hindi", "LICENSE", "README.md"]),
    # Official TRAC-2 train/dev files (CC BY-NC-SA 4.0), mirrored by a participant team
    "trac2": ("https://github.com/socialmediaie/TRAC2020.git", ["data/raw/hin"]),
}

# name -> {local filename: url}
HTTP = {
    "guest_misogyny": {
        "dataset.zip": "https://aclanthology.org/attachments/2021.eacl-main.114.Dataset.zip",
    },
    "cad": {
        "data.zip": "https://zenodo.org/api/records/4881008/files/data.zip/content",
        "README.txt": "https://zenodo.org/api/records/4881008/files/README.txt/content",
    },
    "measuring_hate_speech": {
        "measuring-hate-speech.parquet":
            "https://huggingface.co/datasets/ucberkeley-dlab/measuring-hate-speech/resolve/main/measuring-hate-speech.parquet",
    },
}

CIVIL = {f"{s}.parquet": f"https://huggingface.co/datasets/google/civil_comments/resolve/main/data/{s}.parquet"
         for s in ["train-00000-of-00002", "train-00001-of-00002",
                   "validation-00000-of-00001", "test-00000-of-00001"]}


def fetch(url, dest):
    if dest.exists():
        return
    print("  GET", url)
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def pull_git(name, url, keep):
    out = RAW / name
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "-q", "--depth", "1", url, tmp], check=True)
        for p in keep:
            src, dst = Path(tmp) / p, out / Path(p).name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                out.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-civil", action="store_true")
    args = ap.parse_args()

    for name, (url, keep) in GIT.items():
        print(name)
        pull_git(name, url, keep)

    for name, files in HTTP.items():
        print(name)
        out = RAW / name
        out.mkdir(parents=True, exist_ok=True)
        for fn, url in files.items():
            fetch(url, out / fn)
            if fn.endswith(".zip"):
                with zipfile.ZipFile(out / fn) as z:
                    z.extractall(out, [m for m in z.namelist() if not m.startswith("__MACOSX")])
                (out / fn).unlink()

    if not args.skip_civil:
        print("civil_comments")
        out = RAW / "civil_comments"
        out.mkdir(parents=True, exist_ok=True)
        for fn, url in CIVIL.items():
            fetch(url, out / fn)


if __name__ == "__main__":
    main()
