from setuptools import setup, find_packages

setup(
    name="etkilesimli-kitap-kutuphanesi",
    version="1.0.0",
    description="Interactive Book Library for Pardus Smart Boards",
    author="Kaan Ferid Altundas",
    packages=find_packages(),
    package_data={
        "src": [
            "assets/locales/*.json",
            "assets/books.json",
            "assets/etkilesimli-kitap-kutuphanesi.png",
            "assets/etkilesimli-kitap-kutuphanesi.ico",
            "assets/etkilesimli-kitap-kutuphanesi.svg"
        ],
    },
    install_requires=[
        "PySide6>=6.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "etkilesimli-kitap-kutuphanesi=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
