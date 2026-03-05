from setuptools import setup, find_packages

setup(
    name="SheekWord",
    version="1.0.0",
    author="Rahul Bhai",
    description="Telegram WordSeek Auto Solver Userbot",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyrogram",
        "tgcrypto"
    ],
    python_requires=">=3.8",
)
