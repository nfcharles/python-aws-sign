from setuptools import setup

setup(
    name = 'aws_sign',
    version = '0.2.0',
    author = 'Navil Charles',
    author_email = 'navil.charles@gmail.com',
    description = 'AWS Signing Tools',
    url = 'git@github.com:nfcharles/python-aws-sign.git',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: API Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        ],
    test_suite = 'nose.collector',
    packages = [
        'aws_sign',
        'aws_sign.v4',
        'aws_sign.client'
        ],
    tests_require = [
        'mock',
        'nose'
        ],
    install_requires = [
        'tornado >= 4.0',
        'boto3'
        ])
