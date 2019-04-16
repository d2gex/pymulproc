import setuptools
import pymulproc


def get_long_desc():
    with open("README.rst", "r") as fh:
        return fh.read()


setuptools.setup(
    name="pymulproc",
    version=pymulproc.__version__,
    author="Dan G",
    author_email="daniel.garcia@d2garcia.com",
    description="A tiny python library to handle multiprocessing communication",
    long_description=get_long_desc(),
    long_description_content_type="text/x-rst",
    url="https://github.com/d2gex/pymulproc",
    packages=['pymulproc'],
    python_requires='>=3.6',
    tests_require=['pytest>=4.4.0'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
