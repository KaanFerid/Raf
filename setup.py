from setuptools import setup, find_packages

setup(
    name="kitapmarkt",
    version="1.0.0",
    description="Pardus Akıllı Tahta Kitap ve Uygulama Marketi",
    author="KitapMarkt Team",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "kitapmarkt=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
