from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_desc = f.read()

setup(
    name="SheekWord",
    version="1.0.1",
    author="Rahul Bhai",
    description="Telegram WordSeek Auto Solver Userbot",
    long_description=long_desc,
    long_description_content_type="text/markdown",

    packages=find_packages(),

    include_package_data=True,

    install_requires=[
        "pyrogram>=1.4,<3.0",
        "tgcrypto>=1.2"
    ],

    python_requires=">=3.8",

    keywords=["telegram", "pyrogram", "wordseek", "solver", "userbot"],

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
