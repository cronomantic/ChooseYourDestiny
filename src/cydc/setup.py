from setuptools import setup

setup(
    name="realpython-reader",
    version="1.0.0",
    description="Read the latest Real Python tutorials",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/cronomantic/ChooseYourDestiny/tree/main/src/cydc",
    author="Cronomantic",
    author_email="cronomantic@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    packages=["cydc"],
    include_package_data=True,
    install_requires=["progressbar"],
    entry_points={"console_scripts": ["cydc=cydc.cydc:main"]},
)
