from setuptools import setup, find_packages

setup(
    name='pug',
    version='1.0.0',
    author='Erfan Tarighi',
    author_email='erfantarighi@gmail.com',
    description='Fast Download manager',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'aiofiles',
        'tqdm',
        'yarl'
    ],
    entry_points={
        'console_scripts': [
            'pug=pug.main:main',
        ],
    },
)
