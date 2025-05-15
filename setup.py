from setuptools import setup, find_packages

VERSION = "0.1"
ENTRY_POINTS = """
[ckan.plugins]
search_export=ckanext.search_export.plugin:SearchExportPlugin
"""


setup(
    name="ckanext-search-export",
    version=VERSION,
    description="Export CKAN search results.",
    author="Tyler Kennedy",
    author_email="tk@tkte.ch",
    keywords="ckan",
    license="MIT",
    packages=find_packages(),
    entry_points=ENTRY_POINTS,
)