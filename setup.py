from setuptools import setup, find_packages

# Read the requirements.txt file
with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name='dcb-atfm',
    version='0.1.0',
    description='Basic logic for demand-capacity balancing in ATFM',
    author='Nhat-Hoang P. Nguyen',
    packages=find_packages(),
    # install_requires=install_requires,  # Use the list of dependencies from requirements.txt
    install_requires=[
        "intervaltree=3.1.0",
        "numpy=1.25.2",
        "pandas=2.0.3",
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
