from setuptools import setup, find_packages

setup(
    name="httplite",
    version="0.0.2",
    author="Jun Ke",
    author_email="kejun91@gmail.com",
    description="A lightweight http client based on urllib3",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/kejun91/httplite",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "urllib3",
        "certifi"
    ],
    python_requires='>=3.9',
)