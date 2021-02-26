import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nettlesome",
    version="0.1.2",
    author="Matt Carey",
    author_email="matt@authorityspoke.com",
    description="simplified semantic reasoning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mscarey/nettlesome",
    packages=setuptools.find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*"]
    ),
    install_requires=[
        "pint",
        "python-slugify",
        "sympy",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: Free To Use But Restricted",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    include_package_data=True,
)
