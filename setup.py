from setuptools import setup

setup(
    name="fcs_flim",
    version="1.0",
    author="Aurora Sirigu",
    description="",
    packages=["fcs_flim"],
    package_dir={"": "src"},
    rust_extensions=[("fcs_flim", "Cargo.toml")],
    zip_safe=False,
)