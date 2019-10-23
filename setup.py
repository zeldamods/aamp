import fastentrypoints
import setuptools
import versioneer

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aamp",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="leoetlino",
    author_email="leo@leolam.fr",
    description="Nintendo parameter archive (AAMP) library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leoetlino/aamp",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries",
    ],
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        'PyYAML~=5.1',
        'dataclasses;python_version=="3.6"'
    ],
    entry_points = {
        'console_scripts': [
            'aamp = aamp.__main__:main',
            'aamp_to_yml = aamp.__main__:main',
            'yml_to_aamp = aamp.__main__:main'
        ]
    },
)
