from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='smae',
    version='0.0.3',
    license="MIT",
    url="https://github.com/JacobFV/smae",
    description='Social Multi-Agent Environment',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Jacob Valdez',
    author_email='jacobfv@msn.com',
    packages=['smae'],  #same as name
    install_requires=[
        'numpy==1.19.0',
        'tensorflow==2.5.1',
        'gym==0.17.2',
        'pillow==8.2.0'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)