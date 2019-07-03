import setuptools

import konfi

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="konfi",
    version=konfi.__version__,
    author=konfi.__author__,
    author_email="team@giesela.dev",
    description="Python config management, but cute.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gieseladev/konfi",
    license="MIT",

    packages=setuptools.find_packages(exclude=("examples", "tests")),

    # entry_points={
    #     "console_scripts": [
    #         "konfi=konfi.cli:main",
    #     ]
    # },

    install_requires=["toml", "pyyaml"],

    extras_require={
        "docs": ["sphinx", "sphinx-autodoc-typehints"],
    },
)
