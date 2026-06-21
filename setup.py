from setuptools import setup, find_packages

setup(
    name="raf",
    version="1.0.0",
    description="Raf: Interactive Book Library for Pardus Smart Boards",
    author="Kaan Ferid Altundas",
    packages=find_packages(),
    package_data={
        "src": [
            "assets/locales/*.json",
            "assets/books.json",
            "assets/raf.png",
            "assets/raf.ico",
            "assets/raf.svg"
        ],
    },
    install_requires=[
        "PySide6>=6.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "raf=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
