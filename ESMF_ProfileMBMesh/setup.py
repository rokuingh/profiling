from setuptools import setup

setup(
    name='profile',
    version='0.1',
    py_modules=['profile'],
    install_requires=[
        'Click',
        'numpy',
        'pandas'
    ],
    entry_points='''
        [console_scripts]
        profile=profile:cli
    ''',
)