"""Python setup.py for cos_registration_server package"""
import io
import os
from setuptools import find_packages, setup
from typing import Optional, List


def read(*paths: str, **kwargs: Optional[str]) -> str:
    """Read the contents of a text file safely.
    >>> read("cos_registration_server", "VERSION")
    '0.1.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path:str) -> List[str]:
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="cos_registration_server",
    version=read("cos_registration_server/cos_registration_server", "VERSION"),
    description="Awesome cos_registration_server created by ubuntu-robotics",
    url="https://github.com/canonical/cos-registration-server/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="ubuntu-robotics",
    packages=find_packages(exclude=[".github"]),
    include_package_data=True,
    install_requires=read_requirements("requirements.txt"),
    extras_require={"test": read_requirements("requirements-test.txt")},
)
