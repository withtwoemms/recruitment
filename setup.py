from os import environ as envvars
from pathlib import Path
from setuptools import find_packages
from setuptools import setup


setup(
    name='recruitment',
    description='a lib for sourcing actionpacked entities capable of getting the job done',
    long_description=Path(__file__).absolute().parent.joinpath('README.md').read_text(),
    long_description_content_type='text/markdown',
    setup_requires=[
        'setuptools_scm==5.0.1'
    ],
    use_scm_version={'local_scheme': 'no-local-version'} if envvars.get('LOCAL_VERSION_SCHEME') else True,
    packages=find_packages(exclude=['tests']),
    author='Emmanuel I. Obi',
    maintainer='Emmanuel I. Obi',
    maintainer_email='withtwoemms@gmail.com',
    url='https://github.com/withtwoemms/recruitment',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    install_requires=[
        'actionpack==1.7.13',
        'boto3==1.21.10',
    ],
)

